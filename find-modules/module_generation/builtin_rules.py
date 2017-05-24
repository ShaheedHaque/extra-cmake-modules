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

from __future__ import print_function
import gettext
import logging
import re

from clang.cindex import AccessSpecifier, CursorKind, TypeKind
from sip_generator import trace_generated_for

logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _


FIXED_ARRAY_RE = re.compile(".*(\[[^]]+\])+")
VARIABLE_ARRAY_RE = re.compile(".*(\[\])+")
MAPPED_TYPE_RE = re.compile(".*<.*")
ANNOTATIONS_RE = re.compile(" /.*/")
RE_PARAMETER_VALUE = re.compile(r"\s*=\s*")
RE_PARAMETER_TYPE = re.compile(r"(.*[ >&*])(.*)")


def fqn(container, child):
    """
    A handy helper to return the full-qualified name for something.

    :param container:                   Parent container.
    :param child:                       The item whose FQN we seek.
    :return: string name.
    """
    result = []
    parent = container
    while parent and parent.kind != CursorKind.TRANSLATION_UNIT:
        result.append(parent.spelling)
        parent = parent.semantic_parent
    result = "::".join(reversed(result))
    return result + "::" + child


def parse_template(template, expected=None):
    """
    Extract template name and arguments even in cases like 'const QSet<QMap<QAction *, KIPI::Category> > &foo'.

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
    if expected is not None:
        assert len(args) == expected, "Expected {} template arguments in '{}', got {}".format(expected, template, args)
    return name, args


def actual_type(parameter_text):
    """
    :param parameter_text:              The text from the source code.
    :return: the type of the parameter.
    """
    return parameter_text


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

    def __init__(self, cxx_t, clang_kind, base_cxx_t=None):
        """
        :param cxx_t:                       The declaration text from the source code.
        :param clang_kind:                  The clang kind or None.
        :param base_cxx_t:                  Th base type, can be manually overridden.
        """
        self.cxx_t = cxx_t
        if base_cxx_t is None:
            base_cxx_t = base_type(cxx_t)
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
        self.category = HeldAs.categorise(cxx_t, clang_kind)

    def cxx_to_py_template(self):
        raise NotImplementedError()

    def py_to_cxx_template(self):
        raise NotImplementedError()

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
        :param clang_kind:                  The clang kind or None.
        :return: the storage type of the object.
        """
        if cxx_t.endswith("*"):
            return HeldAs.POINTER
        elif cxx_t.endswith("&"):
            return HeldAs.categorise(cxx_t[:-1].strip(), clang_kind)
        elif cxx_t == HeldAs.VOID:
            return HeldAs.VOID
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
                if clang_kind == TypeKind.LVALUEREFERENCE:
                    return HeldAs.OBJECT
                elif clang_kind == TypeKind.VOID:
                    return HeldAs.VOID
                #
                # We we already know it did not seem to be a pointer, so check for a templated object:
                #
                #   TypeKind.ELABORATED: 'WTF::Vector<RegDescriptor *>'
                #   TypeKind.UNEXPOSED: 'HashMap<KJS::Interpreter *, ProtectedPtr<KJS::JSValue> >'
                #
                if "<" in cxx_t and clang_kind in [TypeKind.ELABORATED, TypeKind.UNEXPOSED]:
                    return HeldAs.OBJECT
                raise AssertionError(_("Unexpected {} for {}").format(clang_kind, cxx_t))
        if "<" in cxx_t:
            return HeldAs.OBJECT
        if "char" in cxx_t:
            return HeldAs.BYTE
        if "float" in cxx_t or "double" in cxx_t:
            return HeldAs.FLOAT
        if "int" in cxx_t or "long" in cxx_t or cxx_t == "bool":
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

    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        code = self.cxx_to_py_template()
        code = code.replace("{name}", name)
        code = code.replace("{cxx_i}", cxx_i)
        code = code.replace("{cxx_po}", cxx_po if cxx_po else cxx_i)
        code = code.replace("{transfer}", "sipTransferObj" if needs_reference else "NULL")
        return code

    def py_to_cxx(self, name, needs_reference, py_v):
        code = self.py_to_cxx_template()
        code = code.replace("{name}", name)
        code = code.replace("{py_v}", py_v)
        code = code.replace("{transfer}", "sipTransferObj" if needs_reference else "NULL")
        return code


