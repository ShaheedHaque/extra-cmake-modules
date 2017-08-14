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
Generic SIP %MappedType code for C++-template classes. The main content is:

    - The AbstractExpander class which is a model of how template expansion
      can be performed as needed.

    - {Dict,List,Set}Expander derived classes which implement corresponding
      templates.

    - FunctionDb, ParameterDb and TypeCodeDb-compatible entries usable in
      RuleSets (e.g. {dict,list,set}_{fn_result,parameter,typecode}).

This is supported by other public methods and classes which can be used as
examples and/or helper code.
"""
from abc import ABCMeta, abstractmethod
import gettext
import logging
import os

from clangcparser import CursorKind, TypeKind
from rule_helpers import trace_generated_for, HeldAs


gettext.install(os.path.basename(__file__))
logger = logging.getLogger(__name__)

# Keep PyCharm happy.
_ = _


class AbstractExpander(object):
    """
    Defines a basic structure useful for describing the expansion of C++
    templated types as SIP %MappedTypes.

    Rule writers can tailor the expansion using custom subclasses which
    override the template itself (@see expand_generic()) and the parameters
    (@see __init__()).
    """
    __metaclass__ = ABCMeta

    def __init__(self, variables):
        """
        Constructor.

        :param variables:       The [(string, class)] which characterise the template
                                to be expanded.
        """
        self.variables = [v[0] for v in variables]
        self.helpers = {v[0]: v[1] for v in variables}

    @abstractmethod
    def expand_generic(self, template_t, entries):
        """
        Expand a text-template using the passed parameters.

        :param template_t:      The name of the C++ template, such as "QMap" or "std::vector".
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
        return HeldAs.actual_type(parameter_text)

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
        return HeldAs.base_type(parameter_text)

    def header_for(self, template_t):
        return template_t

    def parse_template(self, template, expected):
        """
        Extract template name and arguments even in cases like
        'const QSet<QMap<QAction *, KIPI::Category> > &foo'.

        :return: (name, [args])
        """
        name, args = template.split("<", 1)
        name = name.split()[-1]
        text = args.rsplit(">", 1)[0]
        args = []
        bracket_level = 0
        left = 0
        for right, token in enumerate(text):
            if bracket_level <= 0 and token is ",":
                args.append(text[left:right].strip())
                left = right + 1
            elif token is "<":
                bracket_level += 1
            elif token is ">":
                bracket_level -= 1
        args.append(text[left:].strip())
        assert len(args) == expected, "Expected {} template arguments in '{}', got {}".format(expected, template, args)
        return name, args

    def expand(self, rule, cursor, text, sip):
        """
        Expand a template, and return the results via the sip.

        :param rule:            The rule requesting the expansion.
        :param cursor:          The item Cursor for whom the expansion is being performed.
                                This is typically a typed object, such as "QMap" or "QHash".
        :param text:            The item text to be expanded.
        :param sip:             The sip.

                                    - mt_parameter_helper: Tailored parameter handling. Rule
                                      writers can tailor the expansion of parameters using
                                      custom subclasses of GenerateMappedHelper.
        """
        expected_parameters = self.variables
        #
        # Extract the text forms even in cases like 'QSet<QMap<QAction *, KIPI::Category> >'.
        #
        text_type, text_args = self.parse_template(text, len(expected_parameters))
        #
        # We would like to be able to use clang type system to determine the HELD_AS etc, but the number of children of
        # the typedef is variable (i.e. the structure of an AST is not represented). Also, for example, int types are
        # not even included.
        #
        # So we proceed by get matching arrays of the clang template parameters and the corresponding texts.
        #
        clang_type = None
        clang_args = []
        #
        # We are only interested in things that can affect the type of the parameters.
        #
        tmp = [c for c in cursor.get_children() if c.kind not in [CursorKind.NAMESPACE_REF, CursorKind.UNEXPOSED_ATTR]]
        for c in tmp:
            if c.referenced:
                spelling = c.referenced.type.get_canonical().spelling
            else:
                spelling = c.type.get_canonical().spelling
            if spelling in text_args:
                clang_args.append(c)
            elif c.kind in [CursorKind.TEMPLATE_REF, CursorKind.TYPE_REF]:
                clang_type = c
        #
        # We only use the information if it matches the cases we understand (i.e. a non-trivial AST is implied).
        #
        if clang_type and len(clang_args) == len(text_args):
            pass
        else:
            if False:
                # Debug
                print("TEMPLATE BEGIN {}".format(text))
                print("    PARENT {}".format(clang_type.spelling))
                for i, c in enumerate(clang_args):
                    if clang_args[i].type.kind == TypeKind.INVALID:
                        tmp = clang_args[i].kind
                    else:
                        tmp = clang_args[i].type.kind
                    print("    CHILD{}".format(i), tmp, clang_args[i].spelling)
                print("TEMPLATE END")
            clang_args = [None] * len(expected_parameters)
        #
        # Compose the parent type, and the dicts for the parameters and a default declaration.
        #
        manual_types = sip.get("types", [None] * len(expected_parameters))
        manual_base_types = sip.get("base_types", [None] * len(expected_parameters))
        entries = {}
        parameters = []
        for i, parameter in enumerate(expected_parameters):
            actual_type = self.actual_type(manual_types[i], text_args[i], clang_args[i])
            base_type = self.base_type(manual_base_types[i], actual_type, clang_args[i])
            p = {
                "type": actual_type,
                "base_type": base_type,
            }
            clang_t = clang_args[i].type.get_canonical() if clang_args[i] else None
            entries[parameter] = self.helpers[parameter](p, clang_t)
            parameters.append(actual_type)
        text_args = ", ".join(text_args)
        #
        # Run the template handler...
        #
        if text_args.endswith(">"):
            text_args += " "
        mapped_type = "{}<{}>".format(text_type, text_args)
        trace = trace_generated_for(cursor, rule, ["{}({})".format(entries[p].cxx_t, entries[p].category)
                                                   for p in expected_parameters])
        code = self.expand_generic(text_type, entries)
        code = "%MappedType " + mapped_type + "\n{\n" + trace + code + "};\n"
        sip["modulecode"][mapped_type] = code


