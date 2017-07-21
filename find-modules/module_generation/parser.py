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

"""A Clang-C wrapper that irons out some of the idiosyncrasies of Clang-C."""

import clangcplus

CursorKind = clangcplus.CursorKind


class Cursor(clangcplus.Cursor):
    CLASS_MAP = {}


class Container(clangcplus.Container, Cursor):
    pass


class Enum(Cursor):
    CURSOR_KINDS = [CursorKind.ENUM_DECL]
    NAME_FMT = "enum {}"
    GENERATED_NAME_FMT = "__enum{}"

    @property
    def spelling(self):
        return self.proxied_object.spelling or self.proxied_object.displayname or \
               self.GENERATED_NAME_FMT.format(self.extent.start.line)


class Struct(Enum):
    CURSOR_KINDS = [CursorKind.STRUCT_DECL]
    NAME_FMT = "struct {}"
    GENERATED_NAME_FMT = "__struct{}"


class Union(Enum):
    CURSOR_KINDS = [CursorKind.UNION_DECL]
    NAME_FMT = "union {}"
    GENERATED_NAME_FMT = "__union{}"


class Function(Cursor):
    CURSOR_KINDS = [CursorKind.CXX_METHOD, CursorKind.FUNCTION_DECL, CursorKind.FUNCTION_TEMPLATE,
                    CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR, CursorKind.CONVERSION_FUNCTION]

    def __init__(self, fn):
        proxy_attributes = [
            "get_arguments", "get_definition", "get_num_template_arguments", "get_template_argument_kind",
            "get_template_argument_type", "get_template_argument_unsigned_value", "get_template_argument_value",
            "is_const_method", "is_converting_constructor", "is_copy_constructor", "is_default_constructor",
            "is_default_method", "is_definition", "is_move_constructor", "is_pure_virtual_method", "is_static_method",
            "is_virtual_method", "result_type",
        ]
        super(Function, self).__init__(fn, proxy_attributes)

    def is_copy_constructor(self):
        if self.kind != CursorKind.CONSTRUCTOR:
            return False
        num_params = 0
        has_self_type = False
        for child in self.get_children():
            num_params += 1
            if child.kind == CursorKind.PARM_DECL:
                param_type = child.type.spelling
                param_type = param_type.split("::")[-1]
                param_type = param_type.replace("const", "").replace("&", "").strip()
                has_self_type = param_type == self.semantic_parent.spelling
        return num_params == 1 and has_self_type


class TranslationUnit(clangcplus.TranslationUnit, Cursor):
    pass


class Typedef(Cursor):
    CURSOR_KINDS = [CursorKind.TYPEDEF_DECL]

    def __init__(self, typedef):
        proxy_attributes = ["type", "result_type", "underlying_typedef_type"]
        super(Typedef, self).__init__(typedef, proxy_attributes)
