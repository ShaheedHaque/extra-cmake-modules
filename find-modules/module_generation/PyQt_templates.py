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
SIP binding custom type-related code for PyQt-template classes. The main
content is:

    - TypeCodeDb-compatible entries directly usable in RuleSets (e.g.
      typecode_cfttc_dict, typecode_cfttc_list, typecode_cfttc_set)

    - The AbstractExpander class which is a model of how template expansion
      can be performed as needed.

This is supported by other public methods and classes which can be used as
examples and/or helper code.
"""

from abc import *
import logging
import gettext
import os
import re

from clang.cindex import CursorKind, TypeKind

import builtin_rules
from builtin_rules import HeldAs, base_type, parse_template
from sip_generator import trace_generated_for

gettext.install(os.path.basename(__file__))
logger = logging.getLogger(__name__)

# Keep PyCharm happy.
_ = _

QT_PTRS = "(QWeakPointer|Q(Explicitly|)Shared(Data|)Pointer)"
RE_QSHAREDPTR = re.compile("(const )?" + QT_PTRS + "<(.*)>( .)?")


class FunctionParameterHelper(builtin_rules.FunctionParameterHelper):
    """
    Automatic handling for templated function parameter types with auto-unwrapping
    of QT_PTRS.
    """
    def __init__(self, cxx_t, clang_kind, manual_t=None):
        is_qshared = RE_QSHAREDPTR.match(cxx_t)
        if is_qshared:
            template_type = is_qshared.group(2)
            template_args = [is_qshared.group(5)]
            cxx_t = template_args[0] + " *"
        super(FunctionParameterHelper, self).__init__(cxx_t, clang_kind, manual_t)
        self.is_qshared = is_qshared

    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        if self.is_qshared:
            cxx_i += ".data()"
        return super(FunctionParameterHelper, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def cxx_to_cxx(self, aN, original_type, is_out_paramter):
        if self.is_qshared:
            code = """    typedef """ + base_type(original_type) + """ Cxx{aN}T;
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

    def py_parameter(self, type, name, default, annotations):
        if self.is_qshared and default:
            #
            # TODO: We really just want default.data() as the default value, but SIP gets confused.
            #
            default = "NULL"
        return super(FunctionParameterHelper, self).py_parameter(type, name, default, annotations)


