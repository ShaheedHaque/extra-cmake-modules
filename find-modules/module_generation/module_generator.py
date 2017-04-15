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
import os
import inspect
import logging
import multiprocessing
from multiprocessing.pool import Pool
import re
import subprocess
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
PYQT5_SIPS = "/usr/share/sip/PyQt5"
PYKF5_SOURCES = "/usr/include/KF5"
PYKF5_INCLUDES = "/usr/include/x86_64-linux-gnu/qt5,/usr/lib/x86_64-linux-gnu/qt5/mkspecs/linux-g++-64,/usr/include/libxml2"
PYKF5_LIBRARIES = "/usr/lib/x86_64-linux-gnu/libKF5*.so"
PYKF5_RULES = "PyKF5_rules/__init__.py"
PYKF5_PACKAGE_NAME = "PyKF5"
CLANG_PATHS = "clang++-3.9,libclang-3.9.so"
QT5_COMPILE_FLAGS = "-fPIC,-std=gnu++14"
FILE_SORT_KEY=str.lower


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

    def add_remote_stats(self, rule_dict):
        """
        Statistics from remote processes where we do not have access to the rule database directly (not least because
        rule databases contain regular expression which cannot be pickled).

        :param rule_set:
        :return:
        """
        for rule, usage_count in rule_dict.items():
            self.setdefault(rule, 0)
            self[rule] += usage_count


