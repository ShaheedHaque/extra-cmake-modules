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
"""
SIP binding code for std'n'boost-template classes. The main content is:

    - FunctionDb, ParameterDb and TypeCodeDb-compatible entries usable in
      RuleSets (e.g. list_{fn_result,parameter,typecode}).

    - PointerExpander class which implements shared_ptr templates.

This is supported by other public methods and classes which can be used as
examples and/or helper code.
"""
import gettext
import logging
import os
import re

import builtin_rules
from builtin_rules import HeldAs
from clangcparser import TypeKind
import templates.mappedtype
import templates.methodcode

gettext.install(os.path.basename(__file__))
logger = logging.getLogger(__name__)

# Keep PyCharm happy.
_ = _

TYPE = "type"
ARGS = "args"
KNOWN_PTRS = "(?P<" + TYPE + ">(boost::shared_ptr|std::auto_ptr))"
RE_KNOWN_PTRS = re.compile("(const )?" + KNOWN_PTRS + "<(?P<" + ARGS + ">.*)>( [&*])?")

RE_LIST_T = "(const )?(std::vector)<(.*)>( [&*])?"
RE_PTRS_T = "(const )?" + KNOWN_PTRS + "<(.*)>( [&*])?"

RE_LIST_V = RE_LIST_T + ".*"
RE_PTRS_V = RE_PTRS_T + ".*"

RE_UNTEMPLATED_FN = ".*[^>]"


