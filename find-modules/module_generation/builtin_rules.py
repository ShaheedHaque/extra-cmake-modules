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
Rules which ameliorate some of the shortcomings of SIP.

The main public members of this module are intended to be used in a
composable manner. For example, a variable array which is also extern
could be handled by calling @see variable_rewrite_array_nonfixed() and then
@see variable_rewrite_extern().
"""
import gettext
import logging
import re
from clang.cindex import CursorKind, StorageClass, TypeKind

import clangcparser
import rule_helpers
import utils
from utils import trace_generated_for, HeldAs
from templates.methodcode import function_uses_templates

logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _


MAPPED_TYPE_RE = re.compile(".*<.*")


class RewriteArrayHelper(HeldAs):
    def cxx_to_py_template(self, name, cxx_v, cxx_to_py_value):
        options = {
            HeldAs.INTEGER:
                """        {name} = {cxx_to_py_value};
""",
            HeldAs.FLOAT:
                """        {name} = {cxx_to_py_value};
""",
            HeldAs.POINTER:
                """    int {name}State;
        Cxx{name}T cxx{name} = {cxx_to_py_value};
""",
            HeldAs.OBJECT:
                """    int {name}State;
        Cxx{name}T *cxx{name} = {cxx_to_py_value};
""",
        }

        code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{cxx_v}", cxx_v)
        code = code.replace("{cxx_to_py_value}", cxx_to_py_value)
        return code

    def py_to_cxx_template(self, name, py_v, py_to_cxx_value):
        options = {
            HeldAs.INTEGER:
                """    {cxx_v} = {py_to_cxx_value};
""",
            HeldAs.FLOAT:
                """    {cxx_v} = {py_to_cxx_value};
""",
            HeldAs.POINTER:
                """    int {name}State;
        Cxx{name}T cxx{name} = {py_to_cxx_value};
""",
            HeldAs.OBJECT:
                """    int {name}State;
        Cxx{name}T *cxx{name} = {py_to_cxx_value};
""",
        }

        code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{cxx_v}", py_v)
        code = code.replace("{py_to_cxx_value}", py_to_cxx_value)
        return code

    def py_to_cxx_value(self, name, py_v, transfer):
        """An expression converting the named C++ value to Python."""
        options = {
            HeldAs.INTEGER:
                """(
#if PY_MAJOR_VERSION >= 3
    (Cxx{name}T)PyLong_AsLong({name})
#else
    (Cxx{name}T)PyInt_AsLong({name})
#endif
)""",
            HeldAs.FLOAT:
                "(Cxx{name}T)PyFloat_AsDouble({name})",
            HeldAs.POINTER:
                "reinterpret_cast<Cxx{name}T>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr))",
            HeldAs.OBJECT:
                "reinterpret_cast<Cxx{name}T *>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr))",
        }
        ptr_options = {
            HeldAs.BYTE:
                "(Cxx{name}T)PyString_AsString({name})",
            HeldAs.INTEGER:
                """(
#if PY_MAJOR_VERSION >= 3
    (Cxx{name}T)PyLong_AsLong(*({name}))
#else
    (Cxx{name}T)PyInt_AsLong(*({name}))
#endif
)""",
            HeldAs.FLOAT:
                "(Cxx{name}T)PyFloat_AsDouble(*({name}))",
        }

        if self.category == HeldAs.POINTER and self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
            code = ptr_options[self.sip_t]
        else:
            code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{py_v}", py_v)
        return code


class RewriteMappedHelper(HeldAs):
    def cxx_to_py_template(self, name, cxx_v, cxx_to_py_value):
        options = {
            HeldAs.INTEGER:
                """    PyObject *{name} = {cxx_to_py_value};
""",
            HeldAs.FLOAT:
                """    PyObject *{name} = {cxx_to_py_value};
""",
            HeldAs.POINTER:
                """    PyObject *{name} = {cxx_to_py_value};
""",
            HeldAs.OBJECT:
                """    PyObject *{name} = {cxx_to_py_value};
