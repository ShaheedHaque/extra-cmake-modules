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

"""Rules which ameliorate some of the shortcomings of SIP."""

from __future__ import print_function
import gettext
import logging
import re

from clang.cindex import CursorKind, TypeKind

logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _


MAPPED_TYPE_RE = re.compile(".*<.*")


def _parents(container):
    parents = []
    parent = container
    while parent and parent.kind != CursorKind.TRANSLATION_UNIT:
        parents.append(parent.spelling)
        parent = parent.semantic_parent
    parents = "::".join(reversed(parents))
    return parents


class HeldAs(object):
    """
    Items are held either as integral values, pointer values or objects. The
    Python interchange logic depends on this.

    TODO: In the case of pointers, we also need to know whether a specialised
    pointer type is in use (or just "*").
    """
    BYTE = "BYTE"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    POINTER = "POINTER"
    OBJECT = "OBJECT"
    #
    # Clang primitive classifications corresponding to Python types.
    #
    _fwd_map = {
        BYTE: [TypeKind.CHAR_S, TypeKind.CHAR_U, TypeKind.SCHAR, TypeKind.UCHAR],
        INTEGER: [TypeKind.BOOL, TypeKind.CHAR16, TypeKind.CHAR32,
                  TypeKind.USHORT, TypeKind.UINT, TypeKind.ULONG, TypeKind.ULONGLONG, TypeKind.UINT128,
                  TypeKind.SHORT, TypeKind.INT, TypeKind.LONG, TypeKind.LONGLONG, TypeKind.INT128,
                  TypeKind.ENUM],
        FLOAT: [TypeKind.FLOAT, TypeKind.DOUBLE, TypeKind.FLOAT128, TypeKind.LONGDOUBLE],
        POINTER: [TypeKind.POINTER, TypeKind.MEMBERPOINTER],
        OBJECT: [TypeKind.RECORD],
    }
    _rev_map = None

    def __init__(self, cxx_t, clang_kind, sip_t):
        """
        :param cxx_t:                       The text from the source code.
        :param clang_kind:                  The clang kind.
        :param sip_t:
        """
        self.cxx_t = cxx_t
        #
        # This may be a mapped type.
        #
        self.is_mapped_type = ("<" in sip_t)
        if self.is_mapped_type:
            self.sip_t = "sipFindType(cxx{name}S)"
        else:
            self.sip_t = "sipType_" + sip_t.replace("::", "_")
        self.category = HeldAs.categorise(cxx_t, clang_kind)

    @staticmethod
    def categorise(cxx_t, clang_kind):
        """
        We would like to be able to use clang type system to determine the
        HELD_AS, but this is not always possible. For example, in a templated
        typedef, any int types are not even included in the children of the
        typedef. Similarly, in a variable declaration, a templated type might
        appear simply as TypeKind.UNEXPOSED.

        TODO: When we figure this out, get rid of the horrid heuristics.

        :param cxx_t:                       The text from the source code.
        :param clang_kind:                  The clang kind.
        :return: the storage type of the object.
        """
        if cxx_t.endswith(("Ptr", "*", "&")):
            return HeldAs.POINTER
        if cxx_t.startswith(("QSharedPointer", "QExplicitlySharedDataPointer")):
            return HeldAs.POINTER
        #
        # The clang type should be authoritative.
        #
        if clang_kind is not None:
            #
            # One-time init of lookup map.
            #
            if not HeldAs._rev_map:
                HeldAs._rev_map = {}
                for key, values in HeldAs._fwd_map.items():
                    for value in values:
                        HeldAs._rev_map[value] = key
            #
            # Lookup.
            #
            try:
                return HeldAs._rev_map[clang_kind]
            except KeyError:
                #
                # We we already know it did not seem to be a pointer, so check for a templated object:
                #
                #   TypeKind.ELABORATED: 'WTF::Vector<RegDescriptor *>'
                #   TypeKind.UNEXPOSED: 'HashMap<KJS::Interpreter *, ProtectedPtr<KJS::JSValue> >'
                #
                if "<" in cxx_t and clang_kind in [TypeKind.ELABORATED, TypeKind.UNEXPOSED]:
                    return HeldAs.OBJECT
                else:
                    raise AssertionError(_("Unexpected {} for {}").format(clang_kind, cxx_t))
        if "int" in cxx_t or "long" in cxx_t or cxx_t == "bool":
            return HeldAs.INTEGER
        return HeldAs.OBJECT

    def declare_type_helpers(self, name, need_string=False):
        """
        Make it easier to track changes in generated output.

        By creating local definitions at the top of each section of emitted output, the rest of the expanded template
        is a constant. This makes it easier to see the effect of any changes using "diff".
        """
        code = ""
        if self.is_mapped_type or need_string:
            code += """    const char *cxx{name}S = "{cxx_t}";
"""
        if self.category in [HeldAs.POINTER, HeldAs.OBJECT]:
            #
            # If the sipTypeDef needs a run-time lookup using sipFindMappedType, can convert that into a one-off cost
            # using a static.
            #
            if self.is_mapped_type:
                code += """    typedef {cxx_t} Cxx{name}T;
    static const sipTypeDef *gen{name}T = NULL;
    if (gen{name}T == NULL) {
        gen{name}T = {sip_t};
        if (gen{name}T == NULL) {
            PyErr_Format(PyExc_TypeError, "cannot find SIP type for '%s'", cxx{name}S);
            sipErr = 1;
        }
    }
"""
            else:
                code += """    typedef {cxx_t} Cxx{name}T;
    const sipTypeDef *gen{name}T = {sip_t};
"""
        else:
            code += """    typedef {cxx_t} Cxx{name}T;
"""
        code = code.replace("{sip_t}", self.sip_t)
        code = code.replace("{name}", name)
        code = code.replace("{cxx_t}", self.cxx_t)
        return code

    def cxx_to_py(self, name, options, cxxsrc, needs_reference):
        code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{cxxsrc}", cxxsrc)
        code = code.replace("{transfer}", "sipTransferObj" if needs_reference else "NULL")
        return code

    def py_to_cxx(self, name, options, to, needs_reference):
        code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{py_to_cxx}", to)
        code = code.replace("{transfer}", "sipTransferObj" if needs_reference else "NULL")
        return code


