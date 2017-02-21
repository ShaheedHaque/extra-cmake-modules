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
"""Run SIP compiler and C++ compiler for a SIP binding module."""
from __future__ import print_function
import argparse
import errno
import gettext
import glob
import os
import inspect
import logging
import multiprocessing
from multiprocessing.pool import Pool
import re
import shutil
import sipconfig
import subprocess
import sys
import traceback

from PyQt5.QtCore import PYQT_CONFIGURATION

import rules_engine
from module_generator import INCLUDES_EXTRACT, MODULE_SIP, feature_for_sip_module
from module_generator import PYQT5_SIPS, PYKF5_INCLUDES, PYKF5_SOURCES, PYKF5_LIBRARIES, PYKF5_RULES, PYKF5_PACKAGE_NAME


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _


FILE_SORT_KEY=str.lower


class ModuleCompiler(object):
    def __init__(self, package, output, project_rules, sips, includes, imports, libraries, verbose):
        """
        Constructor.

        :param package:             The name of the Python package.
        :param output:              The Python and shippable SIP output directory.
        :param project_rules:       The rules for the project.
        :param sips:                The source SIP directory.
        :param includes:            CXX includes directories to use.
        :param imports:             SIP module directories to use.
        :param libraries:           Globs of library files.
        :param verbose:             Debug info.
        """
        self.package = package
        self.rules = project_rules
        self.input_sips = sips
        self.includes = includes
        self.imports = imports
        self.tmp = os.path.join(output, "tmp")
        self.output_so = os.path.join(output, "python")
        #
        # We are going to process a whole set of modules. We therefore assume
        # we will need to fixup recursive %Imports and create a shippable
        # package of .sip files and bindings.
        #
        self.output_sips = os.path.join(output, "sip")
        self.libraries = []
        for lg in libraries:
            lg = lg.strip()
            libs = [":" + os.path.basename(l) for l in glob.glob(lg)]
            self.libraries.extend(libs)
        self.verbose = verbose
        #
        # Get the SIP configuration information.
        #
        self.sipconfig = sipconfig.Configuration()
        self.pyqt_sip_flags = PYQT_CONFIGURATION["sip_flags"].split()

    def process_tree(self, jobs, selector, omitter):
        """
        Run a set of SIP files, but don't throw any errors.

        :param jobs:                How many jobs to run in parallel? 0 for serial inline (debug) mode.
        :param omitter:             A regular expression which sets the files from project_root NOT to be processed.
        :param selector:            A regular expression which limits the files from project_root to be processed.
        :return: (attempts, [failures])
        """
        #
        # Set up the project output directory.
        #
        for dir in [self.tmp, self.output_so, self.output_sips]:
            try:
                os.makedirs(os.path.join(dir, self.package))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        with open(os.path.join(self.output_so, self.package, "__init__.py"), "w") as f:
            pass
        #
        # If there is a set of features, copy it.
        #
        features = "modules.features"
        try:
            copy_file(self.input_sips, features, os.path.join(self.output_sips, self.package))
        except:
            features = None
        per_process_args = []
        for dirpath, dirnames, filenames in os.walk(self.input_sips):
            #
            # Use sorted walks.
            #
            dirnames.sort(key=FILE_SORT_KEY)
            filenames.sort(key=FILE_SORT_KEY)
            for filename in filenames:
                if filename != os.path.basename(dirpath) + MODULE_SIP:
                    continue
                sip_file = os.path.join(dirpath, filename)
                sip_file = sip_file[len(self.input_sips) + len(os.path.sep):]
                #
                # Was this file selected?
                #
                if not(selector.search(sip_file) and not omitter.search(sip_file)):
                    continue
                per_process_args.append((sip_file, ))
        std_args = (self.input_sips, self.includes, self.imports, self.libraries, self.package, self.output_so,
                    self.output_sips, self.tmp, self.sipconfig, self.pyqt_sip_flags, features, self.verbose)
        if jobs == 0:
            #
            # Debug mode.
            #
            results = [process_one(*(process_args + std_args)) for process_args in per_process_args]
        else:
            #
            # Parallel processing here...
            #
            tp = Pool(processes=jobs)
            results = [tp.apply_async(process_one, process_args + std_args) for process_args in per_process_args]
            tp.close()
            tp.join()
            #
            # Serial again.
            #
            results = [r.get() for r in results]
        results = {result[0]: result[1:] for result in results}
        failures = []
        for sip_file in sorted(results.keys(), key=FILE_SORT_KEY):
            e = results[sip_file][0]
            if e:
                failures.append((sip_file, e))
        return len(results), failures