""",
        }

        code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{cxx_v}", cxx_v)
        code = code.replace("{cxx_to_py_value}", cxx_to_py_value)
        return code

    def cxx_to_py_value(self, name, cxx_v, transfer):
        """An expression converting the named C++ value to Python."""
        options = {
            HeldAs.INTEGER:
                """(
#if PY_MAJOR_VERSION >= 3
    PyLong_FromLong((long){cxx_v})
#else
    PyInt_FromLong((long){cxx_v})
#endif
)""",
            HeldAs.FLOAT:
                "PyFloat_FromDouble((double){cxx_v})",
            HeldAs.POINTER:
                "sipConvertFromType((void *){cxx_v}, gen{name}T, {transfer})",
            HeldAs.OBJECT:
                "sipConvertFromType((void *)&{cxx_v}, gen{name}T, {transfer})",
        }
        ptr_options = {
            HeldAs.BYTE:
                "PyString_FromStringAndSize((char *)({cxx_v}), 1)",
            HeldAs.INTEGER:
                """(
#if PY_MAJOR_VERSION >= 3
    PyLong_FromLong((long)*{cxx_v})
#else
    PyInt_FromLong((long)*{cxx_v})
#endif
)""",
            HeldAs.FLOAT:
                "PyFloat_FromDouble((double)*({cxx_v}))",
        }

        if self.category == HeldAs.POINTER and self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
            code = ptr_options[self.sip_t]
        else:
            code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{cxx_v}", cxx_v)
        code = code.replace("{transfer}", transfer)
        return code

    def py_to_cxx_template(self, name, py_v, py_to_cxx_value):
        options = {
            HeldAs.INTEGER:
                """    Cxx{name}T cxx{name} = {py_to_cxx_value};
""",
            HeldAs.FLOAT:
                """    Cxx{name}T cxx{name} = {py_to_cxx_value};
""",
            HeldAs.POINTER:
                """    int {name}State;
    Cxx{name}T cxx{name} = {py_to_cxx_value};
""",
            HeldAs.OBJECT:
                """    int {name}State;
    Cxx{name}T *cxx{name} = {py_to_cxx_value};
""",
        }

        code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{cxx_v}", py_v)
        code = code.replace("{py_to_cxx_value}", py_to_cxx_value)
        return code

    def py_to_cxx_value(self, name, py_v, transfer):
        """An expression converting the named C++ value to Python."""
        options = {
            HeldAs.INTEGER:
                """(
#if PY_MAJOR_VERSION >= 3
    (Cxx{name}T)PyLong_AsLong({name})
#else
    (Cxx{name}T)PyInt_AsLong({name})
#endif
)""",
            HeldAs.FLOAT:
                "(Cxx{name}T)PyFloat_AsDouble({name})",
            HeldAs.POINTER:
                "reinterpret_cast<Cxx{name}T>(sipForceConvertToType(sipPy, gen{name}T, {transfer}, SIP_NOT_NONE, &{name}State, &sipErr))",
            HeldAs.OBJECT:
                "reinterpret_cast<Cxx{name}T *>(sipForceConvertToType(sipPy, gen{name}T, {transfer}, SIP_NOT_NONE, &{name}State, &sipErr))",
        }
        ptr_options = {
            HeldAs.BYTE:
                "(Cxx{name}T)PyString_AsString({name})",
            HeldAs.INTEGER:
                """(
#if PY_MAJOR_VERSION >= 3
    (Cxx{name}T)PyLong_AsLong(*({name}))
#else
    (Cxx{name}T)PyInt_AsLong(*({name}))
#endif
)""",
            HeldAs.FLOAT:
                "(Cxx{name}T)PyFloat_AsDouble(*({name}))",
        }

        if self.category == HeldAs.POINTER and self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
            code = ptr_options[self.sip_t]
        else:
            code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{py_v}", py_v)
        code = code.replace("{transfer}", transfer)
        return code


def container_rewrite_exception(container, sip, rule):
    """
    Convert a class which is an exception into a %Exception.

    :param container:
    :param sip:
    :param matcher:
    :return:
    """
    sip["name"] = utils.fqn(container, sip["name"])
    sip_name = sip["name"].replace("::", "_")
    py_name = "".join([w[0].upper() + w[1:] for w in sip_name.split("_")])
    base_exception = sip["base_specifiers"][0]
    sip["decl"] = "%Exception {}({}) /PyName={}/".format(sip["name"], base_exception, py_name)
    sip["base_specifiers"] = []
    sip["body"] = """
%RaiseCode
    const char *detail = sipExceptionRef.what();

    SIP_BLOCK_THREADS
    PyErr_SetString(sipException_{}, detail);
    SIP_UNBLOCK_THREADS
