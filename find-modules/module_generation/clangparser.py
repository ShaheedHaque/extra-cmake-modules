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
        # If this is an array, the container is templated.
        #
        self.template_parameters = None
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
            if not found_start or not found_end:
                #
                # Clang tokens did not help. Try looking in the source code.
                #
                text = self.translation_unit.source_processor.preprocessed(container.extent,
                                                                           container.extent.start.file.name)
                found = text.find(container.spelling)
                if found != -1:
                    text = text[:found].strip()
                    if text.endswith("struct"):
                        self.initial_access_specifier = "public: // Was struct"
                else:
                    #
                    # The worst case is that the user has to write a rule to fix this.
                    #
                    logger.debug(_("Unable to expand {}".format(container.spelling)))

    @property
    def SIP_TYPE_NAME(self):
        return "namespace" if self.kind == CursorKind.NAMESPACE else "class"


class Enum(Container):
    CURSOR_KINDS = [CursorKind.ENUM_DECL]
    SIP_TYPE_NAME = "enum"
    GENERATED_NAME_FMT = "__enum{}"

    @property
    def spelling(self):
        return self.proxied_object.spelling or self.proxied_object.displayname or \
               self.GENERATED_NAME_FMT.format(self.extent.start.line)


class Function(Cursor):
    PROXIES = (
        clang.cindex.Cursor,
        [
            "get_arguments", "get_definition", "get_num_template_arguments", "get_template_argument_kind",
            "get_template_argument_type", "get_template_argument_unsigned_value", "get_template_argument_value",
            "is_const_method", "is_converting_constructor", "is_copy_constructor", "is_default_constructor",
            "is_default_method", "is_definition", "is_move_constructor", "is_pure_virtual_method", "is_static_method",
            "is_virtual_method", "result_type",
        ]
    )
    CURSOR_KINDS = [CursorKind.CXX_METHOD, CursorKind.FUNCTION_DECL, CursorKind.FUNCTION_TEMPLATE,
                    CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR, CursorKind.CONVERSION_FUNCTION]

    def __init__(self, fn):
        super(Function, self).__init__(fn)
        #
        # If this is an array, the function is templated.
        #
        self.template_parameters = None

    def is_implementation(self, container):
        """
        Is implementation of function previously declared in a class/struct.

        :param container:           The current container, which is not
                                    necessarily the semantic_parent; it is this
                                    distinction which matters.
        """
        return self.proxied_object.is_definition() and \
            container.kind in [CursorKind.TRANSLATION_UNIT, CursorKind.NAMESPACE] and \
                self.semantic_parent.kind in [CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]


class TemplateParameter(Cursor):
    CURSOR_KINDS = [CursorKind.TEMPLATE_TYPE_PARAMETER, CursorKind.TEMPLATE_NON_TYPE_PARAMETER,
                    CursorKind.TEMPLATE_TEMPLATE_PARAMETER]
    PROXIES = (
        clang.cindex.Cursor,
        [
            "type",
        ]
    )

    @property
    def SIP_TYPE_NAME(self):
        if self.kind == CursorKind.TEMPLATE_TYPE_PARAMETER:
            #
            # "typename " + self.spelling
            #
            return self.spelling
        elif self.kind == CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
            #
            # self.type.spelling + " " + self.spelling
            #
            return self.spelling
        elif self.kind == CursorKind.TEMPLATE_TEMPLATE_PARAMETER:
            #
            # Recursive template template parameter walk...
            #
            # template<...> class foo
            #
            parameter = []
            for member in self.get_children():
                parameter.append(member.SIP_TYPE_NAME)
            return "template<" + (", ".join(parameter)) + "> class " + self.spelling

    @property
    def spelling(self):
        location = self.proxied_object.location
        return self.proxied_object.spelling or "__{}_{}".format(location.line, location.column)


class Struct(Enum):
    CURSOR_KINDS = [CursorKind.STRUCT_DECL]
    SIP_TYPE_NAME = "struct"
    GENERATED_NAME_FMT = "__struct{}"


class Union(Enum):
    CURSOR_KINDS = [CursorKind.UNION_DECL]
    #
    # Render a union as a struct. From the point of view of the accessors created for the bindings,
    # this should behave as expected!
    #
    SIP_TYPE_NAME = "/* union */ struct"
    GENERATED_NAME_FMT = "__union{}"


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