class RewriteArrayHelper(HeldAs):
    cxx_to_py_templates = {
        HeldAs.INTEGER:
            """#if PY_MAJOR_VERSION >= 3
                    {name} = PyLong_FromLong((long){cxx_i});
#else
                    {name} = PyInt_FromLong((long){cxx_i});
#endif""",
        HeldAs.FLOAT:
            """                {name} = PyFloat_FromDouble((double){cxx_i});""",
        HeldAs.POINTER:
            """                {name} = sipConvertFromType({cxx_i}, gen{name}T, sipTransferObj);""",
        HeldAs.OBJECT:
            """                {name} = sipConvertFromType(&{cxx_i}, gen{name}T, sipTransferObj);""",
    }

    py_to_cxx_templates = {
        HeldAs.INTEGER:
            """             #if PY_MAJOR_VERSION >= 3
                    (*cxx{name})[i] = (Cxx{name}T)PyLong_AsLong({name});
#else
                    (*cxx{name})[i] = (Cxx{name}T)PyInt_AsLong({name});
#endif""",
        HeldAs.FLOAT:
            """                (*cxx{name})[i] = (Cxx{name}T)PyFloat_AsDouble({name});""",
        HeldAs.POINTER:
            """        int {name}State;
        Cxx{name}T cxx{name} = NULL;
        cxx{name} = reinterpret_cast<Cxx{name}T>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr));""",
        HeldAs.OBJECT:
            """        int {name}State;
        Cxx{name}T *cxx{name} = NULL;
        cxx{name} = reinterpret_cast<Cxx{name}T *>(sipForceConvertToType({name}, gen{name}T, sipTransferObj, SIP_NOT_NONE, &{name}State, sipIsErr));""",
    }

    def cxx_to_py_template(self):
        return self.cxx_to_py_templates[self.category]

    def py_to_cxx_template(self):
        return self.py_to_cxx_templates[self.category]


