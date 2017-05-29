#
# Copyright 2017 by Shaheed Haque (srhaque@theiet.org)
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
from __future__ import print_function
import os
import re
import shutil
import tempfile

import module_compiler
import module_generator

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
TMP_DIR = None
BUILD_DIR = None
COMPILE_DIR = None


class Test:
    @classmethod
    def setup_class(cls):
        global TMP_DIR
        TMP_DIR = tempfile.mkdtemp()
        global BUILD_DIR
        BUILD_DIR = os.path.join(TMP_DIR, "tmp")
        global COMPILE_DIR
        COMPILE_DIR = os.path.join(TMP_DIR, "tmp2")
        print("TMP_DIR = " + TMP_DIR)

    @classmethod
    def teardown_class(cls):
        pass#shutil.rmtree(TMP_DIR)

    def test_00_generate(self):
        """
        test_00_generate: Generate module.
        """
        rules_pkg = os.path.join(SCRIPT_DIR, "Rules")
        d = module_generator.ModuleGenerator(rules_pkg, BUILD_DIR)
        omit = re.compile("=Nothing=", re.I)
        select = re.compile(".*", re.I)
        attempts, failures, directories = d.process_tree(jobs=0, selector=select, omitter=omit)
        print("Summary: {} processing errors for {} files in {} modules".format(len(failures), attempts, directories))
        assert len(failures) == 0

    def test_10_compile(self):
        """
        test_10_compile: Compile module.
        """
        rules_pkg = os.path.join(SCRIPT_DIR, "Rules")
        d = module_compiler.ModuleCompiler(rules_pkg, True, BUILD_DIR, COMPILE_DIR)
        omit = re.compile("=Nothing=", re.I)
        select = re.compile(".*", re.I)
        attempts, failures = d.process_tree(jobs=0, selector=select, omitter=omit)
        print("Summary: {} processing errors for {} modules".format(len(failures), attempts))
        assert len(failures) == 0