def copy_file(input_dir, filename, output_dir):
    output = os.path.join(output_dir, filename)
    try:
        os.makedirs(os.path.dirname(output))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    input = os.path.join(input_dir, filename)
    shutil.copy(input, output)


def process_one(sip_file, input_sips, includes, imports, libraries, package, output_so, output_sips, tmp_dir,
                self_sipconfig, pyqt_sip_flags, features, verbose):
    """
    Run a SIP file.

    :param sip_file:            A SIP file name.
    :param input_sips:          Config
    :param includes:            Config
    :param imports:             Config
    :param libraries:           Config
    :param package:             Config
    :param output_so:           Config
    :param output_sips:         Config
    :param tmp_dir:             Config
    :param self_sipconfig:      Config
    :param pyqt_sip_flags:      Config
    :param features:            Is there a features file?
    :param verbose:             Config
    :return:                    (
                                    sip_file,
                                    error,
                                )
    """
    #
    # Make sure any errors mention the file that was being processed.
    #
    try:
        #
        # Read the supplied SIP module for the module name and the included modules.
        #
        feature = feature_for_sip_module(sip_file)
        match_re = re.compile("%Module(\s+|\s*\(\s*name\s*=\s*)(?P<name>[^\s,)]+).*")
        include_re = re.compile("%Include(\s+|\s*\(\s*name\s*=\s*)(?P<name>[^\s,)]+).*")
        module_name = None
        included_modules = []
        with open(os.path.join(input_sips, sip_file), "rU") as i:
            for line in i:
                m = match_re.match(line)
                if m:
                    module_name = m.group("name")
                else:
                    m = include_re.match(line)
                    if m:
                        assert module_name, _("%Include not preceeded by %Module")
                        included_modules.append(m.group("name"))
        assert module_name, _("No %Module found")
        #
        # Set up the module output directory.
        #
        module_path = module_name.replace(".", os.path.sep)
        tmp_dir = os.path.join(tmp_dir, module_path)
        output_so = os.path.join(output_so, os.path.dirname(module_path))
        assert module_name.startswith(package + "."),_("Expected {} to be part of {}").format(module_name, package)
        output_sips = os.path.join(output_sips, package)
        for dir in [tmp_dir, output_so, output_sips]:
            try:
                os.makedirs(dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        #
        # Create the set of output SIP files:
        #
        #   - The original SIP module.
        #   - Any %Included SIP modules.
        #   - Optionally, write a version of the supplied SIP module with feature support included.
        #
        copy_file(input_sips, sip_file, output_sips)
        for i in included_modules:
            copy_file(input_sips, i, output_sips)
        if features:
            source = os.path.join(output_sips, os.path.splitext(sip_file)[0] + ".with_features.sip")
            with open(source, "w") as o:
                #
                # Suppress the feature that corresponds to the SIP file being processed to avoid feeding SIP
                # %Import clauses which recursively refer to module beng processed. we do this by cloaking each
                # in a %Feature, and then disabling the one for "this".
                #
                # To avoid defining the %Feature multiple time, we put them inline in the temporary module.
                #
                o.write("// Run SIP with '-x {}' to prevent recursive definitions.\n".format(feature))
                o.write("%Include(name={})\n".format(features))
                o.write("%Include(name={})\n".format(os.path.basename(sip_file)))
        else:
            source = os.path.join(output_sips, sip_file)
        #
        # Run the SIP compiler. Use the -X option to extract all include paths actually used by the compiler.
        #
        build_file = os.path.join(tmp_dir, "module.sbf")
        make_file = os.path.join(tmp_dir, "module.Makefile")
        module_includes = os.path.join(tmp_dir, "module.includes")
        logger.info(_("Compiling {}").format(source))
        cmd = [self_sipconfig.sip_bin, "-c", tmp_dir, "-b", build_file, "-e", "-o", "-w", "-X",
               INCLUDES_EXTRACT + ":" + module_includes]
        if features:
            cmd += ["-x", feature]
        cmd += pyqt_sip_flags + ["-I" + i for i in imports + [input_sips]] + [source]
        _run_command(verbose, cmd)
        #
        # Create the Makefile.
        #
        parsed_includes = open(module_includes, "rU").read().split("\n")
        parsed_includes = [i for i in parsed_includes if i]
        includes = parsed_includes + includes
        self_sipconfig._macros["INCDIR"] = " ".join(includes)
        makefile = sipconfig.SIPModuleMakefile(self_sipconfig, build_file, makefile=make_file)
        #
        # Link against the user-specified libraries. Typically, any one module won't need them all, but this
        # is better than having to specify them by hand.
        #
        makefile.extra_libs = libraries
        makefile.generate()
        #
        # Compile and publish the module.
        # TODO: The hardcoded ".so" is not portable.
        #
        _run_command(verbose, ["make", "-f", os.path.basename(make_file)], cwd=tmp_dir)
        cpython_module = os.path.basename(module_path) + ".so"
        logger.info(_("Publishing {}").format(module_name))
        copy_file(tmp_dir, cpython_module, output_so)
        with open(os.path.join(output_so, "__init__.py"), "w") as f:
            pass
    except Exception as e:
        logger.error("{} while processing {}".format(e, sip_file))
        #
        # Tracebacks cannot be pickled for use by multiprocessing.
        #
        e = (e.__class__, str(e), traceback.format_exc())
        return sip_file, e
    return sip_file, None


def _run_command(verbose, cmd, *args, **kwds):
    if verbose:
        logger.info(" ".join(cmd))
    sub = subprocess.Popen(cmd, *args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwds)
    stdout, stderr = sub.communicate()
    stdout = stdout.strip()
    if sub.returncode:
        raise RuntimeError(stdout)
    if verbose and stdout:
        print(stdout)


def main(argv=None):
    """
    Run the SIP compiler, and the "make" the generated code. By default, all
    the modules specified in the rules file will be processed. The set of files
    can be restricted using the --select option, or a single standalone file
    specified using the "@" prefix to the --select option.

    The standalone mode also bypasses all of the special processing associated
    with the bulk processing of modules (see README) because it is assumed the
    user knows best.

    Examples:

        sip_compiler.py --select KDBusAddons sip
        sip_compiler.py sip 
    """
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(epilog=inspect.getdoc(main),
                                     formatter_class=HelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help=_("Enable verbose output"))
    parser.add_argument("--includes", default=PYKF5_INCLUDES + ",/usr/include/x86_64-linux-gnu/qt5/QtWidgets",
                        help=_("Comma-separated C++ header directories for includes"))
    parser.add_argument("--libraries", default=PYKF5_LIBRARIES,
                        help=_("Comma-separated globs of libraries for linking"))
    parser.add_argument("--imports", default=PYQT5_SIPS,
                        help=_("Comma-separated SIP module directories for imports"))
    parser.add_argument("--package", default=PYKF5_PACKAGE_NAME, help=_("Package name"))
    parser.add_argument("--project-rules", default=os.path.join(os.path.dirname(__file__), PYKF5_RULES),
                        help=_("Project rules"))
    parser.add_argument("--select", default=".*", type=lambda s: re.compile(s, re.I),
                        help=_("Regular expression of SIP modules under 'sips' to be processed"))
    parser.add_argument("--omit", default="<nothing>", type=lambda s: re.compile(s, re.I),
                        help=_("Regular expression of C++ headers under 'sips' NOT to be processed"))
    parser.add_argument("-j", "--jobs", type=int, default=multiprocessing.cpu_count(),
                        help=_("Number of parallel jobs, 0 for serial inline operation"))
    parser.add_argument("sips", help=_("SIP input directory to process"))
    parser.add_argument("output", help=_("Python and shippable SIP output directory"))
    try:
        args = parser.parse_args(argv[1:])
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        #
        # Compile!
        #
        sips = os.path.normpath(args.sips)
        includes = args.includes.lstrip().split(",")
        exploded_includes = args.includes.lstrip().split(",")
        for i in includes:
            for dirpath, dirnames, filenames in os.walk(i):
                for d in dirnames:
                    d = os.path.join(dirpath, d)
                    if d not in exploded_includes:
                        exploded_includes.append(d)
        rules = rules_engine.rules(args.project_rules)
        imports = args.imports.lstrip().split(",")
        libraries = args.libraries.lstrip().split(",")
        d = ModuleCompiler(args.package, args.output, rules, sips, includes, imports, libraries, args.verbose)
        attempts, failures = d.process_tree(args.jobs, args.select, args.omit)
        #
        # Dump a summary of what we did. Order the results by the name of the source.
        #
        for sip_file, e in failures:
            logger.info(_("Summary: {}: {} while processing {}").format(e[0].__name__, e[1], sip_file))
        level = logging.ERROR if failures else logging.INFO
        logger.log(level, _("Summary: {} processing errors for {} modules").format(len(failures), attempts))
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
