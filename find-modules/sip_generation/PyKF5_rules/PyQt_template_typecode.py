#=============================================================================
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
#=============================================================================
"""
SIP binding custom type-related code for PyQt-template classes.
"""

import inspect
import os

from clang.cindex import CursorKind, TypeKind


class HELD_AS:
    """
    Items are held either as integral values, pointer values or objects. The
    Python interchange logic depends on this.

    TODO: In the case of pointers, we also need to know whether a specialised
    pointer type is in use (or just "*").
    """
    INTEGRAL = "INTEGRAL"
    POINTER = "POINTER"
    OBJECT = "OBJECT"


def _declare_aliases(name, entry, category, need_string=False):
    """
    By creating local definitions at the top of each section of emitted output, the rest of the expanded template
    is a constant. This makes it easier to see the effect of any changes using "diff".
    """
    cxx_t = entry[name]["type"]
    sip_t = entry[name]["base_type"]
    #
    # This may be a mapped type.
    #
    is_mapped_type = ("<" in sip_t)
    if is_mapped_type:
        sip_t = "sipFindMappedType(\"{}\")".format(sip_t)
    else:
        sip_t = sip_t.replace("::", "_")
        sip_t = "sipType_" + sip_t
    if category in [HELD_AS.POINTER, HELD_AS.OBJECT]:
        #
        # If the sipTypeDef needs a run-time lookup using sipFindMappedType, can convert that into a one-off cost
        # using a static.
        #
        if is_mapped_type:
            code = """    static const sipTypeDef *gen{name}T = NULL;
    if (gen{name}T == NULL) {
        gen{name}T = {sip_t};
    }
    typedef {cxx_t} Cxx{name}T;
"""
        else:
            code = """    const sipTypeDef *gen{name}T = {sip_t};
    typedef {cxx_t} Cxx{name}T;
"""
    else:
        code = ""
    if need_string:
        code += """    const char *cxx{name}S = "{cxx_t}";
"""
    code = code.replace("{name}", name)
    code = code.replace("{cxx_t}", cxx_t)
    code = code.replace("{sip_t}", sip_t)
    return code


def _from(name, i_value, po_value, category):
    if category == HELD_AS.INTEGRAL:
        code = """#if PY_MAJOR_VERSION >= 3
        PyObject *{name} = PyLong_FromLong((long){i_value});
#else
        PyObject *{name} = PyInt_FromLong((long){i_value});
#endif
"""
    elif category in [HELD_AS.POINTER]:
        code = """        Cxx{name}T {name}_ = {po_value};
        PyObject *{name} = sipConvertFromNewType({name}_, gen{name}T, sipTransferObj);
"""
    elif category in [HELD_AS.OBJECT]:
        code = """        Cxx{name}T *{name}_ = new Cxx{name}T({po_value});
        PyObject *{name} = sipConvertFromNewType({name}_, gen{name}T, sipTransferObj);
"""
    code = code.replace("{name}", name)
    code = code.replace("{i_value}", i_value)
    code = code.replace("{po_value}", po_value)
    return code


def _decref(name, category):
    if category == HELD_AS.INTEGRAL:
        code = """            Py_DECREF({name});
"""
    elif category in [HELD_AS.POINTER, HELD_AS.OBJECT]:
        code = """            Py_XDECREF({name});
"""
    code = code.replace("{name}", name)
    return code


def _check(name, category):
    if category == HELD_AS.INTEGRAL:
        code = """#if PY_MAJOR_VERSION >= 3
            if (!PyLong_Check({name})) {
                return 0;
            }
#else
            if (!PyInt_Check({name})) {
                return 0;
            }
#endif
"""
    elif category in [HELD_AS.POINTER, HELD_AS.OBJECT]:
        code = """            if (!sipCanConvertToType({name}, gen{name}T, SIP_NOT_NONE)) {
                return 0;
            }
"""
    code = code.replace("{name}", name)
    return code


def _to(name, category):
    if category == HELD_AS.INTEGRAL:
        code = """
#if PY_MAJOR_VERSION >= 3
        Cxx{name}T {name}_ = (Cxx{name}T)PyLong_AsLong({name});
#else
        Cxx{name}T {name}_ = (Cxx{name}T)PyInt_AsLong({name});
#endif
"""
    elif category in [HELD_AS.POINTER]:
        code = """        int {name}State;
        Cxx{name}T {name}_ = NULL;
        {name}_ = reinterpret_cast<Cxx{name}T>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr));
"""
    elif category in [HELD_AS.OBJECT]:
        code = """        int {name}State;
        Cxx{name}T *{name}_ = NULL;
        {name}_ = reinterpret_cast<Cxx{name}T *>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr));
"""
    code = code.replace("{name}", name)
    return code