%End
""".format(sip_name)


def container_rewrite_std_exception(container, sip, rule):
    """
    Synthesise an %Exception for std::<exception>.
    """
    std_exception = sip["base_specifiers"][0]
    container_rewrite_exception(container, sip, rule)
    sip_name = std_exception.replace("::", "_")
    py_name = "".join([w[0].upper() + w[1:] for w in sip_name.split("_")])
    sip["modulecode"][std_exception] = """%Exception {}(SIP_Exception) /PyName={}/
{{
%TypeHeaderCode
#include <exception>
%End

%RaiseCode
    const char *detail = sipExceptionRef.what();

    SIP_BLOCK_THREADS
    PyErr_SetString(sipException_{}, detail);
    SIP_UNBLOCK_THREADS
%End
}};
""".format(std_exception, py_name, sip_name)


def variable_rewrite_array(container, variable, sip, rule):
    if variable.type.kind == TypeKind.CONSTANTARRAY:
        variable_rewrite_array_fixed(container, variable, sip, rule)
    else:
        variable_rewrite_array_nonfixed(container, variable, sip, rule)


def variable_rewrite_array_fixed(container, variable, sip, rule):
    """
    Handle n-dimensional fixed size arrays.
    """
    #
    # Templates for a SIP_PYBUFFER.
    #
    SIP_PYBUFFER_GETCODE = """    char *cxxvalue = (char *)&{cxxarray}[0];

    // Create the Python buffer.
    Py_ssize_t elementCount = {element_count};
    sipPy = PyByteArray_FromStringAndSize(cxxvalue, elementCount);"""

    SIP_PYBUFFER_SETCODE = """    char *cxxvalue = (char *)&{cxxarray}[0];
    Py_ssize_t elementCount = {element_count};
    const char *name = "{name}";

    if (!PyByteArray_Check(sipPy)) {
        PyErr_Format(PyExc_TypeError, "expected buffer");
        sipErr = 1;
    }

    // Convert the buffer to C++.
    if (!sipErr) {
        if (PyByteArray_GET_SIZE(sipPy) != elementCount) {
            PyErr_Format(PyExc_ValueError, "'%s' must have length %ld", name, elementCount);
            sipErr = 1;
        } else {
            memcpy(cxxvalue, PyByteArray_AsString(sipPy), elementCount);
        }
    }"""
    #
    # Templates for a SIP_PYLIST.
    #
    SIP_PYLIST_GETCODE = """typedef {cxx_t} CxxvalueT;
struct getcode
{
    PyObject *getList(int *sipErr, Py_ssize_t dims[], int numDims, int dim, CxxvalueT *cxxvalue[]) {
        Py_ssize_t elementCount = dims[dim];
        PyObject *list;

        // Create the Python list.
        if (!*sipErr) {
            list = PyList_New(elementCount);
            if (!list) {
                PyErr_Format(PyExc_TypeError, "unable to create a list");
                *sipErr = 1;
            }
        }

        // Set the list elements.
        if (!*sipErr) {
            for (Py_ssize_t i = 0; i < elementCount; ++i) {
                PyObject *value;
                if (dim + 1 < numDims) {
                    value = getList(sipErr, dims, numDims, dim + 1, &cxxvalue[i]);
                } else {
// TODO: use sipConvertToArray and sipConvertToTypedArray
{cxx_to_py}
                }
                if (value == NULL) {
                    PyErr_Format(PyExc_TypeError, "cannot insert value into list");
                    Py_XDECREF(value);
                    Py_DECREF(list);
                    *sipErr = 1;
                } else {
                    PyList_SET_ITEM(list, i, value);
                }
            }
        }
        return list;
    };
} getcode;

    Py_ssize_t dims[] = {{dims}};
    auto numDims = sizeof(dims) / sizeof(dims[0]);
    int sipErr = 0;
    PyObject *list = getcode.getList(&sipErr, dims, numDims, 0, (CxxvalueT **)&{cxxarray}[0]);
    sipPy = sipErr ? list : NULL;"""

    SIP_PYLIST_SETCODE = """typedef {cxx_t} CxxvalueT;
