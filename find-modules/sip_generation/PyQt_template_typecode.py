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

def _from(name, type, value, category):
    if category == HELD_AS.INTEGRAL:
        code = """
#if PY_MAJOR_VERSION >= 3
        PyObject *{name} = PyLong_FromLong(({type}){value});
#else
        PyObject *{name} = PyInt_FromLong(({type}){value});
#endif"""
    elif category in [HELD_AS.POINTER, HELD_AS.OBJECT]:
        code = """
    {type} *{name}_ = new {type}({value});
    PyObject *{name} = sipConvertFromNewType({name}_, sipType_{type}, sipTransferObj);
"""
    code = code.replace("{name}", name)
    code = code.replace("{type}", type)
    code = code.replace("{value}", value)
    return code


def _decref(name, category):
    if category == HELD_AS.INTEGRAL:
        code = """
        Py_DECREF({name});
"""
    elif category == HELD_AS.POINTER:
        code = """
    if ({name}) {
        Py_DECREF({name});
    } else {
        delete {name}_;
    }"""
    elif category == HELD_AS.OBJECT:
        code = """
    Py_XDECREF({name});"""
    code = code.replace("{name}", name)
    return code


def _check(name, type, category):
    if category == HELD_AS.INTEGRAL:
        code = """
#if PY_MAJOR_VERSION >= 3
        if (!PyLong_Check({name})) {
            return 0;
        }
#else
        if (!PyInt_Check({name})) {
            return 0;
        }
#endif"""
    elif category in [HELD_AS.POINTER, HELD_AS.OBJECT]:
        code = """
    if (!sipCanConvertToType({name}, sipType_{type}, SIP_NOT_NONE)) {
        return 0;
    }"""
    code = code.replace("{name}", name)
    code = code.replace("{type}", type)
    return code


def _to(name, type, category):
    if category == HELD_AS.INTEGRAL:
        code = """
#if PY_MAJOR_VERSION >= 3
        {type} {name}_ = ({type})PyLong_AsLong({name});
#else
        {type} {name}_ = ({type})PyInt_AsLong({name});
#endif"""
    elif category in [HELD_AS.POINTER, HELD_AS.OBJECT]:
        code = """
    int {name}State;
    {type} *{name}_ = reinterpret_cast<{type} *>(sipConvertToType({name}, sipType_{type}, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr));"""
    code = code.replace("{name}", name)
    code = code.replace("{type}", type)
    return code


def _release(name, type, category):
    if category == HELD_AS.INTEGRAL:
        code = ""
    elif category in [HELD_AS.POINTER, HELD_AS.OBJECT]:
        code = """
    sipReleaseType({name}_, sipType_{type}, {name}State);"""
    code = code.replace("{name}", name)
    code = code.replace("{type}", type)
    return code


def _insert(name, type, category):
    if category == HELD_AS.INTEGRAL:
        code = "({type}){name}_"
    elif category == HELD_AS.POINTER:
        code = "*(new ptr_t({name}_))"
    elif category == HELD_AS.OBJECT:
        code = "*{name}_"
    code = code.replace("{name}", name)
    code = code.replace("{type}", type)
    return code