def _release(name, category):
    if category == HELD_AS.INTEGRAL:
        code = ""
    elif category in [HELD_AS.POINTER, HELD_AS.OBJECT]:
        code = """        sipReleaseType({name}_, gen{name}T, {name}State);
"""
    code = code.replace("{name}", name)
    return code


def _insert(name, category):
    if category == HELD_AS.INTEGRAL:
        code = "{name}_"
    elif category == HELD_AS.POINTER:
        code = "{name}_"
    elif category == HELD_AS.OBJECT:
        code = "*{name}_"
    code = code.replace("{name}", name)
    return code


def _cfttc_expand_dict(typedef, sip, entry):
    """
    Generic support for C++ types which map onto a Python dict, such as QMap<k, v> and
    QHash<k, v>. Either template parameter can be of any integral (int, long, enum) type
    or non-integral type, for example, QMap<int, QString>.

    :param typedef:         The type, such as "QMap" or "QHash".
    :param entry:           The dictionary entry. Expected keys:

                                name            Optional. Name of the typedef.
                                key             Type of key.
                                value           Type of value.
                                key_category    Is it a long or similar?
                                value_category  Is it a long or similar?

                            The key and value have the following keys:

                                type            The type of the item.
                                base_type       The base type of the item, different from type in the case of a pointer.
                                held_as         Is the item integral, pointer
                                                or object?
    """
    key_category = entry["key"]["held_as"]
    value_category = entry["value"]["held_as"]
    code = """
%TypeHeaderCode
#include <{cxx_type}>
%End
%ConvertFromTypeCode
    // These definitions make it easier to track changes in generated output.
"""
    code += _declare_aliases("key", entry, key_category)
    code += _declare_aliases("value", entry, value_category)
    code += """    // Create the dictionary.
    PyObject *dict = PyDict_New();
    if (!dict) {
        return 0;
    }

    // Set the dictionary elements.
    {cxx_type}<CxxkeyT, CxxvalueT>::const_iterator i = sipCpp->constBegin();
    {cxx_type}<CxxkeyT, CxxvalueT>::const_iterator end = sipCpp->constEnd();
    while (i != end) {
"""
    code += _from("key", "i.key()", "i.key()", key_category)
    code += _from("value", "i.value()", "i.value()", value_category)
    #
    # Error handling assumptions:
    #
    #   - a failed "new" throws (or, not compliant, return NULL).
    #   - the good path should be as fast as possible, error recovery can be slow.
    #
    code += """
        if (key == NULL || value == NULL || PyDict_SetItem(dict, key, value) < 0) {
            if (key && value) {
                Py_DECREF(dict);
            }
"""
    code += _decref("key", key_category) + _decref("value", value_category)
    if key_category == HELD_AS.OBJECT:
        code += """            delete key;
"""
    if value_category == HELD_AS.OBJECT:
        code += """            delete value;
"""
    code += """            return 0;
        }
        Py_DECREF(key);
        Py_DECREF(value);
        ++i;
    }
    return dict;
%End
%ConvertToTypeCode
    // These definitions make it easier to track changes in generated output.
"""
    code += _declare_aliases("key", entry, key_category, need_string=True)
    code += _declare_aliases("value", entry, value_category, need_string=True)
    code += """    PyObject *key;
    PyObject *value;
    Py_ssize_t i = 0;

    // Check the type if that is all that is required.
    if (sipIsErr == NULL) {
        if (!PyDict_Check(sipPy)) {
            return 0;
        }

        while (PyDict_Next(sipPy, &i, &key, &value)) {
"""
    code += _check("key", key_category)
    code += _check("value", value_category)
    code += """        }
        return 1;
    } else if (*sipIsErr) {
        return 0;
    }

    {cxx_type}<CxxkeyT, CxxvalueT> *dict = new {cxx_type}<CxxkeyT, CxxvalueT>();
    while (PyDict_Next(sipPy, &i, &key, &value)) {
"""
    code += _to("key", key_category)
    code += _to("value", value_category)
    code += """
        if (*sipIsErr) {
            if (key == NULL) {
                PyErr_Format(PyExc_TypeError, "a dict key has type '%s' but '%s' is expected",
                             Py_TYPE(key)->tp_name, cxxkeyS);
            }
            if (value == NULL) {
                PyErr_Format(PyExc_TypeError, "a dict value has type '%s' but '%s' is expected",
                             Py_TYPE(value)->tp_name, cxxvalueS);
            }
"""
    code += _release("key", key_category)
    code += _release("value", value_category)
    code += """            delete dict;
            return 0;
        }
        dict->insert("""
    code += _insert("key", key_category) + ", " + _insert("value", value_category)
    code += """);
"""
    code += _release("key", key_category)
    code += _release("value", value_category)
    code += """    }
    *sipCppPtr = dict;
    return sipGetState(sipTransferObj);
%End
"""
    code = code.replace("{cxx_type}", entry["template"])
    key_t = entry["key"]["type"]
    code = code.replace("{key_t}", key_t)
    value_t = entry["value"]["type"]
    code = code.replace("{value_t}", value_t)
    sip["code"] = code
    sip["name"] = entry.get("name", sip["name"])