struct setcode
{
    void setList(int *sipErr, Py_ssize_t dims[], int numDims, int dim, PyObject *list, CxxvalueT *cxxvalue[]) {
        Py_ssize_t elementCount = dims[dim];
        const char *name = "{name}";

        if (!*sipErr) {
            if (!PyList_Check(list)) {
                PyErr_Format(PyExc_TypeError, "expected list");
                *sipErr = 1;
            }
        }

        // Convert the list to C++.
        if (!*sipErr) {
            if (PyList_GET_SIZE(list) != elementCount) {
                PyErr_Format(PyExc_ValueError, "'%s' must have length %ld", name, elementCount);
                *sipErr = 1;
            } else {
                for (Py_ssize_t i = 0; i < elementCount; ++i) {
                    PyObject *value = PyList_GetItem(list, i);
                    if (dim + 1 < numDims) {
                        setList(sipErr, dims, numDims, dim + 1, value, &cxxvalue[i]);
                    } else {
{py_to_cxx}
                    }
                }
            }
        }
    };
} setcode;

    Py_ssize_t dims[] = {{dims}};
    auto numDims = sizeof(dims) / sizeof(dims[0]);
    setcode.setList(&sipErr, dims, numDims, 0, sipPy, (CxxvalueT **)&{cxxarray}[0]);"""

    prefixes, text, operators, dims = utils.decompose_type(sip["decl"])
    dims = [d[1:-1] for d in dims]
    element_type = variable.type
    while element_type.kind == TypeKind.CONSTANTARRAY:
        element_type = element_type.underlying_type
    converter = RewriteArrayHelper(sip["decl"], element_type)
    if converter.category == HeldAs.BYTE:
        decl = "SIP_PYBUFFER"
        getcode = SIP_PYBUFFER_GETCODE
        setcode = SIP_PYBUFFER_SETCODE
    else:
        decl = "SIP_PYLIST"
        getcode = SIP_PYLIST_GETCODE
        setcode = SIP_PYLIST_SETCODE
    code = """
{
%GetCode
{trace}
"""
    code += getcode
    code += """
%End"""
    #
    # Do we need %SetCode?
    #
    if "const " not in prefixes:
        code += """

%SetCode
{trace}
"""
        code += setcode
        code += """
%End"""
    code += """
}"""
    if converter.category == HeldAs.BYTE:
        pass
    else:
        aliases_ = converter.declare_type_helpers("value", "*sipErr = 1;")
        cxx_to_py = converter.cxx_to_py("value", True, "(*cxxvalue)[i]")
        py_to_cxx = converter.py_to_cxx("value", True, "(*cxxvalue)[i]")
        code = code.replace("{cxx_t}", element_type.spelling)
        code = code.replace("{aliases}", aliases_)
        code = code.replace("{cxx_to_py}", cxx_to_py)
        code = code.replace("{py_to_cxx}", py_to_cxx)
    trace = trace_generated_for(variable, rule, {})
    code = code.replace("{trace}", trace)
    #
    # SIP cannot handle %GetCode/%SetCode for global variables.
    #
    if container.kind == CursorKind.TRANSLATION_UNIT:
        if len(dims) == 1:
            #
            # Note that replacing [] with * only works for one dimension.
            #
            dims = "*" * len(dims)
            sip["decl"] = re.sub("\[.*\]", dims, sip["decl"])
        else:
            return
    else:
        sip["decl"] = decl
        code = code.replace("{element_count}", dims[-1])
        if variable.storage_class == StorageClass.STATIC:
            code = code.replace("{cxxarray}", utils.fqn(variable, "{name}"))
        else:
            code = code.replace("{cxxarray}", "sipCpp->{name}")
        code = code.replace("{name}", sip["name"])
        dims = ["(Py_ssize_t){}".format(i) for i in dims]
        code = code.replace("{dims}", ", ".join(dims))
        sip["code"] = code


def variable_rewrite_array_nonfixed(container, variable, sip, rule):
    prefixes, text, operators, dims = utils.decompose_type(sip["decl"])
    if len(dims) == 1:
        sip["decl"] = sip["decl"].replace("[]", "*")
    else:
        logger.warning(
            _("TODO: Support for nonfixed {}-D variables: {}").format(len(dims), utils.item_describe(variable)))
    #
    # Even though we render this as a "foo *", it started life as a "foo []". So if there is a const, the array
    # itself was a const...
    #
    if "const " in prefixes:
        sip["annotations"].add("NoSetter")


def variable_rewrite_extern(container, variable, sip, rule):
    """
    SIP does not support "extern", so drop the keyword.
    """
    sip["decl"] = sip["decl"][7:]
    if MAPPED_TYPE_RE.match(sip["decl"]):
        variable_rewrite_mapped(container, variable, sip, rule)
    elif isinstance(variable.type, clangcparser.ArrayType):
        variable_rewrite_array(container, variable, sip, rule)


def variable_rewrite_static(container, variable, sip, rule):
    """
    SIP does not support "static", so handle static variables.
    """
    #
    # SIP does not support %GetCode/%SetCode for file scope variables. But luckily, just dropping the prefix works
    # assuming we don't actually need anything more complicated.
    #
    sip["decl"] = sip["decl"][7:]
    if MAPPED_TYPE_RE.match(sip["decl"]):
        variable_rewrite_mapped(container, variable, sip, rule)
    elif isinstance(variable.type, clangcparser.ArrayType):
        variable_rewrite_array(container, variable, sip, rule)
    #
    # Inside a class, "static" is fine. Do we need %GetCode/%SetCode?
    #
    while container.kind == CursorKind.NAMESPACE:
        container = container.semantic_parent
    if container.kind != CursorKind.TRANSLATION_UNIT:
        sip["decl"] = "static " + sip["decl"]


def variable_rewrite_mapped(container, variable, sip, rule):
    """
    Handle class-static variables.
    """
    #
    # Create a Python <-> C++ conversion helper.
    #
    variable_type = variable.type.get_canonical()
    converter = RewriteMappedHelper(variable_type.spelling, variable_type)
    aliases = converter.declare_type_helpers("value", "sipErr = 1;")
    code = """
{
%GetCode
{trace}
    int sipErr = 0;
"""
    code += aliases
    if converter.is_mapped_type:
        code += """    if (sipErr) {
        return NULL;
    }
"""
    is_complex = converter.category in [HeldAs.POINTER, HeldAs.OBJECT]
    if variable.storage_class == StorageClass.STATIC:
        cxx = utils.fqn(variable, "{name}")
    else:
        cxx = "sipCpp->{name}"
    code += converter.cxx_to_py("value", False, "{cxx}")
    code += """    sipPy = (sipErr || PyErr_Occurred()) ? NULL : value;
%End

%SetCode
{trace}
"""
    code += aliases
    if converter.is_mapped_type:
        code += """    if (sipErr) {
        return -1;
    }
"""
    code += converter.py_to_cxx("value", False, "{cxx}")
    if is_complex:
        code += """    if (!sipErr) {
        {cxx} = *cxxvalue;
    }
%End
}"""
    else:
        code += """    if (PyErr_Occurred()) {
        sipErr = 1;
    } else {
        {cxx} = cxxvalue;
    }
