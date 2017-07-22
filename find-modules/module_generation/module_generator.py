#!/usr/bin/env python
#
# Copyright 2016 by Shaheed Haque (srhaque@theiet.org)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""Run SIP generator across a set of .h files, and create the SIP binding module."""
from __future__ import print_function
import argparse
import datetime
import errno
import gettext
import glob
import os
import inspect
import logging
import multiprocessing
from multiprocessing.pool import Pool
import re
import sys
import traceback

from clang import cindex

import rules_engine
from sip_generator import SipGenerator


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _


MODULE_SIP = "mod.sip"
INCLUDES_EXTRACT = "includes"
FILE_SORT_KEY = str.lower


def feature_for_sip_module(sip_file):
    """Convert a SIP module name into a feature name."""
    return os.path.splitext(sip_file)[0].replace(os.path.sep, "_").replace(".", "_").replace("+", "_")


class RuleUsage(dict):
    """
    When using multiprocessing, we need some way to gather the rule usage counts. This class provides the logic for
    accumulating the stats from remote as well as the local process.
    """
    def __init__(self):
        super(RuleUsage, self).__init__()

    def add_local_stats(self, rule_set):
        """
        Statistics from local usage where we have access to the rule database directly.

        :param rule_set:
        :return:
        """
        def accumulate_local(rule, usage_count):
            self.setdefault(str(rule), 0)
            self[rule] += usage_count

        rule_set.dump_unused(accumulate_local)

    def add_remote_stats(self, stats):
        """
        Statistics from remote processes where we do not have access to the
        rule database directly (not least because rule databases contain
        regular expression which cannot be pickled).
        """
        for rule, usage_count in stats.items():
            self.setdefault(rule, 0)
            self[rule] += usage_count


class IncludeToImportMap(dict):
    def __init__(self, project_root):
        """
        Initialise the dictionary with mappings based on the project root.

        :param root:                The root we started with.
        :param parent:              The current recursion point.
        """
        super(IncludeToImportMap, self).__init__()
        self.fill_from_includes(project_root, project_root)
        #
        # These are the SIP files that belong to the project.
        #
        self.predicted_sips = list(self.values())

    def __getitem__(self, item):
        return super(IncludeToImportMap, self).__getitem__(item.lower())

    def __setitem__(self, key, value):
        super(IncludeToImportMap, self).__setitem__(key.lower(), value)

    def fill_from_includes(self, root, parent):
        """
        Recursively fill the dictionary with mappings based on root.

        :param root:                The root we started with.
        :param parent:              The current recursion point.
        """
        names = ModuleGenerator.dedupe_legacy_names(sorted(os.listdir(parent)))
        for name in names:
            srcname = os.path.join(parent, name)
            if os.path.isdir(srcname):
                #
                # Any C++ definitions picked up by #include from this dirname
                # should match SIP definitions from this module.
                #
                module_dir = srcname[len(root) + len(os.path.sep):]
                sip = os.path.join(module_dir, name + MODULE_SIP)
                for funny in ModuleGenerator.FUNNY_CHARS:
                    sip = sip.replace(funny, "_")
                self[module_dir] = sip
                self.fill_from_includes(root, srcname)


