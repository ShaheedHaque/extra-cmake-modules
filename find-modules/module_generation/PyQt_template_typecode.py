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

    - TypeCodeDb-compatible entries directly usable un RuleSets (e.g.
      typecode_cfttc_dict, typecode_cfttc_list, typecode_cfttc_set)

    - The AbstractExpander class which is a model of how template expansion
      can be performed as needed.

This is supported by other public methods and classes which can be used as
examples and/or helper code. Notable among these is the declare_aliases()
function.
"""

from abc import *
import inspect
import logging
import gettext
import os

from clang.cindex import CursorKind, TypeKind

from builtin_rules import HeldAs
from sip_generator import SipGenerator

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
    def _text(self, cursor, entry):
        """
        Expand a text-template using the passed parameters.

        :param cursor:          The CursorKind for whom the expansion is being performed. This is typically a type
                                object, such as "QMap" or "QHash".
        :param entry:           Dictionary describing the C++ template. Expected keys:

                                    name            Name of the C++ template, "QMap".
                                    mapped_type     Complete C++ template declaration, "QMap<int, String>".
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
        return parameter_text

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
        if parameter_text.endswith("Ptr"):
            parameter_text = parameter_text[:-3]
            if parameter_text.endswith("::"):
                parameter_text = parameter_text[:-2]
        elif parameter_text.endswith(("*", "&")):
            parameter_text = parameter_text[:-1].strip()
        return parameter_text

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
        assert parent.kind == CursorKind.TEMPLATE_REF, _("Parent {} with kind {}").format(parent.spelling, parent.kind)
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
        decls = []
        bracket_level = 0
        text = sip["decl"][len(parent.spelling) + 1:-1]
        left = 0
        for right, token in enumerate(text):
            if bracket_level <= 0 and token is ",":
                decls.append(text[left:right].strip())
                left = right + 1
            elif token is "<":
                bracket_level += 1
            elif token is ">":
                bracket_level -= 1
        decls.append(text[left:].strip())
        assert len(decls) == len(expected_parameters), _("Cannot extract decls from {}").format(sip["decl"])
        #
        # Compose the parent type, and the dicts for the parameters and a default declaration.
        #
        manual_types = sip.get("types", [None] * len(expected_parameters))
        manual_base_types = sip.get("base_types", [None] * len(expected_parameters))
        entry = {}
        parameters = []
        for i, parameter in enumerate(expected_parameters):
            p = {}
            p["type"] = self.actual_type(manual_types[i], decls[i], types[i])
            p["base_type"] = self.base_type(manual_base_types[i], p["type"], types[i])
            kind = types[i].type.get_canonical().kind if types[i] else None
            p["held_as"] = GenerateMappedHelper(p["type"], kind, p["base_type"])
            entry[parameter] = p
            parameters.append(p["type"])
        parameters = ", ".join(parameters)
        if parameters.endswith(">"):
            parameters += " "
        entry["name"] = parent.spelling
        entry["mapped_type"] = "{}<{}>".format(parent.spelling, parameters)
        #
        # Run the handler...
        #
        fn = self._text
        fn_file = os.path.basename(inspect.getfile(fn))
        from copy import deepcopy
        tmp = {k: v for (k, v) in deepcopy(entry.items()) if k != "code"}
        for parameter in expected_parameters:
            tmp[parameter]["held_as"] = tmp[parameter]["held_as"].category
        trace = "// Generated for {} of {} (by {}:{}): {}".format(SipGenerator.describe(cursor),
                                                                    os.path.basename(cursor.extent.start.file.name),
                                                                    fn_file, fn.__name__,
                                                                    tmp)
        fn(cursor, entry)
        code = "%MappedType " + entry["mapped_type"] + "\n{\n" + trace + entry["code"] + "};\n"
        sip["module_code"][entry["mapped_type"]] = code


