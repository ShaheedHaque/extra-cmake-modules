#
# Copyright 2017 by Shaheed Haque (srhaque@theiet.org)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA.
#
"""
SIP binding customisation for PyKF5.kio. This modules describes:

    * Supplementary SIP file generator rules.
"""

from clang.cindex import TypeKind


def variable_rewrite_array(container, variable, sip, matcher):
    base_type, indices = sip["decl"].split("[", 1)
    indices = "[" + indices
    #
    # If all the indices are empty, as in [][][], then just convert to ***.
    #
    if indices == "[]":
        sip["decl"] = base_type + "*"
        return
    #
    # We only handle simple 1D arrays of byte values.
    #
    if variable.type.kind != TypeKind.CONSTANTARRAY:
        return
    element_type = variable.type.element_type.get_canonical()
    if element_type.kind in [TypeKind.CHAR_S, TypeKind.CHAR_U, TypeKind.SCHAR, TypeKind.UCHAR]:
        sip["decl"] = "SIP_PYBUFFER"
        code = """
{
%GetCode
    char *cxxvalue = (char *)&sipCpp->{name}[0];

    // Create the Python buffer.
    Py_ssize_t element_count = {element_count};
    sipPy = PyByteArray_FromStringAndSize(cxxvalue, element_count);
%End

%SetCode
    char *cxxvalue = (char *)&sipCpp->{name}[0];
    Py_ssize_t element_count = {element_count};
    const char *name = "{name}";

    if (!PyByteArray_Check(sipPy)) {
        PyErr_Format(PyExc_TypeError, "expected buffer");
        sipErr = 1;
    }

    // Convert the buffer to C++.
    if (!sipErr) {
        if (PyByteArray_GET_SIZE(sipPy) != element_count) {
            PyErr_Format(PyExc_ValueError, "'%s' must have length %ld", name, element_count);
            sipErr = 1;
        } else {
            memcpy(cxxvalue, PyByteArray_AsString(sipPy), element_count);
        }
    }
%End
}"""
    elif element_type.kind in [TypeKind.USHORT, TypeKind.UINT, TypeKind.ULONG, TypeKind.ULONGLONG, TypeKind.UINT128,
                               TypeKind.SHORT, TypeKind.INT, TypeKind.LONG, TypeKind.LONGLONG, TypeKind.INT128,
                               TypeKind.ENUM]:
        sip["decl"] = base_type + "*"
        sip["decl"] = "SIP_PYTUPLE"
        code = """
{
%GetCode
    typedef {cxx_t} CxxvalueT;
    CxxvalueT *cxxvalue = (CxxvalueT *)&sipCpp->{name}[0];
    Py_ssize_t element_count = {element_count};
    int sipErr = 0;

    // Create the Python tuple.
    PyObject *tuple = PyTuple_New(element_count);
    if (!tuple) {
        PyErr_Format(PyExc_TypeError, "unable to create a tuple");
        sipErr = 1;
    }

    // Populate the tuple elements.
    if (!sipErr) {
        Py_ssize_t i = 0;
        for (i = 0; i < element_count; ++i) {
#if PY_MAJOR_VERSION >= 3
            PyObject *value = PyLong_FromLong((long)cxxvalue[i]);
#else
            PyObject *value = PyInt_FromLong((long)cxxvalue[i]);
#endif
            if (value == NULL) {
                PyErr_Format(PyExc_TypeError, "cannot insert value into tuple");
                Py_XDECREF(value);
                Py_DECREF(tuple);
                sipErr = 1;
            } else {
                PyTuple_SET_ITEM(tuple, i, value);
            }
        }
    }
    sipPy = sipErr ? tuple : NULL;
%End

%SetCode
    typedef {cxx_t} CxxvalueT;
    CxxvalueT *cxxvalue = (CxxvalueT *)&sipCpp->{name}[0];
    Py_ssize_t element_count = {element_count};
    const char *name = "{name}";

    if (!PyTuple_Check(sipPy)) {
        PyErr_Format(PyExc_TypeError, "expected tuple");
        sipErr = 1;
    }

    // Convert the tuple to C++.
    if (!sipErr) {
        if (PyTuple_GET_SIZE(sipPy) != element_count) {
            PyErr_Format(PyExc_ValueError, "'%s' must have length %ld", name, element_count);
            sipErr = 1;
        } else {
            Py_ssize_t i = 0;
            for (i = 0; i < element_count; ++i) {
                PyObject *value = PyTuple_GetItem(sipPy, i);
#if PY_MAJOR_VERSION >= 3
                cxxvalue[i] = (CxxvalueT)PyLong_AsLong(value);
#else
                cxxvalue[i] = (CxxvalueT)PyInt_AsLong(value);
#endif
            }
        }
    }
%End
}"""
    else:
        return
    code = code.replace("{cxx_t}", element_type.spelling)
    code = code.replace("{element_count}", str(variable.type.element_count))
    code = code.replace("{name}", sip["name"])
    sip["code"] = code


def variable_fully_qualify(container, variable, sip, matcher):
    sip["decl"] = "KNTLM::" + sip["decl"]


def variable_rules():
    return [
        #
        # Emit code for fixed arrays.
        #
        ["KNTLM::.*", ".*", ".*\[.+\]", variable_rewrite_array],
        #
        # Fully-qualify.
        #
        ["KNTLM::.*", ".*", "SecBuf.*", variable_fully_qualify],
    ]