class DictHelperKey(templates.mappedtype.GenerateMappedHelper):
    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po):
        cxx_i += ".key()"
        cxx_po += ".key()"
        return super(DictHelperKey, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def py_to_cxx(self, name, needs_reference, py_v):
        return super(DictHelperKey, self).py_to_cxx(name, needs_reference, py_v)


class DictHelperValue(templates.mappedtype.GenerateMappedHelper):
    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po):
        cxx_i += ".value()"
        cxx_po += ".value()"
        return super(DictHelperValue, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def py_to_cxx(self, name, needs_reference, py_v):
        return super(DictHelperValue, self).py_to_cxx(name, needs_reference, py_v)


class ListHelperValue(templates.mappedtype.GenerateMappedHelper):
    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po):
        cxx_i += "->at(i)"
        cxx_po += "->at(i)"
        return super(ListHelperValue, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def py_to_cxx(self, name, needs_reference, py_v):
        return super(ListHelperValue, self).py_to_cxx(name, needs_reference, py_v)


class SetHelperValue(templates.mappedtype.GenerateMappedHelper):
    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po):
        cxx_i = "*" + cxx_i
        cxx_po = "*" + cxx_po
        return super(SetHelperValue, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def py_to_cxx(self, name, needs_reference, py_v):
        return super(SetHelperValue, self).py_to_cxx(name, needs_reference, py_v)


class FunctionParameterHelper(templates.methodcode.FunctionParameterHelper):
    """
    Automatic handling for templated function parameter types with auto-unwrapping
    of KNOWN_PTRS.
    """
    def __init__(self, cxx_t, clang_t, manual_t=None):
        is_pointer = RE_KNOWN_PTRS.match(cxx_t)
        if is_pointer:
            template_type = is_pointer.group(TYPE)
            template_args = [is_pointer.group(ARGS)]
            cxx_t = template_args[0] + " *"
        super(FunctionParameterHelper, self).__init__(cxx_t, clang_t, manual_t)
        self.is_pointer = is_pointer

    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        if self.is_pointer:
            cxx_i += ".get()"
        return super(FunctionParameterHelper, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def cxx_to_cxx(self, aN, original_type, is_out_paramter):
        if self.is_pointer:
            code = """    typedef """ + HeldAs.base_type(original_type) + """ Cxx{aN}T;
    Cxx{aN}T *cxx{aN} = new Cxx{aN}T({aN});
"""
            code = code.replace("{aN}", aN, 4)
            #
            # A QWeakPointer has to be constructed via an intermediate QSharedPointer.
            #
            is_weakptr = re.match("(const )?QWeakPointer<(.*)>( .)?", original_type)
            if is_weakptr:
                code = code.replace("{aN}", "QSharedPointer<" + is_weakptr.group(2) + ">(" + aN + ")")
            else:
                code = code.replace("{aN}", aN)
            aN = "*cxx" + aN
            return code, aN
        return super(FunctionParameterHelper, self).cxx_to_cxx(aN, original_type, is_out_paramter)

    def py_parameter(self, type_, name, default, annotations):
        if self.is_pointer and default:
            #
            # TODO: We really just want default.data() as the default value, but SIP gets confused.
            #
            default = "NULL"
        return super(FunctionParameterHelper, self).py_parameter(type_, name, default, annotations)


class FunctionReturnHelper(templates.methodcode.FunctionReturnHelper):
    """
    Automatic handling for templated function return types with auto-unwrapping
    of KNOWN_PTRS templates.
    """
    def __init__(self, cxx_t, clang_t, manual_t=None):
        is_pointer = RE_KNOWN_PTRS.match(cxx_t)
        if is_pointer:
            template_type = is_pointer.group(TYPE)
            template_args = [is_pointer.group(ARGS)]
            cxx_t = template_args[0] + " *"
        super(FunctionReturnHelper, self).__init__(cxx_t, clang_t, manual_t)
        self.is_pointer = is_pointer

    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        if self.is_pointer:
            cxx_i += ".get()"
        return super(FunctionReturnHelper, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def py_fn_result(self, is_constructor):
        if self.is_pointer:
            return self.cxx_t
        return super(FunctionReturnHelper, self).py_fn_result(is_constructor)


class ListExpander(templates.mappedtype.ListExpander):

    def __init__(self, value_helper=ListHelperValue):
        super(ListExpander, self).__init__(value_helper)

    def header_for(self, template_t):
        """
        There is no simple algorithmic way to map template_t to a header file.
        """
        headers = {
            "std::vector": "vector",
        }
        return headers[template_t]

    def parse_template(self, template, expected):
        """
        std::vector takes a second argument, which is the allocator.
        """
        return super(ListExpander, self).parse_template(template, expected + 1)


class PointerExpander(templates.mappedtype.AbstractExpander):

    def __init__(self):
        super(PointerExpander, self).__init__([("value", PointerHelperValue)])

    def expand_generic(self, template_t, entries):
        """
        Generic support for template pointer types. The template parameter can
        be of any integral (int, long, enum) type or non-integral type, for
        example, QWeakPointer<int>.

        :param template_t:      The name of the C++ template, e.g. "QSharedDataPointer".
        :param entries:         Dictionary describing the C++ template. Expected keys:

                                    value           Is the value integral, pointer or object?
        """
        value_h = entries["value"]
        code = """
%TypeHeaderCode
#include <{header_h}>
%End
%ConvertFromTypeCode
"""
        code += value_h.declare_type_helpers("value", "return 0;")
        code += """
    // Convert the value from C++.
"""
        code += value_h.cxx_to_py("value", True, "sipCpp", "sipCpp")
        code += """    if (value == NULL) {
        PyErr_Format(PyExc_TypeError, "cannot convert value");
        return 0;
    }
    return value;
%End
%ConvertToTypeCode
"""
        code += value_h.declare_type_helpers("value", "return 0;", need_string=value_h.category != HeldAs.INTEGER)
        code += """    PyObject *value;

    // Convert the value to C++.
    value = sipPy;
"""
        code += value_h.py_to_cxx("value", True, "value")
        code += """
    if (*sipIsErr) {
"""
        if value_h.category != HeldAs.INTEGER:
            code += """        if (cxxvalue == NULL) {
            PyErr_Format(PyExc_TypeError, "value has type '%s' but '%s' is expected",
                         Py_TYPE(value)->tp_name, cxxvalueS);
        }
"""
        code += value_h.release_sip_helper("value")
        code += """        return 0;
    }
"""
        code += value_h.release_sip_helper("value")
        code += """    *sipCppPtr = new {template_t}<CxxvalueT>(cxxvalue);
"""
        code += """    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{header_h}", self.header_for(template_t), 1)
        code = code.replace("{template_t}", template_t)
        code = code.replace("{sip_t}", value_h.sip_t)
        return code

    def header_for(self, template_t):
        """
        There is no simple algorithmic way to map template_t to a header file.
        """
        headers = {
            "std::auto_ptr": "memory",
            "boost::shared_ptr": os.path.join("boost", "shared_ptr.hpp"),
        }
        return headers[template_t]


class PointerHelperValue(templates.mappedtype.GenerateMappedHelper):
    def cxx_to_py_template(self):
        return """    Cxx{name}T *cxx{name} = {cxx_po};
    PyObject *{name} = sipConvertFromType((void *)cxx{name}, gen{name}T, sipTransferObj);
"""

    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po):
        cxx_i += "->get()"
        cxx_po += "->get()"
        return super(PointerHelperValue, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def py_to_cxx(self, name, needs_reference, py_v):
        return super(PointerHelperValue, self).py_to_cxx(name, needs_reference, py_v)


def function_uses_templates(container, fn, sip, rule):
    """
    A FunctionDb-compatible function used to create %MethodCode expansions
    for C++ functions with templated return types and/or parameters.
    """
    sip.setdefault("parameter_helper", FunctionParameterHelper)
    sip.setdefault("return_helper", FunctionReturnHelper)
    builtin_rules.function_uses_templates(container, fn, sip, rule)


def list_fn_result(container, fn, sip, rule):
    """
    A FunctionDb-compatible function used to create a %MappedType for C++
    types with one template argument into Python lists.

    A call to function_uses_templates handles the %MethodCode expansion.
    """
    template = ListExpander()
    template.expand(rule, fn, sip["fn_result"], sip)
    function_uses_templates(container, fn, sip, rule)


def list_parameter(container, fn, parameter, sip, rule):
    """
    A ParameterDb-compatible function used to create a %MappedType for C++
    types with one template argument into Python lists.
    """
    template = ListExpander()
    template.expand(rule, parameter, sip["decl"], sip)


def list_typecode(container, typedef, sip, rule):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for C++
    types with one template argument into Python lists.
    """
    template = ListExpander()
    template.expand(rule, typedef, sip["decl"], sip)


def pointer_fn_result(container, fn, sip, rule):
    """
    A FunctionDb-compatible function used to create a %MappedType for a
    boost pointer type.

    A call to function_uses_templates handles the %MethodCode expansion.
    """
    template = PointerExpander()
    template.expand(rule, fn, sip["fn_result"], sip)
    function_uses_templates(container, fn, sip, rule)


def pointer_parameter(container, fn, parameter, sip, rule):
    """
    A ParameterDb-compatible function used to create a %MappedType for a
    boost pointer type.
    """
    template = PointerExpander()
    template.expand(rule, parameter, sip["decl"], sip)


def pointer_typecode(container, typedef, sip, rule):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for a
    boost pointer type.
    """
    template = PointerExpander()
    if typedef.underlying_type.kind == TypeKind.ELABORATED:
        #
        # This is a typedef of a typedef, and Clang gets the template
        # parameters wrong, so abort.
        #
        return
    assert typedef.underlying_type.kind == TypeKind.UNEXPOSED
    template.expand(rule, typedef, sip["decl"], sip)


def function_rules():
    return [
        #
        # Supplement std'n'boost templates with %MappedTypes for the function
        # result, and call function_uses_templates for %MethodCode too.
        #
        [".*", RE_UNTEMPLATED_FN, "", RE_LIST_V, ".*", list_fn_result],
        [".*", RE_UNTEMPLATED_FN, "", RE_PTRS_V, ".*", pointer_fn_result],
        #
        # Call function_uses_templates...the parameters have been dealt with elsewhere.
        #
        [".*", RE_UNTEMPLATED_FN, "", ".*", RE_LIST_V, function_uses_templates],
        [".*", RE_UNTEMPLATED_FN, "", ".*", RE_PTRS_V, function_uses_templates],
    ]


def parameter_rules():
    return [
        #
        # Supplement std'n'boost templates with %MappedTypes.
        #
        [".*", RE_UNTEMPLATED_FN, ".*", RE_LIST_V, ".*", list_parameter],
        [".*", RE_UNTEMPLATED_FN, ".*", RE_PTRS_V, ".*", pointer_parameter],
    ]


def typedef_rules():
    return [
        #
        # Supplement std'n'boost templates with %MappedTypes.
        #
        [".*", ".*", ".*", RE_LIST_T, list_typecode],
        [".*", ".*", ".*", RE_PTRS_T, pointer_typecode],
    ]