def _cfttc_expand_list(typedef, sip, entry):
    """
    Generic support for C++ types which map onto a Python list, such as QList<v> and
    QVector<v>. The template parameter can be of any integral (int, long, enum) type
    or non-integral type, for example, QList<int> or QList<QString>.

    :param typedef:         The type, such as "QList" or "QVector".
    :param entry:           The dictionary entry. Expected keys:

                                name            Optional. Name of the typedef.
                                key             Key description dict.
                                value           Value description dict.

                            The value has the following keys:

                                type            The type of the item.
                                base_type       The base type of the item, different from type in the case of a pointer.
                                held_as         Is the item integral, pointer
                                                or object?
    """
    value_category = entry["value"]["held_as"]
    code = """
%TypeHeaderCode
#include <{cxx_type}>
%End
%ConvertFromTypeCode
    // These definitions make it easier to track changes in generated output.
"""
    code += _declare_aliases("value", entry, value_category)
    code += """    // Create the list.
    PyObject *list = PyList_New(sipCpp->size());
    if (!list) {
        return 0;
    }

    // Set the list elements.
    Py_ssize_t i = 0;
    for (i = 0; i < sipCpp->size(); ++i) {
"""
    code += _from("value", "sipCpp->value(i)", "sipCpp->at(i)", value_category)
    code += """
        if (value == NULL || PyList_SetItem(list, i, value) < 0) {
            if (value) {
                Py_DECREF(list);
            }
"""
    code += _decref("value", value_category)
    code += """            return 0;
        }
    }
    return list;
%End
%ConvertToTypeCode
    // These definitions make it easier to track changes in generated output.
"""
    code += _declare_aliases("value", entry, value_category, need_string=True)
    code += """    PyObject *value;
    Py_ssize_t i = 0;

    // Check the type if that is all that is required.
    if (sipIsErr == NULL) {
        if (!PyList_Check(sipPy)) {
            return 0;
        }

        for (i = 0; i < PyList_GET_SIZE(sipPy); ++i) {
            value = PyList_GetItem(sipPy, i);
"""
    code += _check("value", value_category)
    code += """        }
        return 1;
    } else if (*sipIsErr) {
        return 0;
    }

    {cxx_type}<CxxvalueT> *list = new {cxx_type}<CxxvalueT>();
    for (i = 0; i < PyList_GET_SIZE(sipPy); ++i) {
        value = PyList_GetItem(sipPy, i);
"""
    code += _to("value", value_category)
    code += """
        if (*sipIsErr) {
            if (value == NULL) {
                PyErr_Format(PyExc_TypeError, "list value %d has type '%s' but '%s' is expected", i,
                             Py_TYPE(value)->tp_name, cxxvalueS);
            }
"""
    code += _release("value", value_category)
    code += """            delete list;
            return 0;
        }
        list->append("""
    code += _insert("value", value_category)
    code += """);
"""
    code += _release("value", value_category)
    code += """    }
    *sipCppPtr = list;
    return sipGetState(sipTransferObj);
%End
"""
    code = code.replace("{cxx_type}", entry["template"])
    value_t = entry["value"]["type"]
    code = code.replace("{value_t}", value_t)
    sip["code"] = code
    sip["name"] = entry.get("name", sip["name"])


