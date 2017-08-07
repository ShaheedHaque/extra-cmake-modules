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
"""
SIP binding code for PyQt-template classes. The main content is:

    - FunctionDb, ParameterDb and TypeCodeDb-compatible entries usable in
      RuleSets (e.g. {dict, list, set}_{fn_result, parameter_typecode}).

    - {Pair,Pointer}Expander classes which implement corresponding templates.

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
from templates.expander import DictExpander, ListExpander, SetExpander, AbstractExpander

gettext.install(os.path.basename(__file__))
logger = logging.getLogger(__name__)

# Keep PyCharm happy.
_ = _

KNOWN_PTRS = "(QWeakPointer|Q(Explicitly|)Shared(Data|)Pointer)"
RE_KNOWN_PTRS = re.compile("(const )?" + KNOWN_PTRS + "<(.*)>( .)?")


class FunctionParameterHelper(builtin_rules.FunctionParameterHelper):
    """
    Automatic handling for templated function parameter types with auto-unwrapping
    of KNOWN_PTRS.
    """
    def __init__(self, cxx_t, clang_t, manual_t=None):
        is_qshared = RE_KNOWN_PTRS.match(cxx_t)
        if is_qshared:
            template_type = is_qshared.group(2)
            template_args = [is_qshared.group(5)]
            cxx_t = template_args[0] + " *"
        super(FunctionParameterHelper, self).__init__(cxx_t, clang_t, manual_t)
        self.is_qshared = is_qshared

    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        if self.is_qshared:
            cxx_i += ".data()"
        return super(FunctionParameterHelper, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def cxx_to_cxx(self, aN, original_type, is_out_paramter):
        if self.is_qshared:
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
        if self.is_qshared and default:
            #
            # TODO: We really just want default.data() as the default value, but SIP gets confused.
            #
            default = "NULL"
        return super(FunctionParameterHelper, self).py_parameter(type_, name, default, annotations)


class FunctionReturnHelper(builtin_rules.FunctionReturnHelper):
    """
    Automatic handling for templated function return types with auto-unwrapping
    of KNOWN_PTRS templates.
    """
    def __init__(self, cxx_t, clang_t, manual_t=None):
        is_qshared = RE_KNOWN_PTRS.match(cxx_t)
        if is_qshared:
            template_type = is_qshared.group(2)
            template_args = [is_qshared.group(5)]
            cxx_t = template_args[0] + " *"
        super(FunctionReturnHelper, self).__init__(cxx_t, clang_t, manual_t)
        self.is_qshared = is_qshared

    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        if self.is_qshared:
            cxx_i += ".data()"
        return super(FunctionReturnHelper, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def py_fn_result(self, is_constructor):
        if self.is_qshared:
            return self.cxx_t
        return super(FunctionReturnHelper, self).py_fn_result(is_constructor)


def function_uses_templates(container, fn, sip, rule):
    """
    A FunctionDb-compatible function used to create %MethodCode expansions
    for C++ functions with templated return types and/or parameters.
    """
    sip.setdefault("parameter_helper", FunctionParameterHelper)
    sip.setdefault("return_helper", FunctionReturnHelper)
    builtin_rules.function_uses_templates(container, fn, sip, rule)


def dict_fn_result(container, fn, sip, rule):
    """
    A FunctionDb-compatible function used to create a %MappedType for C++
    types with two template arguments into Python dicts.

    A call to function_uses_templates handles the %MethodCode expansion.
    """
    template = DictExpander()
    template.expand(rule, fn, sip["fn_result"], sip)
    function_uses_templates(container, fn, sip, rule)


def dict_parameter(container, fn, parameter, sip, rule):
    """
    A ParameterDb-compatible function used to create a %MappedType for C++
    types with two template arguments into Python dicts.
    """
    template = DictExpander()
    template.expand(rule, parameter, sip["decl"], sip)


def dict_typecode(container, typedef, sip, rule):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for C++
    types with two template arguments into Python dicts.
    """
    template = DictExpander()
    template.expand(rule, typedef, sip["decl"], sip)


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


def set_fn_result(container, fn, sip, rule):
    """
    A FunctionDb-compatible function used to create a %MappedType for C++
    types with one template argument into Python sets.

    A call to function_uses_templates handles the %MethodCode expansion.
    """
    template = SetExpander()
    template.expand(rule, fn, sip["fn_result"], sip)
    function_uses_templates(container, fn, sip, rule)