class FunctionReturnHelper(builtin_rules.FunctionReturnHelper):
    """
    Automatic handling for templated function return types with auto-unwrapping
    of QT_PTRS templates.
    """
    def __init__(self, cxx_t, clang_kind, manual_t=None):
        is_qshared = RE_QSHAREDPTR.match(cxx_t)
        if is_qshared:
            template_type = is_qshared.group(2)
            template_args = [is_qshared.group(5)]
            cxx_t = template_args[0] + " *"
        super(FunctionReturnHelper, self).__init__(cxx_t, clang_kind, manual_t)
        self.is_qshared = is_qshared

    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        if self.is_qshared:
            cxx_i += ".data()"
        return super(FunctionReturnHelper, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    def py_fn_result(self, is_constructor):
        if self.is_qshared:
            return self.cxx_t
        return super(FunctionReturnHelper, self).py_fn_result(is_constructor)


class GenerateMappedHelper(HeldAs):
    cxx_to_py_templates = {
        HeldAs.INTEGER:
            """#if PY_MAJOR_VERSION >= 3
        PyObject *{name} = PyLong_FromLong((long){cxx_i});
#else
        PyObject *{name} = PyInt_FromLong((long){cxx_i});
#endif
""",
        HeldAs.POINTER:
            """        Cxx{name}T cxx{name} = {cxx_po};
        PyObject *{name} = sipConvertFromType((void *)cxx{name}, gen{name}T, sipTransferObj);
""",
        HeldAs.OBJECT:
            """        Cxx{name}T *cxx{name} = new Cxx{name}T({cxx_po});
        PyObject *{name} = sipConvertFromNewType((void *)cxx{name}, gen{name}T, sipTransferObj);
""",
    }

    py_to_cxx_templates = {
        HeldAs.INTEGER:
            """
#if PY_MAJOR_VERSION >= 3
        Cxx{name}T cxx{name} = (Cxx{name}T)PyLong_AsLong({name});
#else
        Cxx{name}T cxx{name} = (Cxx{name}T)PyInt_AsLong({name});
#endif
""",
        HeldAs.POINTER:
            """        int {name}State;
        Cxx{name}T cxx{name} = NULL;
        cxx{name} = reinterpret_cast<Cxx{name}T>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr));
""",
        HeldAs.OBJECT:
            """        int {name}State;
        Cxx{name}T *cxx{name} = NULL;
        cxx{name} = reinterpret_cast<Cxx{name}T *>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr));
""",
    }

    cxx_to_py_ptr_templates = {
        HeldAs.BYTE:
            """        PyObject *{name} = PyString_FromStringAndSize((char *)({cxx_i}), 1);
""",
        HeldAs.INTEGER:
            """#if PY_MAJOR_VERSION >= 3
        PyObject *{name} = PyLong_FromLong((long)*({cxx_i}));
#else
        PyObject *{name} = PyInt_FromLong((long)*({cxx_i}));
#endif
""",
        HeldAs.FLOAT:
            """        PyObject *{name} = PyFloat_FromDouble((double)*({cxx_i}));
""",
    }

    py_to_cxx_ptr_templates = {
        HeldAs.BYTE:
            """        Cxx{name}T cxx{name} = (Cxx{name}T)PyString_AsString({name});
""",
        HeldAs.INTEGER:
            """
#if PY_MAJOR_VERSION >= 3
        Cxx{name}T cxx{name} = (Cxx{name}T)PyLong_AsLong(*({name}));
#else
        Cxx{name}T cxx{name} = (Cxx{name}T)PyInt_AsLong(*({name}));
#endif
""",
        HeldAs.FLOAT:
            """        Cxx{name}T cxx{name} = (Cxx{name}T)PyFloat_AsDouble(*({name}));
""",
    }

    def __init__(self, entry, clang_kind):
        super(GenerateMappedHelper, self).__init__(entry["type"], clang_kind, entry["base_type"])

    def cxx_to_py_template(self):
        if self.category == HeldAs.POINTER and self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
            return self.cxx_to_py_ptr_templates[self.sip_t]
        return self.cxx_to_py_templates[self.category]

    def py_to_cxx_template(self):
        if self.category == HeldAs.POINTER and self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
            return self.py_to_cxx_ptr_templates[self.sip_t]
        return self.py_to_cxx_templates[self.category]

    def decrement_python_reference(self, name):
        code = """            Py_XDECREF({name});
"""
        code = code.replace("{name}", name)
        return code

    def check_python_type(self, name, extra=""):
        options = {
            HeldAs.INTEGER:
                """#if PY_MAJOR_VERSION >= 3
            if (!PyLong_Check({name})) {
                {extra}return 0;
            }
#else
            if (!PyInt_Check({name})) {
                {extra}return 0;
            }
#endif
""",
            HeldAs.POINTER:
                """            if (!sipCanConvertToType({name}, gen{name}T, SIP_NOT_NONE)) {
                {extra}return 0;
            }
""",
        }
        ptr_options = {
            HeldAs.BYTE:
                """if (!PyString_Check({name})) {
                {extra}return 0;
            }
""",
            HeldAs.INTEGER:
                """#if PY_MAJOR_VERSION >= 3
            if (!PyLong_Check({name})) {
                {extra}return 0;
            }
#else
            if (!PyInt_Check({name})) {
                {extra}return 0;
            }
#endif
""",
            HeldAs.FLOAT:
                """if (!PyFloat_Check({name})) {
                {extra}return 0;
            }
""",
        }
        if self.category == HeldAs.POINTER and self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
            code = ptr_options[self.sip_t]
        else:
            options[HeldAs.OBJECT] = options[HeldAs.POINTER]
            code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{extra}", extra)
        return code

    def release_sip_helper(self, name):
        options = {
            HeldAs.INTEGER:
                "",
            HeldAs.POINTER:
                """        sipReleaseType((void *)cxx{name}, gen{name}T, {name}State);
""",
        }
        if self.category == HeldAs.POINTER and self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
            code = ""
        else:
            options[HeldAs.OBJECT] = options[HeldAs.POINTER]
            code = options[self.category]
        code = code.replace("{name}", name)
        return code

    def insertable_cxx_value(self, name):
        options = {
            HeldAs.INTEGER: "cxx{name}",
            HeldAs.POINTER: "cxx{name}",
            HeldAs.OBJECT: "*cxx{name}",
        }
        code = options[self.category]
        code = code.replace("{name}", name)
        return code


class AbstractExpander(object):
    """
    Defines a basic structure useful for describing the expansion of C++ templated types as SIP %MappedTypes.
    """
    __metaclass__ = ABCMeta

    def __init__(self, variables):
        """
        Constructor.

        :param variables:       The [string] which characterise the template
                                to be expanded.
        """
        self.variables = variables

    @abstractmethod
    def expand_generic(self, qt_type, entries):
        """
        Expand a text-template using the passed parameters.

        :param qt_type:         The name of the Qt template, such as "QMap" or "QHash".
        :param entries:         Dictionary describing the C++ template. Expected keys:

                                    variable1..N    Is the variable integral, pointer or object?

                                The variable1..N are (subclasses of) HeldAs. The base
                                class HeldAs is sufficient for the needs of the default
                                helper functions (@see categorise, @see actual_type and
                                @see base_type).
        """
        raise NotImplemented(_("Missing subclass"))

    def actual_type(self, manual_override, parameter_text, parameter_cursor):
        """
        We would like to be able to use clang type system to determine the parameter type, but structure of the
        child cursors of the typedef do not form an AST. In addition, children of int types are not even included.

        TODO: When we figure this out, get rid of the horrid heuristics.

        :param manual_override:             The user knows best.
        :param parameter_text:              The text from the source code.
        :param parameter_cursor:            The clang object.
        :return: the type of the parameter.
        """
        if manual_override:
            return manual_override
        if parameter_cursor:
            tmp = parameter_cursor.type.get_canonical().spelling
            if parameter_text.endswith(("*", "&")):
                tmp += " " + parameter_text[-1]
            return tmp
        return builtin_rules.actual_type(parameter_text)

    def base_type(self, manual_override, parameter_text, parameter_cursor):
        """
        We would like to be able to use clang type system to determine the underlying type, but structure of the
        child cursors of the typedef do not form an AST. In addition, children of int types are not even included.

        TODO: When we figure this out, get rid of the horrid heuristics.

        :param manual_override:             The user knows best.
        :param parameter_text:              The text from the source code.
        :param parameter_cursor:            The clang object.
        :return: the base_type of the parameter, e.g. without a pointer suffix.
        """
        if manual_override:
            return manual_override
        if parameter_cursor:
            return parameter_cursor.type.get_canonical().spelling
        return builtin_rules.base_type(parameter_text)

    def expand_parameter(self, fn, cursor, sip):
        """
        Expand a parameter template, and return the results via the sip.

        :param fn:              The function for whom the expansion is being performed.
        :param cursor:          The CursorKind for whom the expansion is being performed.
                                This is typically a typed object, such as "QMap" or "QHash".
        :param sip:             The sip. Expected keys:

                                    decl            Optional. Name of the typedef.
                                    foo             dd
        """
        expected_parameters = self.variables
        #
        # Extract the text forms even in cases like 'QSet<QMap<QAction *, KIPI::Category> >'.
        #
        template_type, template_args = parse_template(sip["decl"], len(expected_parameters))
        #
        # Compose the parent type, and the dicts for the parameters and a default declaration.
        #
        entries = {}
        parameters = []
        for i, parameter in enumerate(expected_parameters):
            actual_type = self.actual_type(None, template_args[i], None)
            base_type =  self.base_type(None, template_args[i], None)
            p = {
                "type": actual_type,
                "base_type": base_type,
            }
            entries[parameter] = GenerateMappedHelper(p, None)
            parameters.append(actual_type)
        template_args = ", ".join(parameters)
        #
        # Run the template handler...
        #
        if template_args.endswith(">"):
            template_args += " "
        mapped_type = "{}<{}>".format(template_type, template_args)
        trace = trace_generated_for(cursor, fn, [[entries[p].cxx_t, entries[p].category] for p in expected_parameters])
        code = self.expand_generic(template_type, entries)
        code = "%MappedType " + mapped_type + "\n{\n" + trace + code + "};\n"
        sip["modulecode"][mapped_type] = code

    def expand_typedef(self, fn, cursor, sip):
        """
        Expand a typedef template, and return the results via the sip.

        :param fn:              The function for whom the expansion is being performed.
        :param cursor:          The CursorKind for whom the expansion is being performed.
                                This is typically a typed object, such as "QMap" or "QHash".
        :param sip:             The sip. Expected keys:

                                    decl            Optional. Name of the typedef.
                                    foo             dd
        """
        expected_parameters = self.variables
        #
        # We would like to be able to use clang type system to determine the HELD_AS etc, but the number of children of
        # the typedef is variable (i.e. the structure of an AST is not represented). Also, for example, int types are
        # not even included.
        #
        # So we proceed by get matching arrays of the clang template parameters and the corresponding texts.
        #
        # Start with the clang type system...
        #
        children = list(cursor.get_children())
        if False:
            # Debug
            print("TEMPLATE BEGIN {}".format(sip["decl"]))
            for i, c in enumerate(children):
                if children[i].type.kind == TypeKind.INVALID:
                    tmp = children[i].kind
                else:
                    tmp = children[i].type.kind
                print("    CHILD{}".format(i), tmp, children[i].spelling)
            print("TEMPLATE END")
        #
        # We are only interested in things that can affect the type of the parameters.
        #
        children = [c for c in children if c.kind not in [CursorKind.NAMESPACE_REF, CursorKind.UNEXPOSED_ATTR]]
        parent = children[0]
        assert parent.kind in [CursorKind.TEMPLATE_REF, CursorKind.TYPE_REF], \
            _("Parent {} with kind {}").format(parent.spelling, parent.kind)
        #
        # We only use the information if it matches the cases we understand (i.e. a non-trivial AST is implied).
        #
        if len(children) == len(expected_parameters) + 1:
            types = children[1:]
        else:
            types = [None] * len(expected_parameters)
        #
        # Extract the text forms even in cases like 'QSet<QMap<QAction *, KIPI::Category> >'.
        #
        template_type, template_args = parse_template(sip["decl"], len(expected_parameters))
        #
        # Compose the parent type, and the dicts for the parameters and a default declaration.
        #
        manual_types = sip.get("types", [None] * len(expected_parameters))
        manual_base_types = sip.get("base_types", [None] * len(expected_parameters))
        entries = {}
        parameters = []
        for i, parameter in enumerate(expected_parameters):
            actual_type = self.actual_type(manual_types[i], template_args[i], types[i])
            base_type =  self.base_type(manual_base_types[i], actual_type, types[i])
            p = {
                "type": actual_type,
                "base_type": base_type,
            }
            kind = types[i].type.get_canonical().kind if types[i] else None
            entries[parameter] = GenerateMappedHelper(p, kind)
            parameters.append(actual_type)
        template_args = ", ".join(parameters)
        #
        # Run the template handler...
        #
        if template_args.endswith(">"):
            template_args += " "
        mapped_type = "{}<{}>".format(template_type, template_args)
        trace = trace_generated_for(cursor, fn, [[entries[p].cxx_t, entries[p].category] for p in expected_parameters])
        code = self.expand_generic(parent.spelling, entries)
        code = "%MappedType " + mapped_type + "\n{\n" + trace + code + "};\n"
        sip["modulecode"][mapped_type] = code


class DictExpander(AbstractExpander):

    def __init__(self):
        super(DictExpander, self).__init__(["key", "value"])

    def expand_generic(self, qt_type, entries):
        """
        Generic support for C++ types which map onto a Python dict, such as QMap<k, v> and
        QHash<k, v>. Either template parameter can be of any integral (int, long, enum) type
        or non-integral type, for example, QMap<int, QString>.

        :param qt_type:         The name of the Qt template, e.g. "QMap".
        :param entries:         Dictionary describing the C++ template. Expected keys:

                                    key             Is the key integral, pointer or object?
                                    value           Is the value integral, pointer or object?
        """
        key_h = entries["key"]
        value_h = entries["value"]
        code = """
%TypeHeaderCode
#include <{qt_type}>
%End
%ConvertFromTypeCode
"""
        code += key_h.declare_type_helpers("key", "return 0;")
        code += value_h.declare_type_helpers("value", "return 0;")
        code += """
    // Create the Python dictionary.
    PyObject *dict = PyDict_New();
    if (!dict) {
        PyErr_Format(PyExc_TypeError, "unable to create a dict");
        return 0;
    }

    // Set the dictionary elements.
    {qt_type}<CxxkeyT, CxxvalueT>::const_iterator i = sipCpp->constBegin();
    {qt_type}<CxxkeyT, CxxvalueT>::const_iterator end = sipCpp->constEnd();
    while (i != end) {
"""
        code += key_h.cxx_to_py("key", True, "i.key()")
        code += value_h.cxx_to_py("value", True, "i.value()")
        #
        # Error handling assumptions:
        #
        #   - a failed "new" throws (or, not compliant, return NULL).
        #   - the good path should be as fast as possible, error recovery can be slow.
        #
        code += """
        if (key == NULL || value == NULL || PyDict_SetItem(dict, key, value) < 0) {
            PyErr_Format(PyExc_TypeError, "cannot insert key/value into dict");
"""
        code += key_h.decrement_python_reference("key") + value_h.decrement_python_reference("value")
        if key_h.category == HeldAs.OBJECT:
            code += """            delete key;
"""
        if value_h.category == HeldAs.OBJECT:
            code += """            delete value;
"""
        code += """            Py_DECREF(dict);
            return 0;
        }
        Py_DECREF(key);
        Py_DECREF(value);
        ++i;
    }
    return dict;
%End
%ConvertToTypeCode
"""
        code += key_h.declare_type_helpers("key", "return 0;", need_string=key_h.category != HeldAs.INTEGER)
        code += value_h.declare_type_helpers("value", "return 0;", need_string=value_h.category != HeldAs.INTEGER)
        code += """    PyObject *key;
    PyObject *value;
    Py_ssize_t i = 0;

    // Silently check the dict if that is all that is required.
    if (sipIsErr == NULL) {
        if (!PyDict_Check(sipPy)) {
            return 0;
        }

        while (PyDict_Next(sipPy, &i, &key, &value)) {
"""
        code += key_h.check_python_type("key")
        code += value_h.check_python_type("value")
        code += """        }
        return 1;
    } else if (*sipIsErr) {
        return 0;
    }
    if (!PyDict_Check(sipPy)) {
        PyErr_Format(PyExc_TypeError, "expected dict");
        *sipIsErr = 1;
        return 0;
    }

    // Convert the dict to C++.
    {qt_type}<CxxkeyT, CxxvalueT> *dict = new {qt_type}<CxxkeyT, CxxvalueT>();
    while (PyDict_Next(sipPy, &i, &key, &value)) {
"""
        code += key_h.py_to_cxx("key", True, "key")
        code += value_h.py_to_cxx("value", True, "value")
        code += """
        if (*sipIsErr) {
"""
        if key_h.category != HeldAs.INTEGER:
            code += """            if (cxxkey == NULL) {
                PyErr_Format(PyExc_TypeError, "a dict key has type '%s' but '%s' is expected",
                             Py_TYPE(key)->tp_name, cxxkeyS);
            }
"""
        if value_h.category != HeldAs.INTEGER:
            code += """            if (cxxvalue == NULL) {
                PyErr_Format(PyExc_TypeError, "a dict value has type '%s' but '%s' is expected",
                             Py_TYPE(value)->tp_name, cxxvalueS);
            }
"""
        code += key_h.release_sip_helper("key")
        code += value_h.release_sip_helper("value")
        code += """            delete dict;
            return 0;
        }
        dict->insert("""
        code += key_h.insertable_cxx_value("key") + ", " + value_h.insertable_cxx_value("value")
        code += """);
"""
        code += key_h.release_sip_helper("key")
        code += value_h.release_sip_helper("value")
        code += """    }
    *sipCppPtr = dict;
    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{qt_type}", qt_type)
        code = code.replace("{key_t}", key_h.cxx_t)
        code = code.replace("{value_t}", value_h.cxx_t)
        return code


class ListExpander(AbstractExpander):

    def __init__(self):
        super(ListExpander, self).__init__(["value"])

    def expand_generic(self, qt_type, entries):
        """
        Generic support for C++ types which map onto a Python list, such as QList<v> and
        QVector<v>. The template parameter can be of any integral (int, long, enum) type
        or non-integral type, for example, QList<int> or QList<QString>.

        :param qt_type:         The name of the Qt template, e.g. "QList".
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
        code += value_h.declare_type_helpers("value", "return 0;")
        code += """
    // Create the Python list.
    PyObject *list = PyList_New(sipCpp->size());
    if (!list) {
        PyErr_Format(PyExc_TypeError, "unable to create a list");
        return 0;
    }

    // Set the list elements.
    Py_ssize_t i = 0;
    for (i = 0; i < sipCpp->size(); ++i) {
"""
        code += value_h.cxx_to_py("value", True, "sipCpp->value(i)", "sipCpp->at(i)")
        code += """
        if (value == NULL) {
            PyErr_Format(PyExc_TypeError, "cannot insert value into list");
"""
        code += value_h.decrement_python_reference("value")
        code += """            Py_DECREF(list);
            return 0;
        } else {
            PyList_SET_ITEM(list, i, value);
        }
    }
    return list;
%End
%ConvertToTypeCode
"""
        code += value_h.declare_type_helpers("value", "return 0;", need_string=value_h.category != HeldAs.INTEGER)
        code += """    PyObject *value;
    Py_ssize_t i = 0;

    // Silently check the list if that is all that is required.
    if (sipIsErr == NULL) {
        if (!PyList_Check(sipPy)) {
            return 0;
        }

        for (i = 0; i < PyList_GET_SIZE(sipPy); ++i) {
            value = PyList_GET_ITEM(sipPy, i);
"""
        code += value_h.check_python_type("value",)
        code += """        }
        return 1;
    } else if (*sipIsErr) {
        return 0;
    }
    if (!PyList_Check(sipPy)) {
        PyErr_Format(PyExc_TypeError, "expected list");
        *sipIsErr = 1;
        return 0;
    }

    // Convert the list to C++.
    {qt_type}<CxxvalueT> *list = new {qt_type}<CxxvalueT>();
    for (i = 0; i < PyList_GET_SIZE(sipPy); ++i) {
        value = PyList_GET_ITEM(sipPy, i);
"""
        code += value_h.py_to_cxx("value", True, "value")
        code += """
        if (*sipIsErr) {
"""
        if value_h.category != HeldAs.INTEGER:
            code += """            if (cxxvalue == NULL) {
                PyErr_Format(PyExc_TypeError, "list value %ld has type '%s' but '%s' is expected", i,
                             Py_TYPE(value)->tp_name, cxxvalueS);
            }
"""
        code += value_h.release_sip_helper("value")
        code += """            delete list;
            return 0;
        }
        list->append("""
        code += value_h.insertable_cxx_value("value")
        code += """);
"""
        code += value_h.release_sip_helper("value")
        code += """    }
    *sipCppPtr = list;
    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{qt_type}", qt_type)
        code = code.replace("{value_t}", value_h.cxx_t)
        return code


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


class SetExpander(AbstractExpander):

    def __init__(self):
        super(SetExpander, self).__init__(["value"])

    def expand_generic(self, qt_type, entries):
        """
        Generic support for QSet<v>. The template parameter can be of any
        integral (int, long, enum) type or non-integral type, for example,
        QSet<int> or QSet<QString>.

        :param qt_type:         The name of the Qt template, e.g. "QSet".
        :param entries:         Dictionary describing the C++ template. Expected keys:

                                    value           Is the item integral, pointer or object?
        """
        value_h = entries["value"]
        code = """
%TypeHeaderCode
#include <{qt_type}>
%End
%ConvertFromTypeCode
"""
        code += value_h.declare_type_helpers("value", "return 0;")
        code += """
    // Create the Python set.
    PyObject *set = PySet_New(NULL);
    if (!set) {
        PyErr_Format(PyExc_TypeError, "unable to create a set");
        return 0;
    }

    // Set the set elements.
    {qt_type}<CxxvalueT>::const_iterator i = sipCpp->constBegin();
    {qt_type}<CxxvalueT>::const_iterator end = sipCpp->constEnd();
    while (i != end) {
"""
        code += value_h.cxx_to_py("value", True, "sipCpp->value(i)", "*i")
        code += """
        if (value == NULL || PySet_Add(set, value) < 0) {
            PyErr_Format(PyExc_TypeError, "cannot insert value into set");
"""
        code += value_h.decrement_python_reference("value")
        code += """            Py_DECREF(set);
            return 0;
        }
        ++i;
    }
    return set;
%End
%ConvertToTypeCode
"""
        code += value_h.declare_type_helpers("value", "*sipIsErr = 1;", need_string=value_h.category != HeldAs.INTEGER)
        code += """    PyObject *value;
    PyObject *i = PyObject_GetIter(sipPy);
    if (i == NULL) {
        if (sipIsErr) {
            PyErr_Format(PyExc_TypeError, "unable to allocate set iterator");
            *sipIsErr = 1;
        }
        return 0;
    }

    // Silently check the set if that is all that is required.
    if (sipIsErr == NULL) {
        if (!PySet_Check(sipPy)) {
            Py_DECREF(i);
            return 0;
        }

        while ((value = PyIter_Next(i)) != NULL) {
"""
        code += value_h.check_python_type("value", "Py_DECREF(i);\n                ")
        code += """        }
        Py_DECREF(i);
        return 1;
    } else if (*sipIsErr) {
        Py_DECREF(i);
        return 0;
    }
    if (!PySet_Check(sipPy)) {
        Py_DECREF(i);
        PyErr_Format(PyExc_TypeError, "expected set");
        *sipIsErr = 1;
        return 0;
    }

    // Convert the set to C++.
    {qt_type}<CxxvalueT> *set = new {qt_type}<CxxvalueT>();
    while ((value = PyIter_Next(i)) != NULL) {
"""
        code += value_h.py_to_cxx("value", True, "value")
        code += """
        if (*sipIsErr) {
"""
        if value_h.category != HeldAs.INTEGER:
            code += """            if (cxxvalue == NULL) {
                PyErr_Format(PyExc_TypeError, "a set value has type '%s' but '%s' is expected",
                             Py_TYPE(value)->tp_name, cxxvalueS);
            }
"""
        code += value_h.release_sip_helper("value")
        code += """            delete set;
            Py_DECREF(i);
            return 0;
        }
        set->insert("""
        code += value_h.insertable_cxx_value("value")
        code += """);
"""
        code += value_h.release_sip_helper("value")
        code += """    }
    Py_DECREF(i);
    *sipCppPtr = set;
    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{qt_type}", qt_type)
        code = code.replace("{value_t}", value_h.cxx_t)
        return code


def function_uses_templates(container, function, sip, matcher):
    """
    A FunctionDb-compatible function used to create %MethodCode expansions
    for C++ functions with templated return types and/or parameters.
    """
    sip.setdefault("parameter_helper", FunctionParameterHelper)
    sip.setdefault("return_helper", FunctionReturnHelper)
    builtin_rules.function_uses_templates(container, function, sip, matcher)


def dict_parameter(container, function, parameter, sip, matcher):
    """
    A ParameterDb-compatible function used to create a %MappedType for C++
    types with two template arguments into Python dicts.
    """
    template = DictExpander()
    template.expand_parameter(dict_parameter, parameter, sip)


def dict_typecode(container, typedef, sip, matcher):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for C++
    types with two template arguments into Python dicts.
    """
    template = DictExpander()
    template.expand_typedef(dict_typecode, typedef, sip)


def list_parameter(container, function, parameter, sip, matcher):
    """
    A ParameterDb-compatible function used to create a %MappedType for C++
    C++ types with one template argument into Python lists.
    """
    template = ListExpander()
    template.expand_parameter(list_parameter, parameter, sip)


def list_typecode(container, typedef, sip, matcher):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for C++
    types with one template argument into Python lists.
    """
    template = ListExpander()
    template.expand_typedef(list_typecode, typedef, sip)


def set_parameter(container, function, parameter, sip, matcher):
    """
    A ParameterDb-compatible function used to create a %MappedType for C++
    types with one template argument into Python sets.
    """
    template = SetExpander()
    template.expand_parameter(set_parameter, parameter, sip)


def set_typecode(container, typedef, sip, matcher):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for C++
    types with one template argument into Python sets.
    """
    template = SetExpander()
    template.expand_typedef(set_typecode, typedef, sip)


def pair_parameter(container, function, parameter, sip, matcher):
    """
    A ParameterDb-compatible function used to create a %MappedType for a
    QPair<> (using a 2-tuple).
    """
    handler = PairExpander()
    handler.expand_parameter(pair_parameter, parameter, sip)


def pair_typecode(container, typedef, sip, matcher):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for a
    QPair<> (using a 2-tuple).
    """
    template = PairExpander()
    template.expand_typedef(pair_typecode, typedef, sip)


def pointer_parameter(container, function, parameter, sip, matcher):
    """
    A ParameterDb-compatible function used to create a %MappedType for a
    Qt pointer type.
    """
    handler = PointerExpander()
    handler.expand_parameter(pointer_parameter, parameter, sip)


def pointer_typecode(container, typedef, sip, matcher):
    """
    A TypeCodeDb-compatible function used to create a %MappedType for a
    Qt pointer type.
    """
    handler = PointerExpander()
    if typedef.underlying_typedef_type.kind == TypeKind.ELABORATED:
        #
        # This is a typedef of a typedef, and Clang gets the template
        # parameters wrong, so abort.
        #
        return
    assert typedef.underlying_typedef_type.kind == TypeKind.UNEXPOSED
    handler.expand_typedef(pointer_parameter, typedef, sip)
