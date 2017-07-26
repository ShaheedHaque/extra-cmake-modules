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
from clang.cindex import TypeKind

import clangcplus

logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _

CursorKind = clangcplus.CursorKind
#
# Function pointers are a tricky area. We need to detect them by text matching.
#
FUNC_PTR = "(*)"


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
                if kind in Parameter.CURSOR_KINDS:
                    parameter_number += 1
                    yield Parameter(child, parameter_number)
                elif kind in TemplateParameter.CURSOR_KINDS:
                    template_parameter_number += 1
                    yield TemplateParameter(child, template_parameter_number)
                else:
                    yield self._wrapped(child)


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
            self.template_args = [c for c in self.get_children() if isinstance(c, TemplateParameter)]
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

    @property
    def SIP_RESULT_TYPE(self):
        if self.kind in [CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR]:
            decl = ""
        else:
            decl = self.result_type.get_canonical().spelling
            #
            # If the result is a self pointer, the canonical spelling is likely to be
            # a problem for SIP. Working out if we have such a case seems hand: the approach
            # now is the following heuristic...
            #
            #   - We have a pointer AND
            #   - We see what looks like the thing Clang seems to use for a self pointer
            #
            if self.result_type.get_canonical().kind == TypeKind.POINTER and decl.find(FUNC_PTR) != -1:
                decl = self.result_type.spelling
            elif self.result_type.get_canonical().kind == TypeKind.MEMBERPOINTER:
                decl = self.result_type.spelling
        return decl


class Parameter(Cursor):
    CURSOR_KINDS = [CursorKind.PARM_DECL]
    PROXIES = (
        clang.cindex.Cursor,
        [
            "type",
        ]
    )

    def __init__(self, parameter, parameter_number):
        super(Parameter, self).__init__(parameter)
        self.parameter_number = parameter_number

    @property
    def spelling(self):
        return self.proxied_object.spelling or "__{}".format(self.parameter_number)

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
        if the_type.kind == TypeKind.POINTER:
            #
            # Except that function pointers need special consideration. See elsewhere too...
            #
            if type_spelling.find(FUNC_PTR) == -1:
                decl = "{} *{}".format(the_type.get_pointee().spelling, self.spelling)
            else:
                #
                # SIP gets confused if we have default values for a canonical function pointer, so use the
                # "higher" form if we have else, else just hope we don't have a default value.
                #
                if self.type.spelling.find("(") == -1:
                    decl = "{} {}".format(self.type.spelling, self.spelling)
                    decl = decl.replace("* ", "*").replace("& ", "&")
                else:
                    named_func_ptr = "(*{})".format(self.spelling)
                    decl = type_spelling.replace(FUNC_PTR, named_func_ptr, 1)
        elif the_type.kind == TypeKind.MEMBERPOINTER:
            func_ptr = "({}::*)".format(the_type.get_class_type().spelling)
            named_func_ptr = "({}::*{})".format(the_type.get_class_type().spelling, self.spelling)
            decl = type_spelling.replace(func_ptr, named_func_ptr, 1)
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


class TemplateParameter(Cursor):
    CURSOR_KINDS = [CursorKind.TEMPLATE_TYPE_PARAMETER, CursorKind.TEMPLATE_NON_TYPE_PARAMETER,
                    CursorKind.TEMPLATE_TEMPLATE_PARAMETER]
    PROXIES = (
        clang.cindex.Cursor,
        [
            "type",
        ]
    )

    def __init__(self, parameter, parameter_number):
        super(TemplateParameter, self).__init__(parameter)
        self.parameter_number = parameter_number

    @property
    def spelling(self):
        return self.proxied_object.spelling or "__{}".format(self.parameter_number)

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

    @property
    def SIP_TYPE_NAME(self):
        the_type = self.underlying_typedef_type
        if the_type.get_canonical().kind in [TypeKind.MEMBERPOINTER, TypeKind.FUNCTIONPROTO]:
            #
            # A function pointer!
            #
            args = [c.type.spelling for c in self.get_children() if isinstance(c, Parameter)]
            decl = ", ".join(args).replace("* ", "*").replace("& ", "&")
        elif the_type.kind == TypeKind.POINTER and the_type.spelling.find(FUNC_PTR) != -1:
            #
            # A function pointer!
            #
            decl = the_type.spelling.split(FUNC_PTR, 1)[1]
            decl = decl.strip()[1:-1]
        elif the_type.kind == TypeKind.RECORD:
            decl = self.underlying_typedef_type.spelling
        elif the_type.kind == TypeKind.DEPENDENTSIZEDARRAY:
            #
            # Clang makes "QString foo[size]" into "QString [size]"!!!
            #
            decl = self.underlying_typedef_type.spelling.replace("[", self.spelling + "[", 1)
        else:
            decl = self.underlying_typedef_type.get_canonical().spelling
        return decl

    @property
    def SIP_RESULT_TYPE(self):
        #
        # If the typedef is for a function pointer, the canonical spelling is likely to be
        # a problem for SIP. Working out if we have such a case seems hard: the approach
        # now is the following heuristic...
        #
        #   - We are not dealing with a TypeKind.MEMBERPOINTER (handled above) AND
        #   (
        #   - The self has a result OR
        #   - We found some arguments OR
        #   - We see what looks like the thing Clang seems to use for a function pointer
        #   )
        #
        the_type = self.underlying_typedef_type.get_canonical()
        if the_type.kind in [TypeKind.MEMBERPOINTER, TypeKind.FUNCTIONPROTO]:
            result_type = self.result_type.spelling
        elif the_type.kind == TypeKind.POINTER and the_type.spelling.find(FUNC_PTR) != -1:
            #
            # A function pointer!
            #
            result_type = the_type.spelling.split(FUNC_PTR, 1)[0]
            result_type = result_type.strip()
        else:
            result_type = ""
        return result_type