class DictExpander(AbstractExpander):

    def __init__(self, key_helper, value_helper):
        super(DictExpander, self).__init__([("key", key_helper), ("value", value_helper)])

    def expand_generic(self, template_t, entries):
        """
        Generic support for C++ types which map onto a Python dict, such as QMap<k, v> and
        QHash<k, v>. Either template parameter can be of any integral (int, long, enum) type
        or non-integral type, for example, QMap<int, QString>.

        :param template_t:      The name of the C++ template, e.g. "QMap".
        :param entries:         Dictionary describing the C++ template. Expected keys:

                                    key             Is the key integral, pointer or object?
                                    value           Is the value integral, pointer or object?
        """
        key_h = entries["key"]
        value_h = entries["value"]
        code = """
%TypeHeaderCode
#include <{header_h}>
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
    {template_t}<CxxkeyT, CxxvalueT>::const_iterator i = sipCpp->constBegin();
    {template_t}<CxxkeyT, CxxvalueT>::const_iterator end = sipCpp->constEnd();
    while (i != end) {
"""
        code += key_h.cxx_to_py("key", True, "i", "i")
        code += value_h.cxx_to_py("value", True, "i", "i")
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
    {template_t}<CxxkeyT, CxxvalueT> *dict = new {template_t}<CxxkeyT, CxxvalueT>();
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
        code = code.replace("{header_h}", self.header_for(template_t), 1)
        code = code.replace("{template_t}", template_t)
        code = code.replace("{key_t}", key_h.cxx_t)
        code = code.replace("{value_t}", value_h.cxx_t)
        return code