def _cfttc_expand_set(typedef, sip, entry):
    """
    Generic support for QSet<v>. The template parameter can be of any
    integral (int, long, enum) type or non-integral type, for example,
    QSet<int> or QSet<QString>.

    :param typedef:         The type, such as "QSet".
    :param entry:           The dictionary entry. Expected keys:

                                value           Value description dict.

                            The value has the following keys:

                                type            The type of the item.
                                base_type       The base type of the item, different from type in the case of a pointer.
                                held_as         Is the item integral, pointer
                                                or object?
    """
    value_category = entry["value"]["held_as"]
    code = """
%TypeHeaderCode
#include <{cxx_type}>
%End
%ConvertFromTypeCode
    // These definitions make it easier to track changes in generated output.
"""
    code += _declare_aliases("value", entry, value_category, need_string=True)
    code += """    // Create the set.
    PyObject *set = PySet_New();
    if (!set) {
        return 0;
    }

    // Set the set elements.
    {cxx_type}<CxxvalueT>::const_iterator i = sipCpp->constBegin();
    {cxx_type}<CxxvalueT>::const_iterator end = sipCpp->constEnd();
    while (i != end) {
"""
    code += _from("value", "sipCpp->value(i)", "sipCpp->at(i)", value_category)
    code += """
        if (value == NULL || PySet_Add(set, value) < 0) {
            if (value) {
                Py_DECREF(set);
            }
"""
    code += _decref("value", value_category)
    code += """            return 0;
        }
    }
    return set;
%End
%ConvertToTypeCode
    // These definitions make it easier to track changes in generated output.
"""
    code += _declare_aliases("value", entry, value_category, need_string=True)
    code += """    PyObject *value;
    Py_ssize_t i = 0;

    // Check the type if that is all that is required.
    if (sipIsErr == NULL) {
        if (!PyList_Check(sipPy)) {
            return 0;
        }

        for (i = 0; i < PySet_GET_SIZE(sipPy); ++i) {
            value = PySet_GetItem(sipPy, i);
"""
    code += _check("value", value_category)
    code += """        }
        return 1;
    } else if (*sipIsErr) {
        return 0;
    }
"""
    if value_category == HELD_AS.INTEGRAL:
        code += """
    {cxx_type}<CxxvalueT> *set = new {cxx_type}<CxxvalueT>();
"""
    else:
        code += """
    typedef QExplicitlySharedDataPointer<cxxvalueT> ptr_t;
    {cxx_type}<ptr_t> *set = new {cxx_type}<ptr_t>;
"""
    code += """
    for (i = 0; i < PySet_GET_SIZE(sipPy); ++i) {
        value = PySet_GetItem(sipPy, i);
"""
    code += _to("value", value_category)
    code += """
        if (*sipIsErr) {
            if (value == NULL) {
                PyErr_Format(PyExc_TypeError, "a set value has type '%s' but '%s' is expected",
                             Py_TYPE(value)->tp_name, cxxvalueS);
            }
"""
    code += _release("value", value_category)
    code += """            delete set;
            return 0;
        }
        set->insert("""
    code += _insert("value", value_category)
    code += """);
"""
    code += _release("value", value_category)
    code += """    }
    *sipCppPtr = set;
    return sipGetState(sipTransferObj);
%End
"""
    code = code.replace("{cxx_type}", entry["template"])
    value_t = entry["value"]["type"]
    code = code.replace("{value_t}", value_t)
    sip["code"] = code
    sip["name"] = entry.get("name", sip["name"])