%End
}"""
    code = code.replace("{cxx}", cxx)
    code = code.replace("{name}", sip["name"])
    trace = trace_generated_for(variable, rule, {})
    code = code.replace("{trace}", trace)
    sip["code"] = code


def container_rules():
    return [
        #
        # Handle std:: exceptions.
        #
        [".*", ".*Exception", ".*", ".*", "std::.*", container_rewrite_std_exception],
        #
        # Other exceptions.
        #
        [".*", ".*", ".*", ".*", ".*Exception", container_rewrite_exception],
    ]


def forward_declaration_rules():
    return [
        #
        # Default forward declaration handling.
        #
        [".*", ".*", ".*", rule_helpers.forward_declaration_discard],
    ]


def function_rules():
    return [
        #
        # Handle functions with templated return types and/or templated parameters.
        #
        [".*", ".*", ".*", ".*[A-Za-z0-9_:]+<.*>.*", ".*", function_uses_templates],
        [".*", ".*", ".*", ".*", ".*[A-Za-z0-9_:]+<.*>.*", function_uses_templates],
    ]


def variable_rules():
    return [
        #
        # Discard the extern keyword.
        #
        [".*", ".*", "extern .*", variable_rewrite_extern],
        #
        # Emit code for static variables.
        #
        [".*", ".*", "static .*", variable_rewrite_static],
        #
        # Emit code for templated variables.
        #
        [".*", ".*", MAPPED_TYPE_RE.pattern, variable_rewrite_mapped],
        #
        # Emit code for fixed arrays.
        #
        [".*", ".*", "(const | volatile )*.*(\[[^]]+\])+", variable_rewrite_array_fixed],
        #
        # Emit code for variable arrays.
        #
        [".*", ".*", "(const | volatile )*.*(\[\])+", variable_rewrite_array_nonfixed],
    ]
