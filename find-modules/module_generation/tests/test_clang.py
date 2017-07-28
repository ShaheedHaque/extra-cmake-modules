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

import clangcplus


class Test:
    def test_custom_parser(self):
        """
        test_custom_parser: Generate custom parser.
        """
        class MyCursor(clangcplus.Cursor):
            CLASS_MAP = {}

        class MyTranslationUnitCursor(clangcplus.TranslationUnitCursor, MyCursor):
            pass

        class MyStruct(MyCursor):
            CURSOR_KINDS = [clangcplus.CursorKind.STRUCT_DECL]

            def __init__(self, container):
                proxy_attributes = []
                super(MyStruct, self).__init__(container, proxy_attributes)

        #
        # Ensure the base parser has not been affected.
        #
        self.test_base_parser()
        assert MyTranslationUnitCursor in MyCursor.CLASS_MAP.values()
        assert MyStruct in MyCursor.CLASS_MAP.values()
        assert MyTranslationUnitCursor in MyTranslationUnitCursor.CLASS_MAP.values()

    def test_base_parser(self):
        """
        test_base_parser: Test base parser.
        """
        assert clangcplus.TranslationUnitCursor in clangcplus.Cursor.CLASS_MAP.values()
        assert clangcplus.TranslationUnitCursor in clangcplus.TranslationUnitCursor.CLASS_MAP.values()