class ModuleGenerator(object):
    def __init__(self, rules_pkg, output_dir, dump_modules=False, dump_items=False, dump_includes=False,
                 dump_privates=False):
        """
        Constructor.

        :param rules_pkg:           The rules for the project.
        :param output_dir:          The destination SIP directory.
        :param dump_modules:        Turn on tracing for modules.
        :param dump_items:          Turn on tracing for container members.
        :param dump_includes:       Turn on diagnostics for include files.
        :param dump_privates:       Turn on diagnostics for omitted private items.
        """
        super(ModuleGenerator, self).__init__()
        #
        # Find and load the libclang.
        #
        lib_clang, exe_clang, sys_includes, exe_sip = get_platform_dependencies()
        cindex.Config.set_library_file(lib_clang)
        self.exe_clang = exe_clang
        #
        # Get paths.
        #
        self.rules_pkg = rules_pkg
        self.compiled_rules = rules_engine.rules(self.rules_pkg)
        self.project_root = self.compiled_rules.cxx_source_root()
        self.package = self.compiled_rules.sip_package()
        self.includes = self.dedupe_legacy_names(self.compiled_rules.cxx_includes())
        self.compile_flags = self.compiled_rules.cxx_compile_flags() + ["-isystem" + i for i in sys_includes]
        exploded_includes = list(self.includes)
        for i in self.includes:
            for dirpath, dirnames, filenames in os.walk(i):
                for d in dirnames:
                    d = os.path.join(dirpath, d)
                    if d not in exploded_includes:
                        exploded_includes.append(d)
        self.compile_flags += ["-I" + i for i in exploded_includes]
        self.imports = self.compiled_rules.sip_imports()
        self.output_dir = output_dir
        self.dump_modules = dump_modules
        self.dump_items = dump_items
        self.dump_includes = dump_includes
        self.dump_privates = dump_privates
        #
        # One of the problems we want to solve is that for each #include in the transitive fanout for a .h under
        # self.project_root, we need to insert a %Import for the corresponding module-level .sip. To do this, we assume
        # that for the relative path aaa/bbb/ccc/foo/bar.h, the needed module is at aaa/bbb/ccc/foo/foomod.sip.
        #
        # However, this is made tricky because we want to use new-style CamelCase names whereever possible:
        #
        #   - Under self.imports, we simply walk the directory structure, folding into any non-lower-case-only names
        #     when possible, and add each xxxmod.sip we find to the available set.
        #
        #   - Under self.output_dir, of course, the .sip files don't actually exist before we start running. So here,
        #     we walk self.project_root, folding into any non-lower-case-only names when possible, and add the
        #     xxxxmod.sip name that will be created to the available set.
        #
        self.include_to_import_cache = IncludeToImportMap(self.project_root)
        for sip_root in self.imports:
            self.include_to_import_cache.fill_from_includes(sip_root, sip_root)
        self.all_features = None
        self.rule_usage = RuleUsage()
        self.omitter = None
        self.selector = None

    @staticmethod
    def dedupe_legacy_names(names):
        new_style_names = [n for n in names if n != n.lower() and n.lower() in names]
        for name in new_style_names:
            #
            # _("Ignoring legacy name for {}").format(os.path.join(root, name)))
            #
            names.remove(name.lower())
        return names

    def process_tree(self, jobs, selector, omitter):
        """
        Run a set of SIP modules, but don't throw any errors.
        
        :param jobs:                How many jobs to run in parallel? 0 for serial inline (debug) mode.
        :param selector:            A regular expression which limits the files from project_root to be processed.
        :param omitter:             A regular expression which sets the files from project_root NOT to be processed.
        :return: (attempts, [failures])
        """
        self.omitter = omitter
        self.selector = selector
        self.all_features = set()
        attempts = 0
        failures = []
        directories = 0
        sources = self.compiled_rules.cxx_sources()
        if sources:
            sources = [s[len(self.project_root):] for s in sources]
            sources = self.dedupe_legacy_names(sources)
            sources = [self.project_root + s for s in sources]
            #
            # If any of the deduped entries points to a legacy path, fix it.
            #
            for i, source in enumerate(sources):
                dir, base = os.path.split(source)
                candidates = self.dedupe_legacy_names(os.listdir(dir))
                candidates = [c for c in candidates if c.lower() == base.lower()]
                sources[i] = os.path.join(dir, candidates[0])
            sources.sort(key=FILE_SORT_KEY)
        else:
            sources = [self.project_root]
        for source in sources:
            if os.path.isdir(source):
                for dirpath, dirnames, filenames in os.walk(source):
                    #
                    # Eliminate the duplication of forwarding headers.
                    #
                    forwarding_headers = [h for h in filenames if not h.endswith(".h") and h.lower() + ".h" in filenames]
                    for h in forwarding_headers:
                        #
                        # _("Ignoring legacy header for {}").format(os.path.join(dirpath, h)))
                        #
                        filenames.remove(h.lower() + ".h")
                    #
                    # Eliminate the duplication of forwarding directories.
                    #
                    dirnames = self.dedupe_legacy_names(dirnames)
                    #
                    # Use sorted walks.
                    #
                    dirnames.sort(key=FILE_SORT_KEY)
                    filenames.sort(key=FILE_SORT_KEY)
                    a, f = self.process_dir(jobs, dirpath, filenames)
                    attempts += a
                    failures += f
                    if a:
                        directories += 1
            else:
                #
                # Assume it is a single-directory glob.
                #
                dirpath = os.path.dirname(source)
                filenames = [os.path.basename(f) for f in glob.iglob(source) if os.path.isfile(f)]
                a, f = self.process_dir(jobs, dirpath, filenames)
                attempts += a
                failures += f
                if a:
                    directories += 1
        feature_list = os.path.join(self.output_dir, "modules.features")
        #
        # TODO, make sure the entries are unique.
        #
        with open(feature_list, "w") as f:
            for feature in sorted(self.all_features, key=FILE_SORT_KEY):
                f.write("%Feature(name={})\n".format(feature))
        self.rule_usage.add_local_stats(self.compiled_rules)
        return attempts, failures, directories

    FUNNY_CHARS = "+"

    def process_dir(self, jobs, dirname, filenames):
        """
        Walk over a directory tree and for each file or directory, apply a function.
        """
        attempts = 0
        failures = []
        per_process_args = []
        for n in filenames:
            source = os.path.join(dirname, n)
            h_file = source[len(self.project_root) + len(os.path.sep):]
            #
            # Was this file selected?
            #
            if self.compiled_rules.cxx_selector.search(h_file) and not self.compiled_rules.cxx_omitter.search(h_file):
                if self.selector.search(h_file) and not self.omitter.search(h_file):
                    per_process_args.append((source, h_file))
        if not per_process_args:
            return attempts, failures
        std_args = (self.project_root, self.rules_pkg, self.package, self.compile_flags, self.includes, self.output_dir,
                    self.dump_modules, self.dump_items, self.dump_includes, self.dump_privates)
        if jobs == 0:
            #
            # Debug mode.
            #
            results = [process_one(*(process_args + std_args)) for process_args in per_process_args]
        else:
            #
            # Parallel processing here...
            #
            tp = Pool()
            results = [tp.apply_async(process_one, process_args + std_args) for process_args in per_process_args]
            tp.close()
            tp.join()
            #
            # Serial again. Order the results by the name of the source.
            #
            results = [r.get() for r in results]
        results = {result[0]: result[1:] for result in results}
        import_sips = set()
        modulecode = {}
        all_include_roots = set()
        sip_files = []
        for source in sorted(results.keys(), key=FILE_SORT_KEY):
            sip_file, tmp, direct_includes, i_paths, rule_usage, e = tuple(results[source])
            #
            # Update the global collections.
            #
            attempts += 1
            if e:
                failures.append((source, e))
            self.rule_usage.add_remote_stats(rule_usage)
            if sip_file:
                modulecode.update(tmp)
                sip_files.append(sip_file)
                #
                # Create something which the SIP compiler can process that includes what appears to be the
                # immediate fanout from this module.
                #
                all_include_roots.update(i_paths)
                #
                # For each include, add the corresponding SIP module to the set to be %Import'd.
                #
                for include in direct_includes:
                    if self.compiled_rules.cxx_omitter.search(include) or self.omitter.search(include):
                        continue
                    if include.endswith(("_export.h", "_version.h")):
                        continue
                    sip = self._map_include_to_import(include)
                    if sip:
                        import_sips.add(sip)
                    else:
                        logger.warn(_("Cannot find SIP for {}").format(include))
        #
        # Create a SIP module including all the SIP files in this directory.
        #
        # NOTE: this is really only best-effort; the output here might have to be edited, or indeed
        # module files may need to be created from scratch if the logic here is not good enough.
        #
        if sip_files:
            h_dir = dirname[len(self.project_root) + len(os.path.sep):]
            if h_dir:
                #
                # Remove funny characters: the results must be Python-valid names.
                #
                for funny in ModuleGenerator.FUNNY_CHARS:
                    h_dir = h_dir.replace(funny, "_")
                module = h_dir.replace(os.path.sep, ".")
                output_file = os.path.join(h_dir, os.path.basename(h_dir) + MODULE_SIP)
            else:
                #
                # Header files at the top level...
                #
                module = self.package
                output_file = os.path.join(h_dir, self.package + MODULE_SIP)
            #
            # Write the header and the body.
            #
            full_output = os.path.join(self.output_dir, output_file)
            try:
                os.makedirs(os.path.dirname(full_output))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            if h_dir:
                decl = "%Module(name={}.{})\n".format(self.package, module)
            else:
                decl = "%Module(name={})\n".format(module)
            decl += """
%ModuleHeaderCode
#pragma GCC visibility push(default)
%End
"""
            feature = feature_for_sip_module(output_file)
            self.all_features.add(feature)
            #
            # Create something which the SIP compiler can process that includes what appears to be the
            # immediate fanout from this module.
            #
            for sip_import in sorted(import_sips, key=FILE_SORT_KEY):
                #
                # Protect each %Import with a feature. The point of this is that we often see module A and B
                # which need to %Import each other; this confuses the SIP compiler which does not like the
                # %Import A encountered in B while processing A's %Import of B. However, we cannot simply
                # declare the corresponding %Feature here because then we will end up with the same %Feature in
                # both A and B which SIP also does not like.
                #
                if sip_import in self.include_to_import_cache.predicted_sips:
                    if sip_import != output_file:
                        feature = feature_for_sip_module(sip_import)
                        self.all_features.add(feature)
                        decl += "%If ({})\n".format(feature)
                        decl += "%Import(name={})\n".format(sip_import)
                        decl += "%End\n"
                else:
                    decl += "%Import(name={})\n".format(sip_import)
            #
            # Add all include paths actually used by the compiler.
            #
            decl += "%Extract(id={})\n".format(INCLUDES_EXTRACT)
            for include in sorted(all_include_roots, key=FILE_SORT_KEY):
                decl += "{}\n".format(include)
            decl += "%End\n"
            #
            # Add all peer .sip files.
            #
            peers = ""
            for sip_file in sip_files:
                peers += "%Include(name={})\n".format(sip_file)
            #
            # Any module-related manual code (%ExportedHeaderCode, %ModuleCode, %ModuleHeaderCode or other
            # module-level directives?
            #
            sip = {
                "name": module,
                "decl": decl,
                "modulecode": modulecode,
                "peers": peers,
            }
            body = ""
            if self.dump_modules:
                logger.info(_("Processing module for {}").format(os.path.basename(full_output)))
            modifying_rule = self.compiled_rules.modulecode(os.path.basename(full_output), sip)
            if modifying_rule:
                body += "// Modified {} (by {}):\n".format(os.path.basename(full_output), modifying_rule)
            logger.info(_("Creating {}").format(full_output))
            with open(full_output, "w") as f:
                f.write(header(output_file, h_dir, self.package))
                f.write(body)
                f.write(sip["decl"])
                #
                # The modulecode dictionary ensures there can be no duplicates, even if multiple sip files might have
                # contributed the same item. By emitting it here, it can provide declare-before-use (needed for
                # %Exceptions).
                #
                # Also, since SIP cannot cope with the same %MappedType in different modules, the rules can be
                # used to eliminate the duplicates.
                #
                f.write("\n")
                for mc in sorted(sip["modulecode"]):
                    f.write(modulecode[mc])
                f.write("\n")
                f.write(sip["peers"])
                f.write(sip["code"])
        return attempts, failures

    def _map_include_to_import(self, include):
        """
        For a given include file, return the corresponding SIP module.

        :param include:                 The name of a header file.
        :return: The name of a SIP module which represents the header file.
        """
        for include_root in self.includes:
            #
            # Assume only EXACTLY one root matches.
            #
            if include.startswith(include_root):
                tmp = include[len(include_root) + len(os.path.sep):]
                try:
                    return self.include_to_import_cache[os.path.dirname(tmp)]
                except KeyError:
                    break
        return None