class ModuleGenerator(object):
    def __init__(self, package, project_rules, compile_flags, includes, sips, project_root, output_dir):
        """
        Constructor.

        :param package:             The name of the Python package.
        :param project_rules:       The rules for the project.
        :param compile_flags:       The compile flags for the file.
        :param includes:            Comma-separated CXX includes directories to use.
        :param sips:                Comma-separated SIP module directories to use.
        :param project_root:        The root of files for which to generate SIP.
        :param output_dir:          The destination SIP directory.
        """
        super(ModuleGenerator, self).__init__()
        self.project_rules = project_rules
        self.compile_flags = compile_flags
        self.package = package
        self.includes = includes
        self.sips = sips.lstrip().split(",")
        self.project_root = project_root
        self.output_dir = output_dir
        #
        # One of the problems we want to solve is that for each #include in the transitive fanout for a .h under
        # self.project_root, we need to insert a %Import for the corresponding module-level .sip. To do this, we assume
        # that for the relative path aaa/bbb/ccc/foo/bar.h, the needed module is at aaa/bbb/ccc/foo/foomod.sip.
        #
        # However, this is made tricky because we want to use new-style CamelCase names whereever possible:
        #
        #   - Under self.sips, we simply walk the directory structure, folding into any non-lower-case-only names when
        #     possible, and add each xxxmod.sip we find to the available set.
        #
        #   - Under self.output_dir, of course, the .sip files don't actually exist before we start running. So here,
        #     we walk self.project_root, folding into any non-lower-case-only names when possible, and add the xxxxmod.sip
        #     name that will be created to the available set.
        #
        self.include_to_import_cache = {}
        for sip_root in self.sips:
            sips = []
            self.find_existing_module_sips(sips, sip_root)
            self.add_include_to_sip_mappings(sips, sip_root)
        sips = []
        self.predict_new_module_sips(sips, self.project_root)
        self.add_include_to_sip_mappings(sips, self.project_root)
        self.predicted_sips = [s[len(self.project_root) + len(os.path.sep):] for s in sips]
        self.all_features = None
        self.rule_usage = RuleUsage()
        self.omitter = None
        self.selector = None

    def find_existing_module_sips(self, all_sips, root):
        """
        Find all existing module .sip files, folding away any non-lower-case-only duplicates.
        """
        names = sorted(os.listdir(root))
        forwarding_names = [n for n in names if n != n.lower() and n.lower() in names]
        for name in forwarding_names:
            #
            # _("Ignoring legacy name for {}").format(os.path.join(root, name)))
            #
            names.remove(name.lower())
        for name in names:
            srcname = os.path.join(root, name)
            if os.path.isfile(srcname):
                if srcname.endswith(MODULE_SIP):
                    all_sips.append(srcname)
            elif os.path.isdir(srcname):
                self.find_existing_module_sips(all_sips, srcname)

    def predict_new_module_sips(self, all_sips, root):
        """
        Predict all the new module .sip files we *might* create.
        """
        names = sorted(os.listdir(root))
        forwarding_names = [n for n in names if n != n.lower() and n.lower() in names]
        for name in forwarding_names:
            #
            # _("Ignoring legacy name for {}").format(os.path.join(root, name)))
            #
            names.remove(name.lower())
        for name in names:
            srcname = os.path.join(root, name)
            if os.path.isdir(srcname):
                sip = os.path.basename(srcname) + MODULE_SIP
                sip = os.path.join(srcname, sip)
                all_sips.append(sip)
                self.predict_new_module_sips(all_sips, srcname)

    def add_include_to_sip_mappings(self, all_sips, root):
        for sip in all_sips:
            sip = sip[len(root) + len(os.path.sep):]
            module_dir = os.path.dirname(sip)
            for funny in ModuleGenerator.FUNNY_CHARS:
                sip = sip.replace(funny, "_")
            self.include_to_import_cache[module_dir.lower()] = sip

    def process_tree(self, jobs, omitter, selector):
        """
        Run a set of SIP modules, but don't throw any errors.
        
        :param jobs:                How many jobs to run in parallel? 0 for serial inline (debug) mode.
        :param omitter:             A regular expression which sets the files from project_root NOT to be processed.
        :param selector:            A regular expression which limits the files from project_root to be processed.
        :return: (attempts, [failures])
        """
        self.omitter = omitter
        self.selector = selector
        self.all_features = []
        compiled_rules = rules_engine.rules(self.project_rules)
        attempts = 0
        failures = []
        directories = 0
        for dirpath, dirnames, filenames in os.walk(self.project_root):
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
            forwarding_directories = [h for h in dirnames if h != h.lower() and h.lower() in dirnames]
            for h in forwarding_directories:
                #
                # _("Ignoring legacy directory for {}").format(os.path.join(dirpath, h)))
                #
                dirnames.remove(h.lower())
            #
            # Use sorted walks.
            #
            dirnames.sort(key=FILE_SORT_KEY)
            filenames.sort(key=FILE_SORT_KEY)
            a, f = self.process_dir(jobs, compiled_rules, dirpath, filenames)
            attempts += a
            failures += f
            if a:
                directories += 1
        feature_list = os.path.join(self.output_dir, "modules.features")
        #
        # TODO, make sure the entries are unique.
        #
        with open(feature_list, "w") as f:
            for feature in self.all_features:
                f.write("%Feature(name={})\n".format(feature))
        self.rule_usage.add_local_stats(compiled_rules)
        return attempts, failures, directories

    FUNNY_CHARS = "+"

    def process_dir(self, jobs, compiled_rules, dirname, filenames):
        """
        Walk over a directory tree and for each file or directory, apply a function.

        :param root:                Tree to be walked.
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
            if self.selector.search(h_file) and not self.omitter.search(h_file):
                per_process_args.append((source, h_file))
        if not per_process_args:
            return attempts, failures
        std_args = (self.project_root, self.project_rules, self.compile_flags, self.includes, self.output_dir, self.package)
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
        mapped_types = {}
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
                mapped_types.update(tmp)
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
                    if self.omitter.search(include):
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
            #
            # Remove funny characters: the results must be Python-valid names.
            #
            for funny in ModuleGenerator.FUNNY_CHARS:
                h_dir = h_dir.replace(funny, "_")
            module = h_dir.replace(os.path.sep, ".")
            output_file = os.path.join(h_dir, os.path.basename(h_dir) + MODULE_SIP)
            #
            # Write the header and the body.
            #
            full_output = os.path.join(self.output_dir, output_file)
            try:
                os.makedirs(os.path.dirname(full_output))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            logger.info(_("Creating {}").format(full_output))
            decl = "%Module(name={}.{})\n".format(self.package, module)
            decl += """
