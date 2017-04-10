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

from clang.cindex import CursorKind, TypeKind

import builtin_rules
from builtin_rules import HeldAs, parse_template
from sip_generator import trace_generated_for

gettext.install(os.path.basename(__file__))
logger = logging.getLogger(__name__)

# Keep PyCharm happy.
_ = _


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
        PyObject *{name} = sipConvertFromType(cxx{name}, gen{name}T, sipTransferObj);
""",
        HeldAs.OBJECT:
            """        Cxx{name}T *cxx{name} = new Cxx{name}T({cxx_po});
        PyObject *{name} = sipConvertFromNewType(cxx{name}, gen{name}T, sipTransferObj);
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

    def __init__(self, entry, clang_kind):
        super(GenerateMappedHelper, self).__init__(entry["type"], clang_kind, entry["base_type"])

    def cxx_to_py_template(self):
        return self.cxx_to_py_templates[self.category]

    def py_to_cxx_template(self):
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
                """        sipReleaseType(cxx{name}, gen{name}T, {name}State);
""",
        }
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

    def __init__(self):
        pass

    @abstractmethod
    def variables(self):
        """
        Returns a list of the variables needed by this expansion.

        :return: [string]
        """
        raise NotImplemented(_("Missing subclass"))

    @abstractmethod
    def decl(self, qt_type, entry):
        """
        Expand a text-template using the passed parameters.

        :param qt_type:         The name of the Qt template, such as "QMap" or "QHash".
        :param entry:           Dictionary describing the C++ template. Expected keys:

                                    variable1..N    Dictionaries, keyed by the needed @see variables().

                                The variable1..N dictionaries have keys determined by the subclass. The defaults used
                                by this superclass are driven by the needs of the default helper functions
                                (@see categorise, @see actual_type and @see base_type), and are presently:

                                    type            The type of the item.
                                    base_type       The base type of the item, different from type in the case of a
                                                    pointer.
                                    held_as         Is the item integral, pointer or object?
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

    def expand(self, cursor, sip):
        """
        Expand a template using the passed parameters, and return the results via the sip.

        :param cursor:          The CursorKind for whom the expansion is being performed. This is typically a typed
                                object, such as "QMap" or "QHash".
        :param sip:             The sip. Expected keys:

                                    decl            Optional. Name of the typedef.
                                    foo             dd
        """
        expected_parameters = self.variables()
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
        # Secondly, extract the text forms even in cases like 'QSet<QMap<QAction *, KIPI::Category> >'.
        #
        original_type, original_args = parse_template(sip["decl"], len(expected_parameters))
        #
        # Compose the parent type, and the dicts for the parameters and a default declaration.
        #
        manual_types = sip.get("types", [None] * len(expected_parameters))
        manual_base_types = sip.get("base_types", [None] * len(expected_parameters))
        entry = {}
        parameters = []
        for i, parameter in enumerate(expected_parameters):
            p = {}
            p["type"] = self.actual_type(manual_types[i], original_args[i], types[i])
            p["base_type"] = self.base_type(manual_base_types[i], p["type"], types[i])
            kind = types[i].type.get_canonical().kind if types[i] else None
            p["held_as"] = GenerateMappedHelper(p, kind)
            entry[parameter] = p
            parameters.append(p["type"])
        original_args = ", ".join(parameters)
        #
        # Run the template handler...
        #
        if original_args.endswith(">"):
            original_args += " "
        mapped_type = "{}<{}>".format(original_type, original_args)
        trace = trace_generated_for(cursor, self.decl, {p: entry[p]["held_as"].category for p in expected_parameters})
        code = self.decl(parent.spelling, entry)
        code = "%MappedType " + mapped_type + "\n{\n" + trace + code + "};\n"
        sip["module_code"][mapped_type] = code


class DictExpander(AbstractExpander):

    def __init__(self):
        super(DictExpander, self).__init__()

    def variables(self):
        return ["key", "value"]

    def decl(self, qt_type, entry):
        """
        Generic support for C++ types which map onto a Python dict, such as QMap<k, v> and
        QHash<k, v>. Either template parameter can be of any integral (int, long, enum) type
        or non-integral type, for example, QMap<int, QString>.

        :param qt_type:         The name of the Qt template, e.g. "QMap".
        :param entry:           Dictionary describing the C++ template. Expected keys:

                                    key             Description of key.
                                    value           Description of value.

                                The key and value descriptions have the following keys:

                                    type            The type of the item.
                                    base_type       The base type of the item, different from type in the case of a
                                                    pointer.
                                    held_as         Is the item integral, pointer or object?
        """
        key_h = entry["key"]["held_as"]
        value_h = entry["value"]["held_as"]
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
        key_t = entry["key"]["type"]
        code = code.replace("{key_t}", key_t)
        value_t = entry["value"]["type"]
        code = code.replace("{value_t}", value_t)
        return code


class ListExpander(AbstractExpander):

    def __init__(self):
        super(ListExpander, self).__init__()

    def variables(self):
        return ["value"]

    def decl(self, qt_type, entry):
        """
        Generic support for C++ types which map onto a Python list, such as QList<v> and
        QVector<v>. The template parameter can be of any integral (int, long, enum) type
        or non-integral type, for example, QList<int> or QList<QString>.

        :param qt_type:         The name of the Qt template, e.g. "QList".
        :param entry:           Dictionary describing the C++ template. Expected keys:

                                    value           Description of value.

                                The value description has the following keys:

                                    type            The type of the item.
                                    base_type       The base type of the item, different from type in the case of a
                                                    pointer.
                                    held_as         Is the item integral, pointer or object?
        """
        value_h = entry["value"]["held_as"]
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
        value_t = entry["value"]["type"]
        code = code.replace("{value_t}", value_t)
        return code


class QPairExpander(AbstractExpander):

    def __init__(self):
        super(QPairExpander, self).__init__()

    def variables(self):
        return ["first", "second"]

    def decl(self, qt_type, entry):
        """
        Generic support for QPair types which are mapped onto a Python tuple. Either
        template parameter can be of any integral (int, long, enum) type or
        non-integral type, for example, QPair<int, QString>.

        :param qt_type:         The name of the Qt template, e.g. "QPair".
        :param entry:           Dictionary describing the C++ template. Expected firsts:

                                    first           Description of first part of pair.
                                    second          Description of second part of pair.

                                The first and second descriptions have the following firsts:

                                    type            The type of the item.
                                    base_type       The base type of the item, different from type in the case of a
                                                    pointer.
                                    held_as         Is the item integral, pointer or object?
        """
        first_h = entry["first"]["held_as"]
        second_h = entry["second"]["held_as"]
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
        first_t = entry["first"]["type"]
        code = code.replace("{first_t}", first_t)
        second_t = entry["second"]["type"]
        code = code.replace("{second_t}", second_t)
        return code


class SetExpander(AbstractExpander):

    def __init__(self):
        super(SetExpander, self).__init__()

    def variables(self):
        return ["value"]

    def decl(self, qt_type, entry):
        """
        Generic support for QSet<v>. The template parameter can be of any
        integral (int, long, enum) type or non-integral type, for example,
        QSet<int> or QSet<QString>.

        :param qt_type:         The name of the Qt template, e.g. "QSet".
        :param entry:           Dictionary describing the C++ template. Expected keys:

                                    value           Description of value.

                                The value description has the following keys:

                                    type            The type of the item.
                                    base_type       The base type of the item, different from type in the case of a
                                                    pointer.
                                    held_as         Is the item integral, pointer or object?
        """
        value_h = entry["value"]["held_as"]
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
        value_t = entry["value"]["type"]
        code = code.replace("{value_t}", value_t)
        return code


def typecode_cfttc_dict(container, typedef, sip, matcher):
    """
    A TypeCodeDb-compatible function used to create %MappedType expansions for C++ types with two template arguments
    into Python dicts.
    """
    template = DictExpander()
    template.expand(typedef, sip)


def typecode_cfttc_list(container, typedef, sip, matcher):
    """
    A TypeCodeDb-compatible function used to create %MappedType expansions fpr C++ types with one template argument
    into Python lists.
    """
    template = ListExpander()
    template.expand(typedef, sip)


def typecode_cfttc_set(container, typedef, sip, matcher):
    """
    A TypeCodeDb-compatible function used to create %MappedType expansions for C++ types with one template argument
    into Python sets.
    """
    template = SetExpander()
    template.expand(typedef, sip)


def typecode_cfttc_tuple_pair(container, typedef, sip, matcher):
    """
    A TypeCodeDb-compatible function used to create %MappedType expansions for QPair with one template argument
    into Python sets.
    """
    template = QPairExpander()
    template.expand(typedef, sip)
