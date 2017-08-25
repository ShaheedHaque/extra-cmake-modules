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

"""Utility functions."""
import os
import re

from clangcparser import CursorKind, TypeKind


def decompose_type_names(text):
    """
    Any template parameters from the parent in "type_text" are extracted, and
    return (name, [parameters]) or (name, None).
    """
    parameters = text.split("<", 1)[-1]
    if parameters == text:
        parameters = None
    else:
        #
        # Strip any suffix &* and parameter name.
        #
        tmp = parameters.rsplit(">", 1)[0]
        #
        # Parse...
        #
        parameters = []
        bracket_level = 0
        left = 0
        for right, token in enumerate(tmp):
            if bracket_level <= 0 and token is ",":
                parameters.append(tmp[left:right].strip())
                left = right + 1
            elif token is "<":
                bracket_level += 1
            elif token is ">":
                bracket_level -= 1
        parameters.append(tmp[left:].strip())
    #
    # Strip any keywords before the name.
    #
    name = text.split("<", 1)[0]
    while name.startswith(("const ", "volatile ", "typename ", "class ", "struct ")):
        tmp, name = name.split(None, 1)
    return name, parameters


def fqn(cursor, alternate_spelling=None):
    """
    A handy helper to return the fully-qualified name for something.
    """
    parents = ""
    parent = cursor.semantic_parent
    while parent and parent.kind != CursorKind.TRANSLATION_UNIT:
        parents = parent.spelling + "::" + parents
        parent = parent.semantic_parent
    if alternate_spelling is None:
        text = cursor.spelling
    else:
        text = alternate_spelling
    return parents + text


def cursor_parents(cursor):
    """
    A helper function which returns the parents of a cursor in the forms:

        - A::B::C::...N for non-top level entities.
        - filename.h    for top level entities.
        - ""            in exceptional cases of having no parents.
    """
    parents = ""
    parent = cursor.semantic_parent
    while parent and parent.kind != CursorKind.TRANSLATION_UNIT:
        parents = parent.spelling + "::" + parents
        parent = parent.semantic_parent
    if parent and not parents:
        return os.path.basename(parent.spelling)
    return parents[:-2]


def item_describe(item, alternate_spelling=None):
    """
    A helper function providing a standardised description for an item,
    which may be a cursor.
    """
    if isinstance(item, str):
        return item
    if alternate_spelling is None:
        text = item.spelling
    else:
        text = alternate_spelling
    return "{} on line {} '{}::{}'".format(item.kind.name, item.extent.start.line, cursor_parents(item), text)


def trace_inserted_for(item, rule):
    trace = "// Inserted for {} (by {}):\n".format(item_describe(item), rule)
    return trace


def trace_discarded_by(item, rule):
    trace = "// Discarded {} (by {})\n".format(item_describe(item), rule)
    return trace


def trace_generated_for(item, rule, extra):
    trace = "// Generated for {} (by {}): {}\n".format(item_describe(item), rule, extra)
    return trace


def trace_modified_by(item, rule):
    trace = "// Modified {} (by {}):\n".format(item_describe(item), rule)
    return trace


