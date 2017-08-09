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
import re

import clang.cindex
from clang.cindex import Type as _Type

import clangcplus

logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _

CursorKind = clangcplus.CursorKind
TypeKind = clangcplus.TypeKind


class Cursor(clangcplus.Cursor):
    CLASS_MAP = {}

    def get_children(self):
        """
        Get the children of this Cursor either as Cursors, or as clang.cindex.Cursor.
        """
        template_parameter_number = -1
        parameter_number = -1
        for child in self.proxied_object.get_children():
            try:
                kind = child.kind
            except ValueError as e:
                #
                # TODO: Some kinds result in a Clang error.
                #
                logger.debug(_("Unknown _kind_id {} for {}".format(e, child.spelling or child.displayname)))
            else:
                if kind in ParameterCursor.CURSOR_KINDS:
                    parameter_number += 1
                    yield ParameterCursor(child, parameter_number)
                elif kind in TemplateParameterCursor.CURSOR_KINDS:
                    template_parameter_number += 1
                    yield TemplateParameterCursor(child, template_parameter_number)
                else:
                    yield self._wrapped(child)


class ContainerCursor(clangcplus.ContainerCursor, Cursor):
    #
    # Our CURSOR_KINDS only adds templates.
    #
    TEMPLATE_CURSOR_KINDS = [CursorKind.CLASS_TEMPLATE, CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION]
    CURSOR_KINDS = clangcplus.ContainerCursor.CURSOR_KINDS + TEMPLATE_CURSOR_KINDS

    def __init__(self, container):
        super(ContainerCursor, self).__init__(container)
        #
        # If this is an array, the container is templated.
        #
        self.template_parameters = None
        #
        # Assume this is a class, not a struct.
        #
        self.initial_access_specifier = ""
        if container.kind in self.TEMPLATE_CURSOR_KINDS:
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


class EnumCursor(ContainerCursor):
    CURSOR_KINDS = [CursorKind.ENUM_DECL]
    SIP_TYPE_NAME = "enum"
    GENERATED_NAME_FMT = "__enum{}"
    PROXIES = (
        clang.cindex.Cursor,
        [
            "type"
        ]
    )

    @property
    def spelling(self):
        return self.proxied_object.spelling or self.proxied_object.displayname or \
               self.GENERATED_NAME_FMT.format(self.extent.start.line)


class FunctionCursor(Cursor):
    PROXIES = (
        clang.cindex.Cursor,
        [
            "get_arguments", "get_definition", "get_num_template_arguments", "get_template_argument_kind",
            "get_template_argument_type", "get_template_argument_unsigned_value", "get_template_argument_value",
            "is_const_method", "is_converting_constructor", "is_copy_constructor", "is_default_constructor",
            "is_default_method", "is_definition", "is_move_constructor", "is_pure_virtual_method", "is_static_method",
            "is_virtual_method",
        ]
    )
    CURSOR_KINDS = [CursorKind.CXX_METHOD, CursorKind.FUNCTION_DECL, CursorKind.FUNCTION_TEMPLATE,
                    CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR, CursorKind.CONVERSION_FUNCTION]

    def __init__(self, fn):
        super(FunctionCursor, self).__init__(fn)
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

    @property
    def result_type(self):
        return Type._wrapped(self.proxied_object.result_type)

    @property
    def SIP_RESULT_TYPE(self):
        if self.kind in [CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR]:
            decl = ""
        else:
            the_type = self.result_type.get_canonical()
            if isinstance(the_type, FunctionType):
                decl = self.result_type.spelling
            else:
                decl = the_type.spelling
        return decl


class ParameterCursor(Cursor):
    CURSOR_KINDS = [CursorKind.PARM_DECL]

    def __init__(self, parameter, parameter_number):
        super(ParameterCursor, self).__init__(parameter)
        self.parameter_number = parameter_number

    @property
    def spelling(self):
        return self.proxied_object.spelling or "__{}".format(self.parameter_number)

    @property
    def type(self):
        return Type._wrapped(self.proxied_object.type)

    @property
    def SIP_TYPE_NAME(self):
        the_type = self.type.get_canonical()
        type_spelling = the_type.spelling
        #
        # Get rid of any pointer const-ness and add a pointer suffix. Not removing the const-ness causes
        # SIP to generate sequences which the C++ compiler seems to optimise away:
        #
        #   QObject* const a1 = 0;
        #
        #   if (sipParseArgs(..., &a1))
        #
        if isinstance(the_type.get_canonical(), FunctionType):
            #
            # SIP does not generally like function pointers. Here the problem
            # is that parameters just don't support canonical function pointers
            # with default values, so use the typedef if one is known. Else,
            # rules are needed to fix them up.
            #
            if self.type.spelling.find("(") == -1:
                decl = self.type.spelling
                if decl[-1] not in "*&":
                    decl += " "
                decl = decl + self.spelling
            else:
                decl = the_type.get_canonical().fmt_declaration(self.spelling)
        elif the_type.kind == TypeKind.INCOMPLETEARRAY:
            #
            # Clang makes "const int []" into "int const[]"!!!
            #
            if " const[" in type_spelling:
                type_spelling = "const " + type_spelling.replace(" const[", " [", 1)
            decl = type_spelling.replace("[", self.spelling + "[", 1)
        else:
            decl = "{} {}".format(type_spelling, self.spelling)
            decl = decl.replace("* ", "*").replace("& ", "&")
        return decl