class ListExpander(AbstractExpander):

    def __init__(self, value_helper):
        super(ListExpander, self).__init__([("value", value_helper)])

    def expand_generic(self, template_t, entries):
        """
        Generic support for C++ types which map onto a Python list, such as QList<v> and
        QVector<v>. The template parameter can be of any integral (int, long, enum) type
        or non-integral type, for example, QList<int> or std::vector<QString>.

        :param template_t:      The name of the C++ template, e.g. "QList".
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
    // Create the Python list.
    PyObject *list = PyList_New(sipCpp->size());
    if (!list) {
        PyErr_Format(PyExc_TypeError, "unable to create a list");
        return 0;
    }

    // Set the list elements.
    Py_ssize_t i = 0;
    for (i = 0; i < (Py_ssize_t)sipCpp->size(); ++i) {
"""
        code += value_h.cxx_to_py("value", True, "sipCpp", "sipCpp")
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
    {template_t}<CxxvalueT> *list = new {template_t}<CxxvalueT>();
    list->reserve(PyList_GET_SIZE(sipPy));
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
        list->push_back("""
        code += value_h.insertable_cxx_value("value")
        code += """);
"""
        code += value_h.release_sip_helper("value")
        code += """    }
    *sipCppPtr = list;
    return sipGetState(sipTransferObj);
%End
"""
        code = code.replace("{header_h}", self.header_for(template_t), 1)
        code = code.replace("{template_t}", template_t)
        code = code.replace("{value_t}", value_h.cxx_t)
        return code


class SetExpander(AbstractExpander):

    def __init__(self, value_helper):
        super(SetExpander, self).__init__([("value", value_helper)])

    def expand_generic(self, template_t, entries):
        """
        Generic support for C++ types which map onto a Python set, such as
        QSet<v>. The template parameter can be of any integral (int, long,
        enum) type or non-integral type, for example, QSet<int> or
        QSet<QString>.

        :param template_t:      The name of the C++ template, e.g. "QSet".
        :param entries:         Dictionary describing the C++ template. Expected keys:

                                    value           Is the item integral, pointer or object?
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
    // Create the Python set.
    PyObject *set = PySet_New(NULL);
    if (!set) {
        PyErr_Format(PyExc_TypeError, "unable to create a set");
        return 0;
    }

    // Set the set elements.
    {template_t}<CxxvalueT>::const_iterator i = sipCpp->constBegin();
    {template_t}<CxxvalueT>::const_iterator end = sipCpp->constEnd();
    while (i != end) {
"""
        code += value_h.cxx_to_py("value", True, "i", "i")
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
    {template_t}<CxxvalueT> *set = new {template_t}<CxxvalueT>();
    set->reserve(PySet_GET_SIZE(sipPy));
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
        code = code.replace("{header_h}", self.header_for(template_t), 1)
        code = code.replace("{template_t}", template_t)
        code = code.replace("{value_t}", value_h.cxx_t)
        return code


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
        HeldAs.FLOAT:
            """        PyObject *{name} = PyFloat_FromDouble((double)*({cxx_i}));
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
        Cxx{name}T cxx{name} = reinterpret_cast<Cxx{name}T>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr));
""",
        HeldAs.OBJECT:
            """        int {name}State;
        Cxx{name}T *cxx{name} = reinterpret_cast<Cxx{name}T *>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr));
""",
        HeldAs.FLOAT:
            """        Cxx{name}T cxx{name} = (Cxx{name}T)PyFloat_AsDouble({name});
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

    def __init__(self, entry, clang_t):
        super(GenerateMappedHelper, self).__init__(entry["type"], clang_t, entry["base_type"])

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
            HeldAs.FLOAT:
                """            if (!PyFloat_Check({name})) {
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
            HeldAs.FLOAT:
                "",
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
            HeldAs.FLOAT: "cxx{name}",
        }
        code = options[self.category]
        code = code.replace("{name}", name)
        return code