def _expand_template(typedef, sip, expected_parameters, fn):
    """
    Generate code for a templated type.

    :param typedef:                         The clang object.
    :param sip:                             The sip dict.
    :param expected_parameters:             What template parameters are we expecting?
    :param fn:                              The template itself.
    """
    def categorise(template_text, template_parameter):
        """
        We would like to be able to use clang type system to determine the HELD_AS, but the number of children of the
        typedef is so inexplicible as to make this impossible at present. For example, int types are not even included.

        TODO: When we figure this out, get rid of this horrid heuristic.

        :param template_text:               The text from the source code.
        :param template_parameter:          The clang object.
        :return: the storage type of the parameter.
        """
        if template_text.endswith(("Ptr", "*", "&")):
            return HELD_AS.POINTER
        if template_text.startswith(("QSharedPointer", "QExplicitlySharedDataPointer")):
            return HELD_AS.POINTER
        if template_parameter:
            type_kind = template_parameter.type.get_canonical().kind
            if type_kind == TypeKind.RECORD:
                return HELD_AS.OBJECT
            elif type_kind in [TypeKind.POINTER, TypeKind.MEMBERPOINTER]:
                return HELD_AS.POINTER
            elif type_kind in [TypeKind.BOOL, TypeKind.USHORT, TypeKind.UINT, TypeKind.ULONG, TypeKind.ULONGLONG,
                               TypeKind.UINT128, TypeKind.SHORT, TypeKind.INT, TypeKind.LONG, TypeKind.LONGLONG,
                               TypeKind.INT128, TypeKind.ENUM]:
                return HELD_AS.INTEGRAL
            else:
                raise AssertionError(_("Unexpected template parameter type {} for {}").format(type_kind, template_text))
        if template_text in ["int", "long"]:
            return HELD_AS.INTEGRAL
        return HELD_AS.OBJECT

    def actual_type(manual_override, template_text, template_parameter):
        """
        We would like to be able to use clang type system to determine underlying type, but the number of children of
        the typedef is so inexplicible as to make this impossible at present.  For example, int types are not even
        included.

        TODO: When we figure this out, get rid of this horrid heuristic.

        :param manual_override:             The user knows best.
        :param template_text:               The text from the source code.
        :param template_parameter:          The clang object.
        :return: the base_type of the parameter.
        """
        if manual_override:
            return manual_override
        if template_parameter:
            tmp = template_parameter.type.get_canonical().spelling
            if template_text.endswith(("*", "&")):
                tmp += " " + template_text[-1]
            return tmp
        return template_text

    def base_type(manual_override, template_text, template_parameter):
        """
        We would like to be able to use clang type system to determine underlying type, but the number of children of
        the typedef is so inexplicible as to make this impossible at present.  For example, int types are not even
        included.

        TODO: When we figure this out, get rid of this horrid heuristic.

        :param manual_override:             The user knows best.
        :param template_text:               The text from the source code.
        :param template_parameter:          The clang object.
        :return: the base_type of the parameter.
        """
        if manual_override:
            return manual_override
        if template_parameter:
            return template_parameter.type.get_canonical().spelling
        if template_text.endswith("Ptr"):
            template_text = template_text[:-3]
            if template_text.endswith("::"):
                template_text = template_text[:-2]
        elif template_text.endswith(("*", "&")):
            template_text = template_text[:-1].strip()
        return template_text

    #
    # We would like to be able to use clang type system to determine the HELD_AS etc, but the number of children of the
    # typedef is variable (i.e. the structure of the AST is not present). Also, for example, int types are not even
    # included.
    #
    # So we proceed by get matching arrays of the clang template parameters and the corresponding texts.
    #
    # Start with the clang type system...
    #
    children = list(typedef.get_children())
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
    assert parent.kind == CursorKind.TEMPLATE_REF, _("Parent {} has bad kind {}").format(parent.spelling, parent.kind)
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
    assert len(decls) == len(expected_parameters), _("Cannot extract decls from {}").format(declaration)
    #
    # Compose the parent type, and the dicts for the parameters and a default declaration.
    #
    sip.setdefault("types", [None] * len(expected_parameters))
    sip.setdefault("base_types", [None] * len(expected_parameters))
    entry = {}
    parameters = []
    for i, parameter in enumerate(expected_parameters):
        p = {}
        p["type"] = actual_type(sip["types"][i], decls[i], types[i])
        p["base_type"] = base_type(sip["base_types"][i], p["type"], types[i])
        p["held_as"] = categorise(p["type"], types[i])
        entry[parameter] = p
        parameters.append(p["type"])
    parameters = ", ".join(parameters)
    if parameters.endswith(">"):
        parameters += " "
    sip["decl"] = "{}<{}>".format(parent.spelling, parameters)
    #
    # Run the handler...
    #
    entry["code"] = fn
    entry["template"] = parent.spelling
    fn_file = os.path.basename(inspect.getfile(fn))
    trace = "// Generated (by {}:{}): {}\n".format(fn_file, fn.__name__, {k:v for (k,v) in entry.items() if k != "code"})
    fn(typedef, sip, entry)
    sip["code"] = trace + sip["code"]


def dict_cfttc(container, typedef, sip, matcher):
    _expand_template(typedef, sip, ["key", "value"], _cfttc_expand_dict)


def list_cfttc(container, typedef, sip, matcher):
    _expand_template(typedef, sip, ["value"], _cfttc_expand_list)


def set_cfttc(container, typedef, sip, matcher):
    _expand_template(typedef, sip, ["value"], _cfttc_expand_set)