class DictExpander(AbstractExpander):

    def __init__(self):
        super(DictExpander, self).__init__()

    def variables(self):
        return ["key", "value"]

    def _text(self, typedef, entry):
        """
        Generic support for C++ types which map onto a Python dict, such as QMap<k, v> and
        QHash<k, v>. Either template parameter can be of any integral (int, long, enum) type
        or non-integral type, for example, QMap<int, QString>.

        :param typedef:         The CursorKind, such as "QMap" or "QHash".
        :param entry:           Dictionary describing the C++ template. Expected keys:

                                    name            Name of the C++ template, "QMap".
                                    mapped_type     Complete C++ template declaration, "QMap<int, String>".
                                    key             Description of key.
                                    value           Description of value.

                                The key and value descriptions have the following keys:

                                    type            The type of the item.
                                    base_type       The base type of the item, different from type in the case of a
                                                    pointer.
                                    held_as         Is the item integral, pointer or object?
        """
        key_category = entry["key"]["held_as"]
        value_category = entry["value"]["held_as"]
        code = """
%TypeHeaderCode
#include <{cxx_type}>
%End
%ConvertFromTypeCode
"""
        code += key_category.declare_type_helpers("key", "return 0;")
        code += value_category.declare_type_helpers("value", "return 0;")
        code += """
    // Create the Python dictionary.
    PyObject *dict = PyDict_New();
    if (!dict) {
        PyErr_Format(PyExc_TypeError, "unable to create a dict");
        return 0;
    }

    // Set the dictionary elements.
    {cxx_type}<CxxkeyT, CxxvalueT>::const_iterator i = sipCpp->constBegin();
    {cxx_type}<CxxkeyT, CxxvalueT>::const_iterator end = sipCpp->constEnd();
    while (i != end) {
"""
        code += key_category.cxx_to_py("key", True, "i.key()")
        code += value_category.cxx_to_py("value", True, "i.value()")
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
        code += key_category.decrement_python_reference("key") + value_category.decrement_python_reference("value")
        if key_category.category == HeldAs.OBJECT:
            code += """            delete key;
"""
        if value_category.category == HeldAs.OBJECT:
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
        code += key_category.declare_type_helpers("key", "return 0;", need_string=True)
        code += value_category.declare_type_helpers("value", "return 0;", need_string=True)
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
        code += key_category.check_python_type("key")
        code += value_category.check_python_type("value")
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
    {cxx_type}<CxxkeyT, CxxvalueT> *dict = new {cxx_type}<CxxkeyT, CxxvalueT>();
    while (PyDict_Next(sipPy, &i, &key, &value)) {
"""
        code += key_category.py_to_cxx("key", True, "key")
        code += value_category.py_to_cxx("value", True, "value")
        code += """
        if (*sipIsErr) {
            if (cxxkey == NULL) {
                PyErr_Format(PyExc_TypeError, "a dict key has type '%s' but '%s' is expected",
                             Py_TYPE(key)->tp_name, cxxkeyS);
            }
            if (cxxvalue == NULL) {
                PyErr_Format(PyExc_TypeError, "a dict value has type '%s' but '%s' is expected",
                             Py_TYPE(value)->tp_name, cxxvalueS);
            }
"""
        code += key_category.release_sip_helper("key")
        code += value_category.release_sip_helper("value")
        code += """            delete dict;
            return 0;
        }
        dict->insert("""
        code += key_category.insertable_cxx_value("key") + ", " + value_category.insertable_cxx_value("value")
        code += """);
"""
        code += key_category.release_sip_helper("key")
        code += value_category.release_sip_helper("value")
        code += """    }
    *sipCppPtr = dict;
    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{cxx_type}", entry["name"])
        key_t = entry["key"]["type"]
        code = code.replace("{key_t}", key_t)
        value_t = entry["value"]["type"]
        code = code.replace("{value_t}", value_t)
        entry["code"] = code


class ListExpander(AbstractExpander):

    def __init__(self):
        super(ListExpander, self).__init__()

    def variables(self):
        return ["value"]

    def _text(self, typedef, entry):
        """
        Generic support for C++ types which map onto a Python list, such as QList<v> and
        QVector<v>. The template parameter can be of any integral (int, long, enum) type
        or non-integral type, for example, QList<int> or QList<QString>.

        :param typedef:         The type, such as "QList" or "QVector".
        :param entry:           Dictionary describing the C++ template. Expected keys:

                                    name            Name of the C++ template, "QList".
                                    mapped_type     Complete C++ template declaration, "QList<int>".
                                    value           Description of value.

                                The value description has the following keys:

                                    type            The type of the item.
                                    base_type       The base type of the item, different from type in the case of a
                                                    pointer.
                                    held_as         Is the item integral, pointer or object?
        """
        value_category = entry["value"]["held_as"]
        code = """
%TypeHeaderCode
#include <{cxx_type}>
%End
%ConvertFromTypeCode
"""
        code += value_category.declare_type_helpers("value", "return 0;")
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
        code += value_category.cxx_to_py("value", True, "sipCpp->value(i)", "sipCpp->at(i)")
        code += """
        if (value == NULL) {
            PyErr_Format(PyExc_TypeError, "cannot insert value into list");
"""
        code += value_category.decrement_python_reference("value")
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
        code += value_category.declare_type_helpers("value", "return 0;", need_string=True)
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
        code += value_category.check_python_type("value",)
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
    {cxx_type}<CxxvalueT> *list = new {cxx_type}<CxxvalueT>();
    for (i = 0; i < PyList_GET_SIZE(sipPy); ++i) {
        value = PyList_GET_ITEM(sipPy, i);
"""
        code += value_category.py_to_cxx("value", True, "value")
        code += """
        if (*sipIsErr) {
            if (cxxvalue == NULL) {
                PyErr_Format(PyExc_TypeError, "list value %ld has type '%s' but '%s' is expected", i,
                             Py_TYPE(value)->tp_name, cxxvalueS);
            }
"""
        code += value_category.release_sip_helper("value")
        code += """            delete list;
            return 0;
        }
        list->append("""
        code += value_category.insertable_cxx_value("value")
        code += """);
"""
        code += value_category.release_sip_helper("value")
        code += """    }
    *sipCppPtr = list;
    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{cxx_type}", entry["name"])
        value_t = entry["value"]["type"]
        code = code.replace("{value_t}", value_t)
        entry["code"] = code