%ModuleHeaderCode
#pragma GCC visibility push(default)
%End
"""
            feature = feature_for_sip_module(output_file)
            self.all_features.append(feature)
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
                if sip_import in self.predicted_sips:
                    if sip_import != output_file:
                        feature = feature_for_sip_module(sip_import)
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
                "mapped_types": mapped_types,
                "peers": peers,
            }
            body = ""
            modifying_rule = compiled_rules.modulecode(os.path.basename(full_output), sip)
            if modifying_rule:
                body += "// Modified {} (by {}):\n".format(os.path.basename(full_output), modifying_rule)
            with open(full_output, "w") as f:
                f.write(header(output_file, h_dir, h_dir, self.package))
                f.write(body)
                f.write(sip["decl"])
                #
                # The mapped_types dictionary ensures there can be no duplicates, even if multiple sip files might have
                # contributed the same item. By emitting it here, it can provide declare-before-use (needed for
                # %Exceptions).
                #
                # Also, since SIP cannot cope with the same %MappedType in different modules, the rules can be
                # used to eliminate the duplicates.
                #
                f.write("\n")
                for mt in sorted(mapped_types):
                    f.write(mapped_types[mt])
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
                parents = os.path.dirname(tmp).lower()
                try:
                    return self.include_to_import_cache[parents]
                except KeyError:
                    break
        return None


def process_one(h_file, h_suffix, h_root, project_rules, compile_flags, i_paths, output_dir, package):
    """
    Walk over a directory tree and for each file or directory, apply a function.

    :param h_file:              Source to be processed.
    :param h_suffix:            Source to be processed, right hand side of name.
    :param h_root:              Config
    :param project_rules:       Config
    :param compile_flags:       Config
    :param i_paths:             Config
    :param output_dir:          Config
    :param package:             Config
    :return:                    (
                                    source,
                                    sip_suffix,
                                    dict(mapped_types),
                                    [direct includes from h_file],
                                    [-I paths needed by h_file],
                                    dict(rule_usage),
                                    error,
                                )
    """
    #
    # Make sure any errors mention the file that was being processed.
    #
    try:
        compiled_rules = rules_engine.rules(project_rules)
        generator = SipGenerator(compiled_rules, compile_flags)
        sip_suffix = None
        result, mapped_types, all_includes, direct_includes, rule_usage = "", {}, lambda: [], set(), {}
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
            result, mapped_types, all_includes = generator.create_sip(h_file, h_suffix)
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
                result, mapped_types, all_includes = generator.create_sip(direct_includes[0], h_suffix)
                direct_includes = [i.include.name for i in all_includes() if i.depth == 1]
        else:
            direct_includes = []
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
        tmp = []
        for include in direct_includes:
            #
            # Deal with oddities such as a/b/c/../x, or repeated separators.
            #
            include = os.path.normpath(include)
            for i_path in i_paths:
                if include.startswith(i_path):
                    if include not in tmp:
                        tmp.append(include)
                    break
        direct_includes = tmp
        #
        # Now the -I<path>...start with the current file.
        #
        i_paths = list(i_paths)
        tmp = {h_root: [os.path.dirname(h_suffix)]}
        for include in all_includes():
            #
            # Deal with oddities such as a/b/c/../x, or repeated separators.
            #
            include = include.include.name
            include = os.path.normpath(include)
            for i_path in i_paths:
                if include.startswith(i_path):
                    trimmed_include = include[len(i_path) + len(os.path.sep):]
                    trimmed_include = os.path.dirname(trimmed_include)
                    tmp.setdefault(i_path, [])
                    if trimmed_include not in tmp[i_path]:
                        tmp[i_path].append(trimmed_include)
                    break
        for i_path, trimmed_includes in tmp.items():
            for trimmed_include in trimmed_includes:
                while trimmed_include:
                    #
                    # Without reading the source code, we don't know exactly how long the -I<path> had to be, so we add
                    # all possible lengths.
                    #
                    possible_i_path = os.path.join(i_path, trimmed_include)
                    if possible_i_path not in i_paths:
                        i_paths.append(possible_i_path)
                    trimmed_include = os.path.dirname(trimmed_include)
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
            header_text = header(sip_suffix, h_suffix, module_path, package)
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
            #
            # Fill the dict of the used rules.
            #
            def add_used(rule, usage_count):
                if usage_count > 0:
                    rule_usage[str(rule)] = usage_count

            compiled_rules.dump_unused(add_used)
        else:
            logger.info(_("Not creating empty SIP for {}").format(h_file))
    except Exception as e:
        logger.error("{} while processing {}".format(e, h_file))
        #
        # Tracebacks cannot be pickled for use by multiprocessing.
        #
        e = (e.__class__, str(e), traceback.format_exc())
        return h_file, sip_suffix, mapped_types, direct_includes, i_paths, rule_usage, e
    return h_file, sip_suffix, mapped_types, direct_includes, i_paths, rule_usage, None


def header(output_file, h_file, module_path, package):
    """
    Override this to get your own preferred file header.

    :param output_file:                 The name of the output file.
    :param h_file:                      The name of the input file.
    :param module_path:                 The delta from the root.
    :return:
    """
    header = """//
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
""".format(output_file, package, h_file, datetime.datetime.utcnow().year)
    return header


def find_clang(exe_clang, lib_clang):
    """"
    Find the clang++, system include directories and libclang.so.
    """
    sys_includes = []
    #
    # Look for a usable executable.
    #
    try:
        lines = subprocess.check_output([exe_clang, "-v", "-E", "-x", "c++", "/dev/null"], stderr=subprocess.STDOUT)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise RuntimeError(_("Unable to find {}").format(exe_clang))
    lines = lines.split("\n")
    #
    # Try to find the system includes. Modelled on the logic in extra-cmake-modules...
    #
    start = None
    end = None
    for i in reversed(range(len(lines))):
        if lines[i].find("search starts here") != -1:
            start = i + 1
            break
    for i in range(len(lines)):
        if lines[i].find("End of search list") != -1:
            end = i
            break
    assert start and end, _("Unable to find system includes in {}").format(lines)
    # on OSX, gcc says things like this:  "/System/Library/Frameworks (framework directory)"
    sys_includes = [l.replace("(framework directory)", "") for l in lines[start:end]]
    sys_includes = [l.strip() for l in sys_includes]
    if not sys_includes:
        RuntimeError(_("Cannot find system includes"))
    lines = subprocess.check_output(["/sbin/ldconfig", "-p"])
    for line in lines.split("\n"):
        fields = line.split()
        if fields and fields[0].endswith(lib_clang):
            lib_clang = fields[-1]
            logger.debug(_("Found libclang at {}").format(lib_clang))
    if not lib_clang:
        raise RuntimeError(_("Cannot find libclang"))
    logger.info(_("Found {} and {}").format(exe_clang, lib_clang))
    return exe_clang, sys_includes, lib_clang


def main(argv=None):
    """
    Convert a whole set of KDE header files and generate the corresponding SIP
    files. Beyond simple generation of the SIP files from the corresponding C++
    header files:

        - A set of rules can be used to customise the generated SIP files.

        - For each set of SIP files in a directory, if at least one SIP file
          is named like a new-style header (i.e. starts with an upper case
          letter, or has no .h suffix), the a "module.sip" is created which
          facilitates running the SIP compiler on a set of related files.

    Examples:

        sip_bulk_generator.py /tmp /usr/include/KF5
    """
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(epilog=inspect.getdoc(main),
                                     formatter_class=HelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help=_("Enable verbose output"))
    parser.add_argument("--includes", default=PYKF5_INCLUDES + "," + PYKF5_SOURCES,
                        help=_("Comma-separated C++ header directories for includes"))
    parser.add_argument("--clang-paths", default=CLANG_PATHS,
                        help=_("Comma-separated clang++ executable and libclang names"))
    parser.add_argument("--compile-flags", default=QT5_COMPILE_FLAGS,
                        help=_("Comma-separated C++ compiler options to use"))
    parser.add_argument("--imports", default=PYQT5_SIPS,
                        help=_("Comma-separated SIP module directories for imports"))
    parser.add_argument("--package", default=PYKF5_PACKAGE_NAME, help=_("Package name"))
    parser.add_argument("--project-rules", default=os.path.join(os.path.dirname(__file__), PYKF5_RULES),
                        help=_("Project rules"))
    parser.add_argument("--select", default=".*", type=lambda s: re.compile(s, re.I),
                        help=_("Regular expression of C++ headers under 'sources' to be processed"))
    parser.add_argument("--omit", default="KDELibs4Support", type=lambda s: re.compile(s, re.I),
                        help=_("Regular expression of C++ headers under 'sources' NOT to be processed"))
    parser.add_argument("-j", "--jobs", type=int, default=multiprocessing.cpu_count(),
                        help=_("Number of parallel jobs, 0 for serial inline operation"))
    parser.add_argument("--dump-rule-usage", action="store_true", default=False,
                        help=_("Debug dump rule usage statistics"))
    parser.add_argument("sips", help=_("SIP output directory"))
    parser.add_argument("sources", default=PYKF5_SOURCES, nargs="?", help=_("C++ header directory to process"))
    try:
        args = parser.parse_args(argv[1:])
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        #
        # Find and load the libclang.
        #
        exe_clang, sys_includes, lib_clang = find_clang(*args.clang_paths.split(","))
        cindex.Config.set_library_file(lib_clang)
        #
        # Generate!
        #
        sources = os.path.normpath(args.sources)
        includes = args.includes.lstrip().split(",")
        exploded_includes = args.includes.lstrip().split(",")
        for i in includes:
            for dirpath, dirnames, filenames in os.walk(i):
                for d in dirnames:
                    d = os.path.join(dirpath, d)
                    if d not in exploded_includes:
                        exploded_includes.append(d)
        compile_flags = ["-I" + i for i in exploded_includes] + \
                            ["-isystem" + i for i in sys_includes] + \
                            args.compile_flags.split(",")
        d = ModuleGenerator(args.package, args.project_rules, compile_flags, includes, args.imports, sources, args.sips)
        attempts, failures, directories = d.process_tree(args.jobs, args.omit, args.select)
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
