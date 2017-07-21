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
import gettext
import logging

import clang.cindex

import clangcplus

logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _

CursorKind = clangcplus.CursorKind


class Cursor(clangcplus.Cursor):
    CLASS_MAP = {}


class Container(clangcplus.Container, Cursor):
    #
    # Our CURSOR_KINDS only adds templates.
    #
    TEMPLATE_CURSOR_KINDS = [CursorKind.CLASS_TEMPLATE, CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION]
    CURSOR_KINDS = clangcplus.Container.CURSOR_KINDS + TEMPLATE_CURSOR_KINDS

    def __init__(self, container):
        super(Container, self).__init__(container)
        #
        # Assume this is a class, not a struct.
        #
        self.initial_access_specifier = ""
        #
        # Find any template arguments. Remember that a template can have zero args!
        #
        self.template_args = None
        if container.kind in self.TEMPLATE_CURSOR_KINDS:
            self.template_args = []
            for child in container.get_children():
                try:
                    if child.kind in [CursorKind.TEMPLATE_TYPE_PARAMETER, CursorKind.TEMPLATE_NON_TYPE_PARAMETER]:
                        self.template_args.append(child)
                    else:
                        break
                except ValueError as e:
                    #
                    # Some kinds result in a Clang error.
                    #
                    logger.debug(_("Unknown _kind_id {} for {}".format(e, child.spelling)))
            #
            # Clang presents a templated struct as a CLASS_TEMPLATE, but does not
            # insert an initial "public" access specifier. Make a best-effort attempt
            # to find this (container.get_tokens() can be flummoxed by macros etc.).
            #
            found_start = False
            found_end = False
            bracket_level = 0
            for token in container.get_tokens():
                #
                # Now count balanced <> till we get to the end.
                #
                if bracket_level == 0 and found_start and token.kind == clang.cindex.TokenKind.KEYWORD:
                    found_end = True
                    if token.spelling == "struct":
                        self.initial_access_specifier = "public: // Was struct"
                    break
                elif token.spelling in "<":
                    found_start = True
                    bracket_level += 1
                elif token.spelling in ">":
                    bracket_level -= 1
            if found_start and not found_end:
                #
                # The worst case is that the user has to write a rule to fix this.
                #
                logger.debug(_("Start but no end found for {}".format(container.spelling)))

    @property
    def SIP_TYPE_NAME(self):
        return "namespace" if self.kind == CursorKind.NAMESPACE else "class"


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


class Function(clangcplus.Function, Cursor):
    pass


class TranslationUnit(clangcplus.TranslationUnit, Cursor):
    pass


class Typedef(Cursor):
    PROXIES = (
        clang.cindex.Cursor,
        [
            "type", "result_type", "underlying_typedef_type",
        ]
    )
    CURSOR_KINDS = [CursorKind.TYPEDEF_DECL]