def set_parameter(container, fn, parameter, sip, rule):
    """
    A ParameterDb-compatible function used to create a %MappedType for C++
    types with one template argument into Python sets.
    """
    template = SetExpander()
    template.expand(rule, parameter, sip["decl"], sip)


def set_typecode(container, typedef, sip, rule):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for C++
    types with one template argument into Python sets.
    """
    template = SetExpander()
    template.expand(rule, typedef, sip["decl"], sip)


def pair_fn_result(container, fn, sip, rule):
    """
    A FunctionDb-compatible function used to create a %MappedType for a
    QPair<> (using a 2-tuple).

    A call to function_uses_templates handles the %MethodCode expansion.
    """
    template = PairExpander()
    template.expand(rule, fn, sip["fn_result"], sip)
    function_uses_templates(container, fn, sip, rule)


def pair_parameter(container, fn, parameter, sip, rule):
    """
    A ParameterDb-compatible function used to create a %MappedType for a
    QPair<> (using a 2-tuple).
    """
    handler = PairExpander()
    handler.expand(rule, parameter, sip["decl"], sip)


def pair_typecode(container, typedef, sip, rule):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for a
    QPair<> (using a 2-tuple).
    """
    template = PairExpander()
    template.expand(rule, typedef, sip["decl"], sip)


def pointer_fn_result(container, fn, sip, rule):
    """
    A FunctionDb-compatible function used to create a %MappedType for a
    Qt pointer type.

    A call to function_uses_templates handles the %MethodCode expansion.
    """
    template = PointerExpander()
    template.expand(rule, fn, sip["fn_result"], sip)
    function_uses_templates(container, fn, sip, rule)


def pointer_parameter(container, fn, parameter, sip, rule):
    """
    A ParameterDb-compatible function used to create a %MappedType for a
    Qt pointer type.
    """
    handler = PointerExpander()
    handler.expand(rule, parameter, sip["decl"], sip)


def pointer_typecode(container, typedef, sip, rule):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for a
    Qt pointer type.
    """
    handler = PointerExpander()
    if typedef.underlying_type.kind == TypeKind.ELABORATED:
        #
        # This is a typedef of a typedef, and Clang gets the template
        # parameters wrong, so abort.
        #
        return
    assert typedef.underlying_type.kind == TypeKind.UNEXPOSED
    handler.expand(rule, typedef, sip["decl"], sip)


class PairExpander(AbstractExpander):

    def __init__(self):
        super(PairExpander, self).__init__(["first", "second"])

    def expand_generic(self, qt_type, entries):
        """
        Generic support for QPair types which are mapped onto a Python tuple. Either
        template parameter can be of any integral (int, long, enum) type or
        non-integral type, for example, QPair<int, QString>.

        :param qt_type:         The name of the Qt template, e.g. "QPair".
        :param entries:         Dictionary describing the C++ template. Expected keys:

                                    first           Is the value integral, pointer or object?
                                    second          Is the value integral, pointer or object?
        """
        first_h = entries["first"]
        second_h = entries["second"]
        code = """
%TypeHeaderCode
#include <{qt_type}>
%End
%ConvertFromTypeCode
"""
        code += first_h.declare_type_helpers("first", "return 0;")
        code += second_h.declare_type_helpers("second", "return 0;")
        code += """
    // Create the tuple
    PyObject *tuple = NULL;
    {
"""
        code += first_h.cxx_to_py("first", True, "sipCpp->first")
        code += second_h.cxx_to_py("second", True, "sipCpp->second")
        code += """        tuple = (first && second) ? PyTuple_Pack(2, first, second) : NULL;
"""
        #
        # Error handling assumptions:
        #
        #   - a failed "new" throws (or, not compliant, return NULL).
        #   - the good path should be as fast as possible, error recovery can be slow.
        #
        code += """
        if (first == NULL || second == NULL || tuple == NULL) {
            PyErr_Format(PyExc_TypeError, "cannot combine first/second as tuple");
"""
        code += first_h.decrement_python_reference("first") + second_h.decrement_python_reference("second")
        if first_h.category == HeldAs.OBJECT:
            code += """            delete first;
"""
        if second_h.category == HeldAs.OBJECT:
            code += """            delete second;
"""
        code += """            Py_XDECREF(tuple);
            return 0;
        }
        Py_DECREF(first);
        Py_DECREF(second);
    }
    return tuple;