class HeldAs(object):
    """
    Items are held either as integral values, pointer values or objects. The
    Python interchange logic depends on this.

    TODO: In the case of pointers, we also need to know whether a specialised
    pointer type is in use (or just "*").
    """
    VOID = "void"
    BYTE = "BYTE"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    POINTER = "POINTER"
    OBJECT = "OBJECT"
    RE_BYTE = re.compile("^char\W|\Wchar\W|\Wchar$|^char$")
    RE_INTEGER = re.compile("^(short|int|long)\W|\W(short|int|long)\W|\W(short|int|long)$|^(short|int|long)$|^bool$")
    RE_FLOAT = re.compile("^(float|double)\W|\W(float|double)\W|\W(float|double)$|^(float|double)$")
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

    def __init__(self, cxx_t, clang_t, base_cxx_t=None):
        """
        :param cxx_t:                       The declaration text from the source code.
        :param clang_t:                     The Clang type or None.
        :param base_cxx_t:                  The base type, can be manually overridden.
        """
        self.cxx_t = cxx_t
        if base_cxx_t is None:
            base_cxx_t = self.base_type(cxx_t)
        #
        # This may be a mapped type.
        #
        self.is_mapped_type = ("<" in base_cxx_t)
        if self.is_mapped_type:
            self.sip_t = "sipFindType(cxx{name}S)"
        else:
            #
            # Primitive types don't need help from a sipType_xxx.
            #
            base_held_as = HeldAs.categorise(base_cxx_t, None)
            if base_held_as in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
                self.sip_t = base_held_as
            else:
                self.sip_t = "sipType_" + base_cxx_t.replace("::", "_")
        self.category = HeldAs.categorise(cxx_t, clang_t)

    def cxx_to_py_template(self, name, cxx_v, cxx_to_py_value):
        raise NotImplementedError()

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
                "sipConvertFromType((void *)cxx{name}, gen{name}T, sipTransferObj)",
            HeldAs.OBJECT:
                "sipConvertFromNewType((void *)cxx{name}, gen{name}T, sipTransferObj)",
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
        return code

    def py_to_cxx_template(self, name, py_v, py_to_cxx_value):
        raise NotImplementedError()

    def py_to_cxx_value(self, name, py_v, transfer):
        """An expression converting the named C++ value to Python."""
        options = {
            HeldAs.INTEGER:
                """(
#if PY_MAJOR_VERSION >= 3
    (Cxx{name}T)PyLong_AsLong({py_v})
#else
    (Cxx{name}T)PyInt_AsLong({py_v})
#endif
)""",
            HeldAs.FLOAT:
                "(Cxx{name}T)PyFloat_AsDouble({py_v})",
            HeldAs.POINTER:
                "reinterpret_cast<Cxx{name}T>(sipForceConvertToType({py_v}, gen{py_v}T, sipTransferObj, SIP_NOT_NONE, &{py_v}State, sipIsErr))",
            HeldAs.OBJECT:
                "reinterpret_cast<Cxx{name}T *>(sipForceConvertToType({py_v}, gen{py_v}T, sipTransferObj, SIP_NOT_NONE, &{py_v}State, sipIsErr))",
        }
        ptr_options = {
            HeldAs.BYTE:
                "(Cxx{name}T)PyString_AsString({py_v})",
            HeldAs.INTEGER:
                """(
#if PY_MAJOR_VERSION >= 3
    (Cxx{name}T)PyLong_AsLong(*({py_v}))
#else
    (Cxx{name}T)PyInt_AsLong(*({py_v}))
#endif
)""",
            HeldAs.FLOAT:
                "(Cxx{name}T)PyFloat_AsDouble(*({py_v}))",
        }

        if self.category == HeldAs.POINTER and self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
            code = ptr_options[self.sip_t]
        else:
            code = options[self.category]
        code = code.replace("{name}", name)
        code = code.replace("{py_v}", py_v)
        return code

    @staticmethod
    def actual_type(parameter_text):
        """
        :param parameter_text:              The text from the source code.
        :return: the type of the parameter.
        """
        return parameter_text

    @staticmethod
    def base_type(parameter_text):
        """
        :param parameter_text:              The text from the source code.
        :return: the base_type of the parameter, e.g. without a pointer suffix.
        """
        if parameter_text.endswith(("*", "&")):
            parameter_text = parameter_text[:-1].strip()
        if parameter_text.startswith("const "):
            parameter_text = parameter_text[6:]
        return parameter_text

    @staticmethod
    def categorise(cxx_t, clang_t):
        """
        We would like to be able to use clang type system to determine the
        HELD_AS, but this is not always possible. For example, in a templated
        typedef, any int types are not even included in the children of the
        typedef. Similarly, in a variable declaration, a templated type might
        appear simply as TypeKind.UNEXPOSED.

        TODO: When we figure this out, get rid of the horrid heuristics.

        :param cxx_t:                       The text from the source code.
        :param clang_t:                     The Clang type or None.
        :return: the storage type of the object.
        """
        if cxx_t.endswith("*"):
            return HeldAs.POINTER
        elif cxx_t.endswith("&"):
            return HeldAs.categorise(cxx_t[:-1].strip(), clang_t)
        elif cxx_t == HeldAs.VOID:
            return HeldAs.VOID
        elif cxx_t.startswith("type-parameter-"):
            return HeldAs.OBJECT
        #
        # The clang type should be authoritative.
        #
        if clang_t is not None:
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
                return HeldAs._rev_map[clang_t.kind]
            except KeyError:
                if clang_t.kind == TypeKind.LVALUEREFERENCE:
                    return HeldAs.categorise(cxx_t, clang_t.underlying_type.get_canonical())
                elif clang_t.kind == TypeKind.VOID:
                    return HeldAs.VOID
                #
                # We we already know it did not seem to be a pointer, so check for a templated object:
                #
                #   TypeKind.ELABORATED: 'WTF::Vector<RegDescriptor *>'
                #   TypeKind.UNEXPOSED: 'HashMap<KJS::Interpreter *, ProtectedPtr<KJS::JSValue> >'
                #
                if "<" in cxx_t and clang_t.kind in [TypeKind.ELABORATED, TypeKind.UNEXPOSED]:
                    return HeldAs.OBJECT
                return HeldAs.OBJECT
        if "<" in cxx_t:
            return HeldAs.OBJECT
        if HeldAs.RE_BYTE.search(cxx_t):
            return HeldAs.BYTE
        #
        # Must check for FLOAT before INTEGER in case of "long double" etc.
        #
        if HeldAs.RE_FLOAT.search(cxx_t):
            return HeldAs.FLOAT
        if HeldAs.RE_INTEGER.search(cxx_t):
            return HeldAs.INTEGER
        return HeldAs.OBJECT

    def declare_type_helpers(self, name, error, need_string=False, need_cxx_t=True):
        """
        Make it easier to track changes in generated output.

        By creating local definitions at the top of each section of emitted output, the rest of the expanded template
        is a constant. This makes it easier to see the effect of any changes using "diff".
        """
        code = ""
        if self.is_mapped_type or need_string:
            code += """    const char *cxx{name}S = "{cxx_t}";
"""
        if need_cxx_t:
            code += """    typedef {cxx_t} Cxx{name}T;
"""
        if self.category in [HeldAs.POINTER, HeldAs.OBJECT]:
            #
            # If the sipTypeDef needs a run-time lookup using sipFindMappedType, can convert that into a one-off cost
            # using a static.
            #
            if self.is_mapped_type:
                code += """    static const sipTypeDef *gen{name}T = NULL;
    if (gen{name}T == NULL) {
        gen{name}T = {sip_t};
        if (gen{name}T == NULL) {
            PyErr_Format(PyExc_TypeError, "cannot find SIP type for '%s'", cxx{name}S);
            {error}
        }
    }
"""
            elif self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
                #
                # Primitive types don't need help from a sipType_xxx.
                #
                pass
            else:
                code += """    const sipTypeDef *gen{name}T = {sip_t};
"""
        code = code.replace("{sip_t}", self.sip_t)
        code = code.replace("{name}", name)
        code = code.replace("{error}", error)
        code = code.replace("{cxx_t}", self.cxx_t)
        return code

    def cxx_to_py(self, name, needs_reference, cxx_v):
        cxx_to_py_value = self.cxx_to_py_value(name, cxx_v, "sipTransferObj" if needs_reference else "NULL")
        code = self.cxx_to_py_template(name, cxx_v, cxx_to_py_value)
        return code

    def py_to_cxx(self, name, needs_reference, py_v):
        py_to_cxx_value = self.py_to_cxx_value(name, py_v, "sipTransferObj" if needs_reference else "NULL")
        code = self.py_to_cxx_template(name, py_v, py_to_cxx_value)
        return code