class TemplateParameterCursor(Cursor):
    CURSOR_KINDS = [CursorKind.TEMPLATE_TYPE_PARAMETER, CursorKind.TEMPLATE_NON_TYPE_PARAMETER,
                    CursorKind.TEMPLATE_TEMPLATE_PARAMETER]

    def __init__(self, parameter, parameter_number):
        super(TemplateParameterCursor, self).__init__(parameter)
        self.parameter_number = parameter_number

    @property
    def spelling(self):
        return self.proxied_object.spelling or "__{}".format(self.parameter_number)

    @property
    def type(self):
        return Type._wrapped(self.proxied_object.type)

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
            parameter = [c.SIP_TYPE_NAME for c in self.get_children()]
            return "template<" + (", ".join(parameter)) + "> class " + self.spelling


class StructCursor(EnumCursor):
    CURSOR_KINDS = [CursorKind.STRUCT_DECL]
    SIP_TYPE_NAME = "struct"
    GENERATED_NAME_FMT = "__struct{}"


class UnionCursor(EnumCursor):
    CURSOR_KINDS = [CursorKind.UNION_DECL]
    #
    # Render a union as a struct. From the point of view of the accessors created for the bindings,
    # this should behave as expected!
    #
    SIP_TYPE_NAME = "/* union */ struct"
    GENERATED_NAME_FMT = "__union{}"


class TranslationUnitCursor(clangcplus.TranslationUnitCursor, Cursor):
    pass


class TypedefCursor(Cursor):
    CURSOR_KINDS = [CursorKind.TYPEDEF_DECL]

    @property
    def type(self):
        return Type._wrapped(self.proxied_object.type)

    @property
    def result_type(self):
        return Type._wrapped(self.proxied_object.result_type)

    @property
    def underlying_type(self):
        return Type._wrapped(self.proxied_object.underlying_typedef_type)

    @property
    def SIP_TYPE_NAME(self):
        the_type = self.underlying_type
        type_spelling = the_type.spelling
        if isinstance(the_type.get_canonical(), FunctionType):
            the_type = the_type.get_canonical()
            decl = the_type.fmt_args() or "void"
        elif the_type.kind == TypeKind.RECORD:
            decl = type_spelling
        elif the_type.kind == TypeKind.DEPENDENTSIZEDARRAY:
            #
            # Clang makes "QString foo[size]" into "QString [size]"!!!
            #
            decl = type_spelling.replace("[", self.spelling + "[", 1)
        else:
            decl = the_type.get_canonical().spelling
        return decl

    @property
    def SIP_RESULT_TYPE(self):
        the_type = self.underlying_type
        if isinstance(the_type.get_canonical(), FunctionType):
            the_type = the_type.get_canonical()
            result_type = the_type.fmt_result()
        else:
            result_type = ""
        return result_type


class VariableCursor(Cursor):
    PROXIES = (
        clang.cindex.Cursor,
        [
            "storage_class",
        ]
    )
    CURSOR_KINDS = [CursorKind.VAR_DECL, CursorKind.FIELD_DECL]

    @property
    def type(self):
        return Type._wrapped(self.proxied_object.type)


class Type(clangcplus.Type):
    pass


class ArrayType(Type):
    PROXIES = (
        clang.cindex.Type,
        [
            "element_type",
        ]
    )
    TYPE_KINDS = [TypeKind.CONSTANTARRAY, TypeKind.VARIABLEARRAY]

    def __init__(self, array, element_count=None):
        super(ArrayType, self).__init__(array)
        if self.kind == TypeKind.CONSTANTARRAY:
            self._element_count = self.proxied_object.element_count
        else:
            assert element_count is not None
            self._element_count = element_count

    @property
    def element_count(self):
        return self._element_count


class FunctionType(clangcplus.FunctionType, Type):
    def fmt_declaration(self, name, args=None):
        if args is None:
            args = self.fmt_args()
        name = self.fmt_name(name)
        result = self.fmt_result()
        if result[-1] not in "*&":
            result += " "
        return "{}({})({})".format(result, name, args)

    def fmt_args(self):
        args = [c.spelling for c in self.argument_types]
        return ", ".join(args)

    def fmt_name(self, name):
        clazz = self.is_member_of
        name = "{}::*{}".format(clazz.spelling, name) if clazz else name
        if self.is_pointer:
            name = "*" + name
        return name

    def fmt_result(self):
        return self.result_type.spelling


class IndirectType(Type):
    TYPE_KINDS = [TypeKind.ELABORATED, TypeKind.TYPEDEF, TypeKind.UNEXPOSED]

    @property
    def underlying_type(self):
        return Type._wrapped(self.proxied_object.get_canonical())

    def get_declaration(self):
        return Cursor._wrapped(self.proxied_object.get_declaration())


class PointerType(clangcplus.PointerType, Type):
    pass


class RecordType(Type):
    TYPE_KINDS = [TypeKind.RECORD]

    @property
    def spelling(self):
        decl = self.proxied_object.spelling
        if "(anonymous " in decl:
            #
            # The spelling will be of the form 'N::n::(anonymous union at /usr/include/KF5/kjs/bytecode/opargs.h:66:5)'
            #
            words = decl.split("(", 1)[1][:-1]
            words = re.split("[ :]", words)
            kind = {"enum": EnumCursor, "struct": StructCursor, "union": UnionCursor}[words[1]]
            decl = kind.SIP_TYPE_NAME + " __" + words[1] + words[-2]
        return decl