class SetExpander(AbstractExpander):

    def __init__(self):
        super(SetExpander, self).__init__()

    def variables(self):
        return ["value"]

    def _text(self, typedef, entry):
        """
        Generic support for QSet<v>. The template parameter can be of any
        integral (int, long, enum) type or non-integral type, for example,
        QSet<int> or QSet<QString>.

        :param typedef:         The type, such as "QSet".
        :param entry:           Dictionary describing the C++ template. Expected keys:

                                    name            Name of the C++ template, "QSet".
                                    mapped_type     Complete C++ template declaration, "QSet<int>".
                                    value           Description of value.

                                The value description has the following keys:

                                    type            The type of the item.
                                    base_type       The base type of the item, different from type in the case of a
                                                    pointer.
                                    held_as         Is the item integral, pointer or object?
        """
        value_category = entry["value"]["held_as"]
        code = """
%TypeHeaderCode
#include <{cxx_type}>
%End
%ConvertFromTypeCode
"""
        code += value_category.declare_type_helpers("value", "return 0;", need_string=True)
        code += """
    // Create the Python set.
    PyObject *set = PySet_New(NULL);
    if (!set) {
        PyErr_Format(PyExc_TypeError, "unable to create a set");
        return 0;
    }

    // Set the set elements.
    {cxx_type}<CxxvalueT>::const_iterator i = sipCpp->constBegin();
    {cxx_type}<CxxvalueT>::const_iterator end = sipCpp->constEnd();
    while (i != end) {
"""
        code += value_category.cxx_to_py("value", True, "sipCpp->value(i)", "*i")
        code += """
        if (value == NULL || PySet_Add(set, value) < 0) {
            PyErr_Format(PyExc_TypeError, "cannot insert value into set");
"""
        code += value_category.decrement_python_reference("value")
        code += """            Py_DECREF(set);
            return 0;
        }
        ++i;
    }
    return set;
%End
%ConvertToTypeCode
"""
        code += value_category.declare_type_helpers("value", "*sipIsErr = 1;", need_string=True)
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

        while (value = PyIter_Next(i)) {
"""
        code += value_category.check_python_type("value", "Py_DECREF(i);\n                ")
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
        *sipIsErr = 1
        return 0;
    }

    // Convert the set to C++.
    {cxx_type}<CxxvalueT> *set = new {cxx_type}<CxxvalueT>();
    while (value = PyIter_Next(i)) {
"""
        code += value_category.py_to_cxx("value", True, "value")
        code += """
        if (*sipIsErr) {
            if (cxxvalue == NULL) {
                PyErr_Format(PyExc_TypeError, "a set value has type '%s' but '%s' is expected",
                             Py_TYPE(value)->tp_name, cxxvalueS);
            }
"""
        code += value_category.release_sip_helper("value")
        code += """            delete set;
            Py_DECREF(i);
            return 0;
        }
        set->insert("""
        code += value_category.insertable_cxx_value("value")
        code += """);
"""
        code += value_category.release_sip_helper("value")
        code += """    }
    Py_DECREF(i);
    *sipCppPtr = set;
    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{cxx_type}", entry["name"])
        value_t = entry["value"]["type"]
        code = code.replace("{value_t}", value_t)
        entry["code"] = code


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