def process_one(h_file, h_suffix, h_root, rules_pkg, package, compile_flags, i_paths, output_dir, dump_modules,
                dump_items, dump_includes, dump_privates):
    """
    Walk over a directory tree and for each file or directory, apply a function.

    :param h_file:              Source to be processed.
    :param h_suffix:            Source to be processed, right hand side of name.
    :param h_root:              Config
    :param rules_pkg:           Config
    :param package:             Config
    :param compile_flags:       Config
    :param i_paths:             Config
    :param output_dir:          Config
    :param dump_modules:        Turn on tracing for modules.
    :param dump_items:          Turn on tracing for container members.
    :param dump_includes:       Turn on diagnostics for include files.
    :param dump_privates:       Turn on diagnostics for omitted private items.
    :return:                    (
                                    source,
                                    sip_suffix,
                                    dict(modulecode),
                                    [direct includes from h_file],
                                    [-I paths needed by h_file],
                                    dict(rule_usage),
                                    error,
                                )
    """
    sip_suffix = None
    all_includes = lambda: []
    direct_includes = []
    result, modulecode, rule_usage = "", {}, {},
    #
    # Make sure any errors mention the file that was being processed.
    #
    try:
        generator = SipGenerator(rules_pkg, compile_flags, dump_modules=dump_modules, dump_items=dump_items,
                                 dump_includes=dump_includes, dump_privates=dump_privates)
        if h_suffix.endswith("_export.h"):
            pass
        elif h_suffix.endswith("_version.h"):
            pass
            #
            # It turns out that generating a SIP file is the wrong thing for version files. TODO: create
            # a .py file directly.
            #
            if False:
                version_defines = re.compile("^#define\s+(?P<name>\S+_VERSION\S*)\s+(?P<value>.+)")
                with open(h_file, "rU") as f:
                    for line in f:
                        match = version_defines.match(line)
                        if match:
                            result += "{} = {}\n".format(match.group("name"), match.group("value"))
        else:
            result, modulecode, all_includes = generator.create_sip(h_file, h_suffix)
            direct_includes = [i.include.name for i in all_includes() if i.depth == 1]
        if result:
            pass
        elif len(direct_includes) == 1:
            #
            # A non-empty SIP file could not be created from the header file. That would be fine except that a
            # common pattern is to use a single #include to create a "forwarding header" to map a legacy header
            # (usually lower case, and ending in .h) into a CamelCase header. Handle the forwarding case...
            #
            if direct_includes[0].startswith(h_root):
                #
                # We could just %Include the other file, but that would ignore the issues that:
                #
                #    - On filesystems without case sensitive semantics (NTFS) the two filenames usually only
                #      differ in case; actually expanding inline avoids making this problem worse (even if it
                #      is not a full solution).
                #    - The forwarding SIP's .so binding needs the legacy SIP's .so on the system, doubling the
                #      number of libraries (and adding to overall confusion, and the case-sensitivity issue).
                #
                result, modulecode, all_includes = generator.create_sip(direct_includes[0], h_suffix)
                direct_includes = [i.include.name for i in all_includes() if i.depth == 1]
        #
        # From the set of includes, we want two things:
        #
        #   1. Infer the %Import'd items this SIP file depends on. We get this from the directly included files.
        #
        #   2. Infer the set of -I<path> paths needed to compile the SIP compiler output. We get this from all
        #      included files (trimmed to omit ones from paths we did not explicity add to get rid of compiler-added
        #      files and the like).
        #
        # First the %Import...
        #
        tmp = set()
        for include in direct_includes:
            #
            # Deal with oddities such as a/b/c/../x, or repeated separators.
            #
            include = os.path.normpath(include)
            for i_path in i_paths:
                if include.startswith(i_path):
                    tmp.add(include)
                    break
        direct_includes = list(tmp)
        #
        # Now the -I<path>...starting with the current file, construct a directory of sets keyed
        # by all possible include paths.
        #
        tmp = {h_root: set()}
        tmp[h_root].add(os.path.dirname(h_suffix))
        for i_path in i_paths:
            tmp.setdefault(i_path, set())
        for include in all_includes():
            #
            # Deal with oddities such as a/b/c/../x, or repeated separators. Then, under the
            # matching include path, add the suffix of the actual include file.
            #
            include = include.include.name
            include = os.path.normpath(include)
            for i_path in tmp:
                if include.startswith(i_path):
                    trimmed_include = include[len(i_path) + len(os.path.sep):]
                    trimmed_include = os.path.dirname(trimmed_include)
                    tmp[i_path].add(trimmed_include)
                    break
        #
        # Now, construct a new version of i_paths that has *everything*.
        #
        i_paths = set()
        for i_path, trimmed_includes in tmp.items():
            i_paths.add(i_path)
            for trimmed_include in trimmed_includes:
                while trimmed_include:
                    #
                    # Without reading the source code, we don't know exactly how long the -I<path> had to be, so we add
                    # all possible lengths.
                    #
                    possible_i_path = os.path.join(i_path, trimmed_include)
                    i_paths.add(possible_i_path)
                    trimmed_include = os.path.dirname(trimmed_include)
        i_paths = list(i_paths)
        if result:
            #
            # Remove funny characters: the results must be Python-valid names.
            #
            module_file = h_suffix
            for funny in ModuleGenerator.FUNNY_CHARS:
                module_file = module_file.replace(funny, "_")
            #
            # Generate a file header. We can always use a .sip suffix because the caller took care of any possible
            # clash of forwarding header with a legacy header on filesystems with case-insensitive lookups (NTFS).
            #
            sip_basename = os.path.basename(module_file)
            sip_basename = os.path.splitext(sip_basename)[0] + ".sip"
            module_path = os.path.dirname(module_file)
            #
            # The SIP compiler ges very confused if you have a filename that matches a search path. Decollide...
            #
            if sip_basename == os.path.basename(module_path):
                sip_basename += "_"
            sip_suffix = os.path.join(module_path, sip_basename)
            header_text = header(sip_suffix, h_suffix, package)
            #
            # Write the header and the body.
            #
            sip_file = os.path.join(output_dir, sip_suffix)
            try:
                os.makedirs(os.path.dirname(sip_file))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            logger.info(_("Creating {}").format(sip_file))
            with open(sip_file, "w") as f:
                f.write(header_text)
                f.write(result)

            def add_used(rule, usage_count):
                """
                Fill the dict of the used rules.
                """
                if usage_count > 0:
                    rule_usage[str(rule)] = usage_count

            generator.compiled_rules.dump_unused(add_used)
        else:
            logger.info(_("Not creating empty SIP for {}").format(h_file))
    except Exception as e:
        logger.error("{} while processing {}".format(e, h_file))
        #
        # Tracebacks cannot be pickled for use by multiprocessing.
        #
        e = (e.__class__, str(e), traceback.format_exc())
        return h_file, sip_suffix, modulecode, direct_includes, i_paths, rule_usage, e
    return h_file, sip_suffix, modulecode, direct_includes, i_paths, rule_usage, None