class RewriteMappedHelper(HeldAs):
    cxx_to_py_templates = {
        HeldAs.INTEGER:
            """    Cxx{name}T cxx{name} = {cxx_i};
#if PY_MAJOR_VERSION >= 3
    PyObject *{name} = PyLong_FromLong((long)cxx{name});
#else
    PyObject *{name} = PyInt_FromLong((long)cxx{name});
#endif
""",
        HeldAs.FLOAT:
            """    Cxx{name}T cxx{name} = {cxx_i};
    PyObject *{name} = PyFloat_FromDouble((double)cxx{name});
""",
        HeldAs.POINTER:
            """    Cxx{name}T cxx{name} = {cxx_i};
    PyObject *{name} = sipConvertFromType(cxx{name}, gen{name}T, {transfer});
""",
        HeldAs.OBJECT:
            """    Cxx{name}T *cxx{name} = &{cxx_i};
    PyObject *{name} = sipConvertFromType(cxx{name}, gen{name}T, {transfer});
""",
    }

    py_to_cxx_templates = {
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

    def cxx_to_py_template(self):
        return self.cxx_to_py_templates[self.category]

    def py_to_cxx_template(self):
        return self.py_to_cxx_templates[self.category]


class FunctionParameterHelper(HeldAs):
    """
    Function parameter helper base class for FunctionWithTemplatesExpander.
    Use subclasses to customise the output from FunctionWithTemplatesExpander.
    """
    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        return "    Cxx{}T cxx{} = {};\n".format(name, name, cxx_i)

    def cxx_to_cxx(self, aN, original_type, is_out_paramter):
        code = ""
        if self.category == HeldAs.OBJECT:
            aN = "*" + aN
        elif is_out_paramter and not self.cxx_t.endswith("&"):
            aN = "&" + aN
        return code, aN

    def py_parameter(self, type, name, default, annotations):
        if not self.cxx_t.endswith(("*", "&", ">")):
            name = " " + name
        if default:
            return "{}{}{} = {}".format(self.cxx_t, name, annotations, default)
        else:
            return "{}{}{}".format(self.cxx_t, name, annotations)


class FunctionReturnHelper(HeldAs):
    """
    Function return value helper base class for FunctionWithTemplatesExpander.
    Use subclasses to customise the output from FunctionWithTemplatesExpander.
    """
    def declare_type_helpers(self, name, error):
        return super(FunctionReturnHelper, self).declare_type_helpers(name, error, need_cxx_t=False)

    cxx_to_py_templates = {
        HeldAs.INTEGER:
            """    {name} = {cxx_i};
#if PY_MAJOR_VERSION >= 3
    return PyLong_FromLong((long){name});
#else
    return PyInt_FromLong((long){name});
#endif
""",
        HeldAs.FLOAT:
            """    {name} = {cxx_i};
    return PyFloat_FromDouble((double){name});
""",
        HeldAs.POINTER:
            """    {name} = {cxx_i};
    return sipConvertFromType({name}, genresultT, {transfer});
""",
        HeldAs.OBJECT:
            """    {name} = &{cxx_i};
    return sipConvertFromType({name}, genresultT, {transfer});
""",
    }

    cxx_to_py_ptr_templates = {
        HeldAs.BYTE:
            """    {name} = {cxx_i};
    return PyString_FromStringAndSize((char *)({name}), 1);
""",
        HeldAs.INTEGER:
            """    {name} = {cxx_i};
#if PY_MAJOR_VERSION >= 3
    return PyLong_FromLong((long)*({name}));
#else
    return PyInt_FromLong((long)*({name}));
#endif
""",
        HeldAs.FLOAT:
            """    {name} = {cxx_i};
    return PyFloat_FromDouble((double)*({name}));
""",
    }

    def cxx_to_py_template(self):
        if self.category == HeldAs.POINTER and self.sip_t in [HeldAs.BYTE, HeldAs.FLOAT, HeldAs.POINTER]:
            return self.cxx_to_py_ptr_templates[self.sip_t]
        return self.cxx_to_py_templates[self.category]

    def py_fn_result(self, is_constructor):
        if not is_constructor and self.category == HeldAs.OBJECT and not self.cxx_t.endswith("&"):
            return self.cxx_t + " *"
        return self.cxx_t


class FunctionWithTemplatesExpander(object):
    """
    Automatic handling for functions with templated parameters and/or return types.
    """
    def __init__(self, parameter_helper, return_helper):
        """

        :param parameter_helper:            (Subclass of) FunctionParameterHelper.
        :param return_helper:               (Subclass of) FunctionReturnHelper.
        """
        super(FunctionWithTemplatesExpander, self).__init__()
        self.parameter_helper = parameter_helper
        self.return_helper = return_helper

    def expand_template(self, function, entries):
        """
        :param function:        The CursorKind for the function.
        :param entries:         Dictionary describing the C++ template. Expected keys:

                                    result          Is the return type integral, pointer or object?
                                    parameters      Is the parameter integral, pointer or object?
        """
        def in_class(item):
            parent = item.semantic_parent
            while parent and parent.kind != CursorKind.CLASS_DECL:
                parent = parent.semantic_parent
            return True if parent else False

        result = entries["result"]
        parameters = entries["parameters"]
        p_types = entries["p_types"]
        p_outs = entries["p_outs"]
        trace = entries["trace"]
        container = function.semantic_parent
        code = """%MethodCode
{}
""".format(trace)
        if function.is_pure_virtual_method():
            code += """    bool sipSelfWasArg = false;
"""
        #
        # Generate parameter list, wrapping shared data as needed.
        #
        sip_stars = []
        for i, parameter_h in enumerate(parameters):
            tmp, p = parameter_h.cxx_to_cxx("a{}".format(i), p_types[i], p_outs[i])
            code += tmp
            sip_stars.append(p)
        #
        # Generate function call, unwrapping shared data result as needed.
        #
        if function.kind == CursorKind.CONSTRUCTOR:
            fn = fqn(container, "")[:-2].replace("::", "_")
            callsite = """    Py_BEGIN_ALLOW_THREADS
    sipCpp = new sip{fn}({});
    Py_END_ALLOW_THREADS
"""
            callsite = callsite.replace("{fn}", fn)
            code += callsite.format(", ".join(sip_stars))
        else:
            fn = function.spelling
            if function.is_static_method() or not in_class(function):
                fn = fqn(container, fn)
                callsite = """    cxxvalue = {fn}({});
"""
            elif function.access_specifier == AccessSpecifier.PROTECTED:
                if function.is_virtual_method():
                    callsite = """#if defined(SIP_PROTECTED_IS_PUBLIC)
    cxxvalue = sipSelfWasArg ? sipCpp->{qn}{fn}({}) : sipCpp->{fn}({});
#else
    cxxvalue = sipCpp->sipProtectVirt_{fn}(sipSelfWasArg{sep}{});
#endif
"""
                    if parameters:
                        callsite = callsite.replace("{sep}", ", ", 1)
                    else:
                        callsite = callsite.replace("{sep}", "", 1)
                    callsite = callsite.replace("{qn}", fqn(container, ""))
                else:
                    callsite = """#if defined(SIP_PROTECTED_IS_PUBLIC)
    cxxvalue = sipCpp->{fn}({});
#else
    cxxvalue = sipCpp->sipProtect_{fn}({});
#endif
"""
            else:
                if function.is_virtual_method():
                    callsite = """    cxxvalue = sipSelfWasArg ? sipCpp->{qn}{fn}({}) : sipCpp->{fn}({});
"""
                    callsite = callsite.replace("{qn}", fqn(container, ""))
                else:
                    callsite = """    cxxvalue = sipCpp->{fn}({});
"""
            callsite = callsite.replace("{fn}", fn)
            callsite = callsite.replace("{}", ", ".join(sip_stars))
            callsite = """    Py_BEGIN_ALLOW_THREADS
""" + callsite + """    Py_END_ALLOW_THREADS
"""
            if result.category == HeldAs.VOID:
                code += callsite.replace("cxxvalue = ", "")
            else:
                code += """    typedef {} CxxvalueT;
    CxxvalueT cxxvalue;
""".format(entries["cxx_fn_result"]) + callsite
                code += result.declare_type_helpers("result", "return 0;")
                code += result.cxx_to_py("sipRes", False, "cxxvalue")
        code += """
%End
"""
        if function.is_virtual_method():
            code += """%VirtualCatcherCode
{}""".format(trace)
            #
            # Generate parameter list, unwrapping shared data as needed.
            #
            sip_stars = []
            sip_encodings = []
            for i, parameter_h in enumerate(parameters):
                p = "a{}".format(i)
                code += parameter_h.declare_type_helpers(p, "sipIsErr = 1;")
                code += parameter_h.cxx_to_py(p, False, p)

                #
                # Encoding map.
                #
                _encoding_map = {
                    HeldAs.BYTE: "c",
                    HeldAs.INTEGER: "n",
                    HeldAs.FLOAT: "d",
                    HeldAs.POINTER: "N",
                    HeldAs.OBJECT: "N",
                }
                _cast_map = {
                    HeldAs.BYTE: "(char)cxx{}",
                    HeldAs.INTEGER: "(long long)cxx{}",
                    HeldAs.FLOAT: "(double)cxx{}",
                    HeldAs.POINTER: "cxx{}, gen{}T, NULL",
                    HeldAs.OBJECT: "&cxx{}, gen{}T, NULL",
                }
                e = _encoding_map[parameter_h.category]
                v = _cast_map[parameter_h.category].format(p, p)
                sip_stars.append(v)
                sip_encodings.append(e)
            sip_stars = ['"' + "".join(sip_encodings) + '"'] + sip_stars
            code += """
    PyObject *result = sipCallMethod(&sipIsErr, sipMethod, {}, NULL);
    if (result == NULL) {{
        sipIsErr = 1;

        // TBD: Free all the pyobjects.
    }}""".format(", ".join(sip_stars))
            if result.category == HeldAs.VOID:
                pass
            else:
                code += """ else {
        // Convert the result to the C++ type. TBD: Figure out type encodings?
        sipParseResult(&sipIsErr, sipMethod, result, "i", &sipRes);
        Py_DECREF(result);
    }"""
            code += """
%End
"""
        return code

    def analyse_function(self, fn, cursor, sip):
        """
        Analyse a function, and return the results via the sip.

        :param fn:              The caller asking for the template expansion.
        :param cursor:          The CursorKind for whom the expansion is being performed.
                                This is the function whose parameters and/or return type
                                uses templates.
        :param sip:             The sip. Expected keys:

                                    decl            Optional. Name of the function.
                                    foo             dd
        """
        #
        # Initialise a C++ declaration.
        #
        annotations = []
        sip["cxx_parameters"] = []
        for p in sip["parameters"]:
            a = ANNOTATIONS_RE.search(p)
            if a:
                a = a.group()
                p = ANNOTATIONS_RE.sub("", p)
            else:
                a = ""
            annotations.append(a)
            sip["cxx_parameters"].append(p)
        sip["cxx_fn_result"] = sip["fn_result"]
        #
        # Deal with function result.
        #
        result_h = self.return_helper(sip["fn_result"], cursor.result_type.get_canonical().kind)
        sip["fn_result"] = result_h.py_fn_result(cursor.kind == CursorKind.CONSTRUCTOR)
        #
        # Now the function parameters.
        #
        clang_kinds = [c.type.get_canonical() for c in cursor.get_children() if c.kind == CursorKind.PARM_DECL]
        parameters = []
        p_types = []
        p_outs = []
        #
        # Generate parameter list, unwrapping shared data as needed.
        #
        for i, p in enumerate(sip["cxx_parameters"]):
            #
            # Get to type by removing any default value then stripping the name.
            #
            lhs, rhs = RE_PARAMETER_VALUE.split(p + "=")[:2]
            t, v = RE_PARAMETER_TYPE.match(lhs).groups()
            t = t.strip()
            parameter_h = self.parameter_helper(t, clang_kinds[i].kind)
            sip["parameters"][i] = parameter_h.py_parameter(t, v, rhs, annotations[i])
            parameters.append(parameter_h)
            p_types.append(t)
            p_outs.append("Out" in annotations[i])
        #
        # Run the template handler...
        #
        trace = trace_generated_for(cursor, fn, [(result_h.cxx_t, result_h.category),
                                                 [(p.cxx_t, p.category) for p in parameters]])
        entries = {
            "result": result_h,
            "parameters": parameters,
            "p_types": p_types,
            "p_outs": p_outs,
            "trace": trace,
            "cxx_fn_result": sip["cxx_fn_result"],
        }
        return entries


def container_rewrite_exception(container, sip, matcher):
    """
    Convert a class which is an exception into a %Exception.

    :param container:
    :param sip:
    :param matcher:
    :return:
    """
    sip["name"] = fqn(container.semantic_parent, sip["name"])
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


def container_rewrite_std_exception(container, sip, matcher):
    """
    Synthesise an %Exception for std::<exception>.

    :param container:
    :param sip:
    :param matcher:
    :return:
    """
    std_exception = sip["base_specifiers"][0]
    container_rewrite_exception(container, sip, matcher)
    sip_name = std_exception.replace("::", "_")
    py_name = "".join([w[0].upper() + w[1:] for w in sip_name.split("_")])
    sip["module_code"][std_exception] = """%Exception {}(SIP_Exception) /PyName={}/
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


def function_uses_templates(container, function, sip, matcher):
    """
    A FunctionDb-compatible function used to create %MethodCode expansions
    for C++ functions with templated return types and/or parameters.
    """
    #
    # No generated code for signals, SIP does not support that.
    #
    if sip["is_signal"]:
        return
    template = sip.get("template", FunctionWithTemplatesExpander)
    parameter_helper = sip.get("parameter_helper", FunctionParameterHelper)
    return_helper = sip.get("return_helper", FunctionReturnHelper)
    template = template(parameter_helper, return_helper)
    entries = template.analyse_function(function_uses_templates, function, sip)
    code = template.expand_template(function, entries)
    sip["code"] = code


def variable_rewrite_array_fixed(container, variable, sip, matcher):
    """
    Handle n-dimensional fixed size arrays.

    :param container:
    :param variable:
    :param sip:
    :param matcher:
    :return:
    """
    #
    # A template for a SIP_PYBUFFER.
    #
    _SIP_PYBUFFER_TEMPLATE = """
{
%GetCode
{trace}
    char *cxxvalue = (char *)&sipCpp->{name}[0];

    // Create the Python buffer.
    Py_ssize_t elementCount = {element_count};
    sipPy = PyByteArray_FromStringAndSize(cxxvalue, elementCount);
%End

%SetCode
{trace}
    char *cxxvalue = (char *)&sipCpp->{name}[0];
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
    }
%End
}"""

    #
    # A template for a SIP_PYLIST.
    #
    _SIP_PYLIST_TEMPLATE = """
{
%GetCode
{trace}
typedef {cxx_t} CxxvalueT;
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
    PyObject *list = getcode.getList(&sipErr, dims, numDims, 0, (CxxvalueT **)&sipCpp->{name}[0]);
    sipPy = sipErr ? list : NULL;
%End

%SetCode
{trace}
typedef {cxx_t} CxxvalueT;
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
    setcode.setList(&sipErr, dims, numDims, 0, sipPy, (CxxvalueT **)&sipCpp->{name}[0]);
%End
}"""

    dims = []
    next_type = variable.type
    while True:
        dims.append(next_type.element_count)
        element_type = next_type.element_type.get_canonical()
        if element_type.kind == TypeKind.CONSTANTARRAY:
            next_type = element_type
        else:
            converter = RewriteArrayHelper(sip["decl"], element_type.kind)
            if converter.category == HeldAs.BYTE:
                decl = "SIP_PYBUFFER"
                code = _SIP_PYBUFFER_TEMPLATE
            else:
                decl = "SIP_PYLIST"
                code = _SIP_PYLIST_TEMPLATE
                aliases_ = converter.declare_type_helpers("value", "*sipErr = 1;")
                cxx_to_py = converter.cxx_to_py("value", True, "(*cxxvalue)[i]")
                py_to_cxx = converter.py_to_cxx("value", True, "(*cxxvalue)[i]")
                code = code.replace("{cxx_t}", element_type.spelling)
                code = code.replace("{aliases}", aliases_)
                code = code.replace("{cxx_to_py}", cxx_to_py)
                code = code.replace("{py_to_cxx}", py_to_cxx)
            trace = trace_generated_for(variable, variable_rewrite_array_fixed, {})
            code = code.replace("{trace}", trace)
            break
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
        code = code.replace("{element_count}", str(next_type.element_count))
        code = code.replace("{name}", sip["name"])
        dims = ["(Py_ssize_t){}".format(i) for i in dims]
        code = code.replace("{dims}", ", ".join(dims))
        sip["code"] = code


def variable_rewrite_array_nonfixed(container, variable, sip, matcher):
    dims = VARIABLE_ARRAY_RE.match(sip["decl"]).groups()
    if len(dims) == 1:
        sip["decl"] = sip["decl"].replace("[]", "*")
    #
    # Even though we render this as a "foo *", it started life as a "foo []". So if there is a const, the array
    # itself was a const...
    #
    if "const " in sip["decl"]:
        sip["annotations"].add("NoSetter")


def variable_rewrite_extern(container, variable, sip, matcher):
    """
    SIP does not support "extern", so drop the keyword.

    :param container:
    :param variable:
    :param sip:
    :param matcher:
    :return:
    """
    sip["decl"] = sip["decl"][7:]
    if MAPPED_TYPE_RE.match(sip["decl"]):
        variable_rewrite_mapped(container, variable, sip, matcher)
    elif FIXED_ARRAY_RE.match(sip["decl"]):
        variable_rewrite_array_fixed(container, variable, sip, matcher)
    elif VARIABLE_ARRAY_RE.match(sip["decl"]):
        variable_rewrite_array_nonfixed(container, variable, sip, matcher)


def variable_rewrite_static(container, variable, sip, matcher):
    """
    SIP does not support "static", so handle static variables.

    :param container:
    :param variable:
    :param sip:
    :param matcher:
    :return:
    """
    while container.kind == CursorKind.NAMESPACE:
        container = container.semantic_parent
    if container.kind == CursorKind.TRANSLATION_UNIT:
        #
        # SIP does not support %GetCode/%SetCode for file scope variables. But luckily, just dropping the prefix works
        # assuming we don't actually need anything more complicated.
        #
        sip["decl"] = sip["decl"][7:]
        if FIXED_ARRAY_RE.match(sip["decl"]):
            variable_rewrite_array_fixed(container, variable, sip, matcher)
        elif VARIABLE_ARRAY_RE.match(sip["decl"]):
            variable_rewrite_array_nonfixed(container, variable, sip, matcher)
    else:
        #
        # Inside a class, "static" is fine. Do we need %GetCode/%SetCode?
        #
        if MAPPED_TYPE_RE.match(sip["decl"]):
            variable_rewrite_mapped(container, variable, sip, matcher)
        elif FIXED_ARRAY_RE.match(sip["decl"]):
            variable_rewrite_array_fixed(container, variable, sip, matcher)
        elif VARIABLE_ARRAY_RE.match(sip["decl"]):
            variable_rewrite_array_nonfixed(container, variable, sip, matcher)


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
    # Create a Python <-> C++ conversion helper.
    #
    variable_type = variable.type.get_canonical()
    converter = RewriteMappedHelper(variable_type.spelling, variable_type.kind)
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
    is_static = sip["decl"].startswith("static ")
    if is_static:
        cxx = fqn(container, "{name}")
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
    trace = trace_generated_for(variable, variable_rewrite_mapped, {})
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


def function_rules():
    return [
        #
        # Handle functions with templated return types and/or templated parameters.
        #
        [".*", ".*", ".*", "[A-Za-z0-9_]+<.*>", ".*", function_uses_templates],
        [".*", ".*", ".*", ".*", ".*[A-Za-z0-9_]+<.*>.*", function_uses_templates],
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
        [".*", ".*", FIXED_ARRAY_RE.pattern, variable_rewrite_array_fixed],
        #
        # Emit code for variable arrays.
        #
        [".*", ".*", VARIABLE_ARRAY_RE.pattern, variable_rewrite_array_nonfixed],
    ]