def QList_cfttc(container, sip, entry):
    """
    Generic support for QList<v>. The template parameter can be of any
    integral (int, long, enum) type or non-integral type, for example,
    QList<int> or QList<QString>.

    :param entry:           The dictionary entry. Expected keys:

                                key             Key description dict.
                                value           Value description dict.

                            Each of key and value have the following keys:

                                type            The type of the item.
                                held_as         Is the item integral, pointer
                                                or object?
                                ptr             Any custom pointer type.
    """
    value_category = entry["value"]["held_as"]
    code = "// {}".format(entry)
    code += """
%ConvertFromTypeCode
    // Create the dictionary.
    PyObject *l = PyList_New();
    if (!l) {
        return NULL;
    }
    if (!sipCpp) {
        return l;
    }

    // Set the list elements.
    for (int i = 0; i < sipCpp->size(); ++i) {"""
    if value_category == HELD_AS.INTEGRAL:
        code += _from("value", "{value_t}", "sipCpp->value(i)", value_category)
    else:
        code += _from("value", "{value_t}", "sipCpp->at(i)", value_category)
    code += """
        if (value == NULL || PyList_SetItem(l, i, value) < 0) {
            Py_DECREF(l);"""
    code += _decref("value", value_category)
    code += """
            return NULL;
        }
    }
    return l;
%End
%ConvertToTypeCode
    PyObject *value;
    SIP_SSIZE_T i = 0;

    // Check the type if that is all that is required.
    if (sipIsErr == NULL) {
        if (!PyList_Check(sipPy)) {
            return 0;
        }

        for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i) {
            value = PyList_GetItem(sipPy, i);"""
    code += _check("value", "{value_t}", value_category)
    code += """
        }
        return 1;
    }
    """
    if value_category == HELD_AS.INTEGRAL:
        code += """
    QList<{value_t}> *ql = new QList<{value_t}>;"""
    else:
        code += """
    typedef QExplicitlySharedDataPointer<{value_t}> ptr_t;
    QList<ptr_t> *ql = new QList<ptr_t>;"""
    code += """for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i) {
        value = PyList_GetItem(sipPy, i);"""
    code += _to("value", "{value_t}", value_category)
    code += """
        if (*sipIsErr) {"""
    code += _release("value", "{value_t}", value_category)
    code += """
            delete ql;
            return 0;
        }
        ql->append("""
    code += _insert("value", "{value_t}", value_category)
    code += ");"
    code += _release("value", "{value_t}", value_category)
    code += """
    }
    *sipCppPtr = ql;
    return sipGetState(sipTransferObj);
%End
"""
    code = code.replace("{value_t}", entry["value"]["type"])
    sip["code"] = code


def QMap_cfttc(container, sip, entry):
    """
    Generic support for QMap<k, v>. Either template parameter can be of any
    integral (int, long, enum) type or non-integral type, for example,
    QMap<int, QString>.

    :param entry:           The dictionary entry. Expected keys:

                                key_t       Type of key.
                                value_t     Type of value.
                                key_category    Is it a long or similar?
                                value_category  Is it a long or similar?
    """
    key_category = entry["key"]["held_as"]
    value_category = entry["value"]["held_as"]
    code = "// {}".format(entry)
    code += """
%ConvertFromTypeCode
    // Create the dictionary.
    PyObject *d = PyDict_New();
    if (!d) {
        return NULL;
    }
    if (!sipCpp) {
        return d;
    }

    // Set the dictionary elements.
    QMap<{key_t}, {value_t}>::const_iterator i = sipCpp->constBegin();
    while (i != sipCpp->constEnd()) {"""
    code += _from("value", "{value_t}", "i.value()", value_category) + _from("key", "{key_t}", "i.key()", key_category)
    code += """
        if (key == NULL || value == NULL || PyDict_SetItem(d, key, value) < 0) {
            Py_DECREF(d);"""
    code += _decref("key", key_category) + _decref("value", value_category)
    code += """
            return NULL;
        }
        Py_DECREF(key);
        Py_DECREF(value);
        ++i;
    }
    return d;
%End
%ConvertToTypeCode
    PyObject *key;
    PyObject *value;
    SIP_SSIZE_T i = 0;

    // Check the type if that is all that is required.
    if (sipIsErr == NULL) {
        if (!PyDict_Check(sipPy)) {
            return 0;
        }

        while (PyDict_Next(sipPy, &i, &key, &value)) {"""
    code += _check("key", "{key_t}", key_category) + _check("value", "{value_t}", value_category)
    code += """
        }
        return 1;
    }

    QMap<{key_t}, {value_t}> *qm = new QMap<{key_t}, {value_t}>;
    while (PyDict_Next(sipPy, &i, &key, &value)) {"""
    code += _to("key", "{key_t}", key_category) + _to("value", "{value_t}", value_category)
    code += """
        if (*sipIsErr) {"""
    code += _release("key", "{key_t}", key_category) + _release("value", "{value_t}", value_category)
    code += """
            delete qm;
            return 0;
        }
        qm->insert("""
    code += _insert("key", "{key_t}", key_category) + ", " + _insert("value", "{value_t}", value_category)
    code += ");"
    code += _release("key", "{key_t}", key_category) + _release("value", "{value_t}", value_category)
    code += """
    }
    *sipCppPtr = qm;
    return sipGetState(sipTransferObj);
%End
"""
    code = code.replace("{key_t}", entry["key"]["type"])
    code = code.replace("{value_t}", entry["value"]["type"])
    sip["code"] = code