%End
%ConvertToTypeCode
"""
        code += first_h.declare_type_helpers("first", "return 0;", need_string=first_h.category != HeldAs.INTEGER)
        code += second_h.declare_type_helpers("second", "return 0;", need_string=second_h.category != HeldAs.INTEGER)
        code += """    PyObject *first;
    PyObject *second;
    Py_ssize_t i = 0;

    // Silently check the sequence if that is all that is required.
    if (sipIsErr == NULL) {
        return (PySequence_Check(sipPy)
#if PY_MAJOR_VERSION < 3
                && !PyString_Check(sipPy)
#endif
                && !PyUnicode_Check(sipPy));
        i = PySequence_Size(sipPy);
        if (i != 2) {
            // A negative length should only be an internal error so let the original exception stand.
            if (i >= 0) {
                PyErr_Format(PyExc_TypeError, "sequence has %zd elements but 2 elements are expected", i);
            }
"""
        code += first_h.check_python_type("first")
        code += second_h.check_python_type("second")
        code += """        }
        return 1;
    } else if (*sipIsErr) {
        return 0;
    }

    // Convert the sequence to C++.
    {qt_type}<CxxfirstT, CxxsecondT> *pair = new {qt_type}<CxxfirstT, CxxsecondT>();
    {
"""
        code += first_h.py_to_cxx("first", True, "PySequence_ITEM(sipPy, 0)")
        code += second_h.py_to_cxx("second", True, "PySequence_ITEM(sipPy, 1)")
        code += """
        if (*sipIsErr) {
"""
        if first_h.category != HeldAs.INTEGER:
            code += """            if (cxxfirst == NULL) {
                PyErr_Format(PyExc_TypeError, "tuple first has type '%s' but '%s' is expected",
                             Py_TYPE(first)->tp_name, cxxfirstS);
            }
"""
        if second_h.category != HeldAs.INTEGER:
            code += """            if (cxxsecond == NULL) {
                PyErr_Format(PyExc_TypeError, "tuple second has type '%s' but '%s' is expected",
                             Py_TYPE(second)->tp_name, cxxsecondS);
            }
"""
        code += first_h.release_sip_helper("first")
        code += second_h.release_sip_helper("second")
        code += """            delete pair;
            return 0;
        }
        pair->first = """
        code += first_h.insertable_cxx_value("first") + """;
        pair->second = """
        code += second_h.insertable_cxx_value("second")
        code += """;
"""
        code += first_h.release_sip_helper("first")
        code += second_h.release_sip_helper("second")
        code += """    }
    *sipCppPtr = pair;
    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{qt_type}", qt_type)
        code = code.replace("{first_t}", first_h.cxx_t)
        code = code.replace("{second_t}", second_h.cxx_t)
        return code


class PointerExpander(AbstractExpander):

    def __init__(self):
        super(PointerExpander, self).__init__(["value"])

    def expand_generic(self, qt_type, entries):
        """
        Generic support for Qt pointer types. The template parameter can be of
        any integral (int, long, enum) type or non-integral type, for example,
        QWeakPointer<int>.

        :param qt_type:         The name of the Qt template, e.g. "QSharedDataPointer".
        :param entries:         Dictionary describing the C++ template. Expected keys:

                                    value           Is the value integral, pointer or object?
        """
        value_h = entries["value"]
        code = """
%TypeHeaderCode
#include <{qt_type}>
%End
%ConvertFromTypeCode
"""
        # code += value_h.declare_type_helpers("value", "return 0;")
        # code += value_h.cxx_to_py("value", True, "cxxvalue")
        code += """    typedef {cxx_t} CxxvalueT;
    const sipTypeDef *genvalueT = {sip_t};

    // Convert the value from C++.
    CxxvalueT *cxxvalue = sipCpp->data();
"""
        if value_h.cxx_t.startswith("QExplicitlySharedDataPointer"):
            code += """    cxxvalue->ref.ref();
"""
        code += """    PyObject *value = sipConvertFromType((void *)cxxvalue, genvalueT, sipTransferObj);
"""
        code = code.replace("{cxx_t}", value_h.cxx_t)
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
        if qt_type == "QWeakPointer":
            #
            # A QWeakPointer has to be constructed via an intermediate QSharedPointer.
            #
            code += """    *sipCppPtr = new {qt_type}<CxxvalueT>(QSharedPointer<CxxvalueT>(cxxvalue));
"""
        else:
            code += """    *sipCppPtr = new {qt_type}<CxxvalueT>(cxxvalue);
"""
        if value_h.cxx_t.startswith("QExplicitlySharedDataPointer"):
            code += """    cxxvalue->ref.deref();
"""
        code += """    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{qt_type}", qt_type)
        code = code.replace("{sip_t}", value_h.sip_t)
        return code