def header(output_file, h_file, package):
    """
    Override this to get your own preferred file header.

    :param output_file:                 The name of the output file.
    :param h_file:                      The name of the input file.
    :param package: 
    :return:
    """
    template = """//
// This file, {}, is part of {}.
// It was derived from {}.
//
%Copying
// Copyright (c) {} by Shaheed Haque (srhaque@theiet.org)
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU Library General Public License as
// published by the Free Software Foundation; either version 2, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details
//
// You should have received a copy of the GNU Library General Public
// License along with this program; if not, write to the
// Free Software Foundation, Inc.,
// 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
%End
//
"""
    return template.format(output_file, package, h_file, datetime.datetime.utcnow().year)


def get_platform_dependencies():
    """
    Find the system include directories and libclang.so.
    """
    data = rules_engine.get_platform_dependencies(os.path.dirname(os.path.realpath(__file__)))
    sys_includes = data["ClangPP_SYS_INCLUDES"].split(";")
    sys_includes = [str(os.path.normpath(i)) for i in sys_includes]
    if not sys_includes:
        raise RuntimeError(_("Cannot find system includes"))
    lib_clang = data["LibClang_LIBRARY"]
    exe_clang = data["ClangPP_EXECUTABLE"]
    exe_sip = data["SIP_EXECUTABLE"]
    logger.info(_("Found Clang: {}, {}, {}").format(lib_clang, exe_clang, sys_includes))
    logger.info(_("Found SIP: {}").format(exe_sip))
    return lib_clang, exe_clang, sys_includes, exe_sip