def variable_rewrite_extern(container, variable, sip, matcher):
    """
    SIP does not support "extern", so drop the keyword.

    :param container:
    :param variable:
    :param sip:
    :param matcher:
    :return:
    """
    assert sip["decl"].startswith("extern ")
    sip["decl"] = sip["decl"][7:]


def variable_rewrite_static(container, variable, sip, matcher):
    """
    SIP does not support "static", so handle static variables.

    :param container:
    :param variable:
    :param sip:
    :param matcher:
    :return:
    """
    assert sip["decl"].startswith("static ")
    if container.kind == CursorKind.TRANSLATION_UNIT:
        #
        # SIP does not support %GetCode/%SetCode for file scope variables. But luckily, just dropping the prefix works
        # assuming we don't actually need anything more complicated.
        #
        sip["decl"] = sip["decl"][7:]
    else:
        #
        # Inside a class, "static" is fine. Do we need %GetCode/%SetCode?
        #
        if MAPPED_TYPE_RE.match(sip["decl"]):
            variable_rewrite_mapped(container, variable, sip, matcher)


def variable_rewrite_mapped(container, variable, sip, matcher):
    """
    Handle class-static variables.

    :param container:
    :param variable:
    :param sip:
    :param matcher:
    :return:
    """
    #
    # SIP does not support "static", and simply dropping the "static" would change the linkage in the case of
    # a class so we just delete the variable - but it seems to work for file scope (!!). TODO: can we use
    # %GetCode/%SetCode for the class case? (SIP does not support %GetCode/%SetCode for file scope).
    #
    cxx_to_py_template = {
        HeldAs.INTEGER:
            """    Cxx{name}T cxx{name} = {cxxsrc};
#if PY_MAJOR_VERSION >= 3
    PyObject *{name} = PyLong_FromLong((long)cxx{name});
#else
    PyObject *{name} = PyInt_FromLong((long)cxx{name});
#endif
""",
        HeldAs.FLOAT:
            """    Cxx{name}T cxx{name} = {cxxsrc};
    PyObject *{name} = PyFloat_FromDouble((double)cxx{name});
""",
        HeldAs.POINTER:
            """    Cxx{name}T cxx{name} = {cxxsrc};
    PyObject *{name} = sipConvertFromType(cxx{name}, gen{name}T, {transfer});
""",
        HeldAs.OBJECT:
            """    Cxx{name}T *cxx{name} = &{cxxsrc};
    PyObject *{name} = sipConvertFromType(cxx{name}, gen{name}T, {transfer});
""",
    }

    py_to_cxx_template = {
        HeldAs.INTEGER:
            """    Cxx{name}T cxx{name};
#if PY_MAJOR_VERSION >= 3
    cxx{name} = (Cxx{name}T)PyLong_AsLong(sipPy);
#else
    cxx{name} = (Cxx{name}T)PyInt_AsLong(sipPy);
#endif
""",
        HeldAs.FLOAT:
            """    Cxx{name}T cxx{name} = (Cxx{name}T)PyFloat_AsDouble(sipPy);
""",
        HeldAs.POINTER:
            """    int {name}State;
    Cxx{name}T cxx{name} = NULL;
    cxx{name} = reinterpret_cast<Cxx{name}T>(sipForceConvertToType(sipPy, gen{name}T, {transfer}, SIP_NOT_NONE, &{name}State, &sipErr));
""",
        HeldAs.OBJECT:
            """    int {name}State;
    Cxx{name}T *cxx{name} = NULL;
    cxx{name} = reinterpret_cast<Cxx{name}T *>(sipForceConvertToType(sipPy, gen{name}T, {transfer}, SIP_NOT_NONE, &{name}State, &sipErr));
""",
    }

    #
    # Create a Python <-> C++ conversion helper.
    #
    converter = HeldAs(variable.type.spelling, variable.type.kind, variable.type.spelling)
    aliases = converter.declare_type_helpers("value")
    code = """
{
%GetCode
    int sipErr = 0;
"""
    code += aliases
    if converter.is_mapped_type:
        code += """    if (sipErr) {
        return NULL;
    }
"""
    is_complex = converter.category in [HeldAs.POINTER, HeldAs.OBJECT]
    is_static = sip["decl"].startswith("static ")
    has_parent = is_complex and not is_static
    if has_parent:
        code += """    sipPy = sipGetReference(sipPySelf, -1);
    if (sipPy) {
        return sipPy;
    }
"""
    if is_static:
        cxx = _parents(container) + "::" + "{name}"
    else:
        cxx = "sipCpp->{name}"
    code += converter.cxx_to_py("value", cxx_to_py_template, "{cxx}", has_parent)
    if has_parent:
        code += """    sipKeepReference(sipPySelf, -1, value);
"""
    code += """    sipPy = (sipErr || PyErr_Occurred()) ? NULL : value;
%End

%SetCode
"""
    code += aliases
    if converter.is_mapped_type:
        code += """    if (sipErr) {
        return -1;
    }
"""
    code += converter.py_to_cxx("value", py_to_cxx_template, "{cxx}", has_parent)
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
    sip["code"] = code


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
    ]
