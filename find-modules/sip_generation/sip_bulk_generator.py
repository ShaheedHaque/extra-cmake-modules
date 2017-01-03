#!/usr/bin/env python
#=============================================================================
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
#=============================================================================
"""SIP file generator driver for PyKDE."""
from __future__ import print_function
import argparse
import datetime
import errno
import gettext
import os
import inspect
import logging
import re
import string
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


def feature_for_sip_module(sip_file):
    """Convert a SIP module name into a feature name."""
    return os.path.splitext(sip_file)[0].replace(os.path.sep, "_").replace(".", "_").replace("+", "_")


class SipBulkGenerator(SipGenerator):
    def __init__(self, module_name, project_rules, compile_flags, includes, sips, omitter, selector, project_root, output_dir):
        """
        Constructor.

        :param module_name:         The module name for the project.
        :param project_rules:       The rules for the project.
        :param compile_flags:       The compile flags for the file.
        :param includes:            Comma-separated CXX includes directories to use.
        :param sips:                Comma-separated SIP module directories to use.
        :param omitter:             A regular expression which sets the files from project_root NOT to be processed.
        :param selector:            A regular expression which limits the files from project_root to be processed.
        :param project_root:        The root of files for which to generate SIP.
        :param output_dir:          The destination SIP directory.
        """
        super(SipBulkGenerator, self).__init__(project_rules, compile_flags)
        self.module_name = module_name
        self.includes = includes
        self.sips = sips.lstrip().split(",")
        self.root = project_root
        self.omitter = omitter
        self.selector = selector
        self.output_dir = output_dir
        #
        # One of the problems we want to solve is that for each #include in the transitive fanout for a .h under
        # self.root, we need to insert a %Import for the corresponding module-level .sip. To do this, we assume
        # that for the relative path aaa/bbb/ccc/foo/bar.h, the needed module is at aaa/bbb/ccc/foo/foomod.sip.
        #
        # However, this is made tricky because we want to use new-style CamelCase names whereever possible:
        #
        #   - Under self.sips, we simply walk the directory structure, folding into any non-lower-case-only names when
        #     possible, and add each xxxmod.sip we find to the available set.
        #
        #   - Under self.output_dir, of course, the .sip files don't actually exist before we start running. So here,
        #     we walk self.root, folding into any non-lower-case-only names when possible, and add the xxxxmod.sip
        #     name that will be created to the available set.
        #
        self.include_to_import_cache = {}
        for sip_root in self.sips:
            sips = []
            self.find_existing_module_sips(sips, sip_root)
            self.add_include_to_sip_mappings(sips, sip_root)
        sips = []
        self.predict_new_module_sips(sips, self.root)
        self.add_include_to_sip_mappings(sips, self.root)
        self.predicted_sips = [s[len(self.output_dir) + len(os.path.sep):] for s in sips]
        self.all_features = None

    def find_existing_module_sips(self, all_sips, root):
        """
        Find all existing module .sip files, folding away any non-lower-case-only duplicates.
        """
        names = sorted(os.listdir(root))
        forwarding_names = [n for n in names if n != n.lower() and n.lower() in names]
        for name in forwarding_names:
            logger.debug(_("Ignoring legacy name for {}").format(os.path.join(root, name)))
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
            logger.debug(_("Ignoring legacy name for {}").format(os.path.join(root, name)))
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
            self.include_to_import_cache[module_dir.lower()] = sip

    def process_tree(self):
        self.all_features = set()
        self._walk_tree(self.root)
        feature_list = os.path.join(self.output_dir, "modules.features")
        #
        # TODO, make sure the entries are unique.
        #
        with open(feature_list, "w") as f:
            for feature in self.all_features:
                f.write("%Feature(name={})\n".format(feature))

    def _walk_tree(self, root):
        """
        Walk over a directory tree and for each file or directory, apply a function.

        :param root:                Tree to be walked.
        """
        direct_sips = set()
        all_include_roots = set()
        names = sorted(os.listdir(root))
        sip_files = []
        #
        # Eliminate the duplication of forwarding headers.
        #
        forwarding_headers = [h for h in names if not h.endswith(".h") and h.lower() + ".h" in names]
        for h in forwarding_headers:
            logger.debug(_("Ignoring legacy header for {}").format(os.path.join(root, h)))
            names.remove(h.lower() + ".h")
        #
        # Eliminate the duplication of forwarding directories.
        #
        forwarding_directories = [h for h in names if h != h.lower() and h.lower() in names]
        for h in forwarding_directories:
            logger.debug(_("Ignoring legacy directory for {}").format(os.path.join(root, h)))
            names.remove(h.lower())
        for name in names:
            srcname = os.path.join(root, name)
            if os.path.isfile(srcname):
                sip_file, direct_includes = self._process_one(srcname)
                if sip_file:
                    sip_files.append(sip_file)
                    #
                    # Create something which the SIP compiler can process that includes what appears to be the
                    # immediate fanout from this module.
                    #
                    for include in direct_includes:
                        all_include_roots.add(os.path.dirname(include))
                    #
                    # For each include, add the corresponding SIP module to the set to be %Import'd.
                    #
                    for include in direct_includes:
                        if self.omitter.search(include):
                            continue
                        if include.endswith(("_export.h", "_version.h")):
                            continue
                        sip = self._map_include_to_import(include)
                        direct_sips.add(sip)
            elif os.path.isdir(srcname):
                self._walk_tree(srcname)
        #
        # Create a SIP module including all the SIP files in this directory.
        #
        # NOTE: this is really only best-effort; the output here might have to be edited, or indeed
        # module files may need to be created from scratch if the logic here is not good enough.
        #
        if sip_files:
            h_dir = root[len(self.root) + len(os.path.sep):]
            module = h_dir.replace(os.path.sep, ".")
            output_file = os.path.join(h_dir, os.path.basename(h_dir) + MODULE_SIP)
            decl = self.header(output_file, h_dir, h_dir)
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
            decl += "%Module(name={}.{})\n".format(self.module_name, module)
            #
            # Create something which the SIP compiler can process that includes what appears to be the
            # immediate fanout from this module.
            #
            for sip_import in sorted(direct_sips):
                #
                # Protect each %Import with a feature. The point of this is that we often see module A and B
                # which need to %Import each other; this confuses the SIP compiler which does not like the
                # %Import A encountered in B while processing A's %Import of B. However, we cannot simply
                # declare the corresponding %Feature here because then we will end up with the same %Feature in
                # both A and B which SIP also does not like.
                #
                if sip_import == output_file:
                    pass
                elif sip_import in self.predicted_sips:
                    feature = feature_for_sip_module(sip_import)
                    self.all_features.add(feature)
                    decl += "%If ({})\n".format(feature)
                    decl += "%Import(name={})\n".format(sip_import)
                    decl += "%End\n"
                else:
                    decl += "%Import(name={})\n".format(sip_import)
            decl += "%Extract(id={})\n".format(INCLUDES_EXTRACT)
            for include in sorted(all_include_roots):
                decl += "{}\n".format(include)
            decl += "%End\n"
            #
            # Add all peer .sip files.
            #
            for sip_file in sip_files:
                decl += "%Include(name={})\n".format(sip_file)
            #
            # Any module-related manual code (%ExportedHeaderCode, %ModuleCode, %ModuleHeaderCode or other
            # module-level directives?
            #
            sip = {
                "name": module,
                "decl": decl
            }
            self.rules.modulecode(os.path.basename(full_output), sip)
            decl = sip["decl"] + sip["code"]
            with open(full_output, "w") as f:
                f.write(decl)


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
        logger.warn(_("Cannot find SIP for {}").format(include))

    def _process_one(self, source):
        """
        Walk over a directory tree and for each file or directory, apply a function.

        :param source:              Source to be processed.
        :return:                    (output_file, set(direct includes from this file))
        """
        h_file = source[len(self.root) + len(os.path.sep):]
        if self.selector.search(h_file) and not self.omitter.search(h_file):
            #
            # Make sure any errors mention the file that was being processed.
            #
            try:
                if h_file.endswith("_export.h"):
                    result, includes = "", lambda : []
                elif h_file.endswith("_version.h"):
                    result, includes = "", lambda : []
                    #
                    # It turns out that generating a SIP file is the wrong thing for version files. TODO: create
                    # a .py file directly.
                    #
                    if False:
                        version_defines = re.compile("^#define\s+(?P<name>\S+_VERSION\S*)\s+(?P<value>.+)")
                        with open(source, "rU") as f:
                            for line in f:
                                match = version_defines.match(line)
                                if match:
                                    result += "{} = {}\n".format(match.group("name"), match.group("value"))
                else:
                    result, includes = self.create_sip(self.root, h_file)
                direct_includes = [i.include.name for i in includes() if i.depth == 1]
                if result:
                    pass
                elif len(direct_includes) == 1:
                    #
                    # A non-empty SIP file could not be created from the header file. That would be fine except that a
                    # common pattern is to use a single #include to create a "forwarding header" to map a legacy header
                    # (usually lower case, and ending in .h) into a CamelCase header. Handle the forwarding case...
                    #
                    if direct_includes[0].startswith(self.root):
                        forwardee = direct_includes[0]
                        forwardee = forwardee[len(self.root) + len(os.path.sep):]
                        #
                        # We could just %Include the other file, but that would ignore the issues that:
                        #
                        #    - On filesystems without case sensitive semantics (NTFS) the two filenames usually only
                        #      differ in case; actually expanding inline avoids making this problem worse (even if it
                        #      is not a full solution).
                        #    - The forwarding SIP's .so binding needs the legacy SIP's .so on the system, doubling the
                        #      number of libraries (and adding to overall confusion, and the case-sensitivity issue).
                        #
                        result, includes = self.create_sip(self.root, forwardee)
                        direct_includes = [i.include.name for i in includes() if i.depth == 1]
                else:
                    direct_includes = []
                #
                # Trim the includes to omit ones from paths we did not explicity add. This should get rid of compiler
                # added files and the like.
                #
                tmp = set()
                for di in direct_includes:
                    #
                    # Deal with oddities such as a/b/c/../x, or repeated separators.
                    #
                    di = os.path.normpath(di)
                    for si in self.includes:
                        if di.startswith(si):
                            di = di[len(si) + len(os.path.sep):]
                            tmp.add(os.path.join(si, di))
                            break
                direct_includes = tmp
            except Exception as e:
                logger.error("{} while processing {}".format(e, source))
                raise
            if result:
                #
                # Generate a file header. We can always use a .sip suffix because the caller took care of any possible
                # clash of forwarding header with a legacy header on filesystems with case-insensitive lookups (NTFS).
                #
                sip_basename = os.path.basename(h_file)
                sip_basename = os.path.splitext(sip_basename)[0] + ".sip"
                module_path = os.path.dirname(h_file)
                #
                # The SIP compiler ges very confused if you have a filename that matches a search path. Decollide...
                #
                if sip_basename == os.path.basename(module_path):
                    sip_basename += "_"
                output_file = os.path.join(module_path, sip_basename)
                header = self.header(output_file, h_file, module_path)
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
                with open(full_output, "w") as f:
                    f.write(header)
                    f.write(result)
                return output_file, direct_includes
            else:
                logger.info(_("Not creating empty SIP for {}").format(source))
        else:
            logger.debug(_("Selector discarded {}").format(source))
        return None, None

    def header(self, output_file, h_file, module_path):
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
""".format(output_file, self.module_name, h_file, datetime.datetime.utcnow().year)
        return header


def walk_directories(root, fn):
    """
    Walk over a directory tree and for each directory, apply a function.
    :param root:                Tree to be walked.
    :param fn:                  Function to apply.
    :return: None
    """
    names = os.listdir(root)
    for name in names:
        srcname = os.path.join(root, name)
        if os.path.isdir(srcname):
            fn(srcname)
        if os.path.isdir(srcname):
            walk_directories(srcname, fn)


def find_libclang():
    """"
    Find the libclang.so to alow us to initialise the system.
    """
    lines = subprocess.check_output(["/sbin/ldconfig", "-p"])
    for line in lines.split("\n"):
        fields = line.split()
        if fields and re.match("libclang.*\.so", fields[0]):
            libclang = fields[-1]
            logger.debug(_("Found libclang at {}").format(libclang))
            return libclang
    raise RuntimeError(_("Cannot find libclang"))


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
    parser.add_argument("--includes", default="/usr/include/x86_64-linux-gnu/qt5",
                        help=_("Comma-separated C++ header directories to use"))
    parser.add_argument("--sips", default="/usr/share/sip/PyQt5",
                        help=_("Comma-separated SIP module directories to use"))
    parser.add_argument("--module-name", default="PyKF5", help=_("Module name"))
    parser.add_argument("--project-rules", default=os.path.join(os.path.dirname(__file__), "PyKF5_rules.py"),
                        help=_("Project rules"))
    parser.add_argument("--select", default=".*", type=lambda s: re.compile(s, re.I),
                        help=_("Regular expression of C++ headers under 'sources' to be processed"))
    parser.add_argument("--omit", default="KDELibs4Support", type=lambda s: re.compile(s, re.I),
                        help=_("Regular expression of C++ headers under sources NOT to be processed"))
    parser.add_argument("--dump-rule-usage", action="store_true", default=False,
                        help=_("Debug dump rule usage statistics"))
    parser.add_argument("sip", help=_("SIP output directory"))
    parser.add_argument("sources", default="/usr/include/KF5", nargs="?", help=_("C++ header directory to process"))
    try:
        args = parser.parse_args(argv[1:])
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        #
        # Find and load the libclang.
        #
        cindex.Config.set_library_file(find_libclang())
        #
        # Generate!
        #
        rules = rules_engine.rules(args.project_rules)
        includes = args.includes.lstrip().split(",") + [args.sources]
        exploded_includes = set(includes)
        for include_root in includes:
            walk_directories(include_root, lambda d: exploded_includes.add(d))
        d = SipBulkGenerator(args.module_name, rules, ["-I" + i for i in exploded_includes], includes, args.sips, args.omit, args.select, args.sources, args.sip)
        d.process_tree()
        if args.dump_rule_usage:
            rules.dump_unused()
    except Exception as e:
        tbk = traceback.format_exc()
        print(tbk)
        return -1


if __name__ == "__main__":
    sys.exit(main())