def main(argv=None):
    """
    Convert a whole set of header files and generate the corresponding SIP
    files. Beyond simple generation of the SIP files from the corresponding C++
    header files:

        - A set of rules can be used to customise the generated SIP files.

        - For each set of SIP files in a directory, if at least one SIP file
          is named like a new-style header (i.e. starts with an upper case
          letter, or has no .h suffix), then a "module.sip" is created which
          facilitates running the SIP compiler on a set of related files.

    Examples:

        module_generator.py /tmp /usr/include/KF5
    """
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(epilog=inspect.getdoc(main),
                                     formatter_class=HelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help=_("Enable verbose output"))
    parser.add_argument("--select", default=".*", type=lambda s: re.compile(s, re.I),
                        help=_("Regular expression of C++ headers from 'rules-pkg' to be processed"))
    parser.add_argument("--omit", default="=Nothing=", type=lambda s: re.compile(s, re.I),
                        help=_("Regular expression of C++ headers from 'rules-pkg' NOT to be processed"))
    parser.add_argument("-j", "--jobs", type=int, default=multiprocessing.cpu_count(),
                        help=_("Number of parallel jobs, 0 for serial inline operation"))
    parser.add_argument("--dump-rule-usage", action="store_true", default=False,
                        help=_("Emit rule usage statistics"))
    parser.add_argument("--dump-includes", action="store_true", default=False,
                        help=_("Emit diagnostics for include files"))
    parser.add_argument("--dump-privates", action="store_true", default=False,
                        help=_("Emit diagnostics for omitted private items"))
    parser.add_argument("--dump-modules", action="store_true", default=False,
                        help=_("Emit tracing for modules"))
    parser.add_argument("--dump-items", action="store_true", default=False,
                        help=_("Emit tracing for container members"))
    parser.add_argument("rules", help=_("Project rules package"))
    parser.add_argument("output", help=_("SIP output directory"))
    try:
        args = parser.parse_args(argv[1:])
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        #
        # Generate!
        #
        rules_pkg = os.path.normpath(args.rules)
        output = os.path.normpath(args.output)
        d = ModuleGenerator(rules_pkg, output, dump_modules=args.dump_modules, dump_items=args.dump_items,
                            dump_includes=args.dump_includes, dump_privates=args.dump_privates)
        attempts, failures, directories = d.process_tree(args.jobs, args.select, args.omit)
        if args.dump_rule_usage:
            for rule in sorted(d.rule_usage.keys()):
                usage_count = d.rule_usage[rule]
                if usage_count:
                    logger.info(_("Rule {} used {} times".format(rule, usage_count)))
                else:
                    logger.warn(_("Rule {} was not used".format(rule)))
        #
        # Dump a summary of what we did. Order the results by the name of the source.
        #
        for source, e in failures:
            logger.info(_("Summary: {}: {} while processing {}").format(e[0].__name__, e[1], source))
        level = logging.ERROR if failures else logging.INFO
        logger.log(level, _("Summary: {} processing errors for {} files in {} modules").format(len(failures), attempts,
                                                                                               directories))
        if failures:
            tbk = failures[0][1][2]
            print(tbk)
            return -1
    except Exception as e:
        tbk = traceback.format_exc()
        print(tbk)
        return -1


if __name__ == "__main__":
    sys.exit(main())
