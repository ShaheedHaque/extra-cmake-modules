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
Generic SIP %MethodCode code for C++ functions which use templated parameters
and/or return types. The main content is:

    - The FunctionExpander class which is a model of how template expansion
      can be performed as needed.

    - Function{Parameter,Return}Helper base classes which implement customisation.

    - FunctionDb-compatible action (function_uses_templates) usable in
      RuleSets.

This is supported by other public methods and classes which can be used as
examples and/or helper code.
"""
import gettext
import logging
import os
import re

from clang.cindex import AccessSpecifier

import rule_helpers
from clangcparser import CursorKind
from rule_helpers import trace_generated_for, HeldAs, fqn, initialise_cxx_decl

gettext.install(os.path.basename(__file__))
logger = logging.getLogger(__name__)

# Keep PyCharm happy.
_ = _


RE_PARAMETER_VALUE = re.compile(r"\s*=\s*")
RE_PARAMETER_TYPE = re.compile(r"(.*[ >&*])(.*)")


class FunctionParameterHelper(HeldAs):
    """
    Function parameter helper base class for FunctionExpander.
    Use subclasses to customise the output from FunctionExpander.
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
        if not self.cxx_t.endswith(("*", "&")):
            name = " " + name
        if default:
            return "{}{}{} = {}".format(self.cxx_t, name, annotations, default)
        else:
            return "{}{}{}".format(self.cxx_t, name, annotations)


class FunctionReturnHelper(HeldAs):
    """
    Function return value helper base class for FunctionExpander.
    Use subclasses to customise the output from FunctionExpander.
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
    return sipConvertFromType((void *){name}, genresultT, {transfer});
""",
        HeldAs.OBJECT:
            #
            # The cast is needed because SIP sometimes declares sipRes without any const keyword.
            #
            """    {name} = const_cast<decltype({name})>(&{cxx_i});
    return sipConvertFromType((void *){name}, genresultT, {transfer});
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


class FunctionExpander(object):
    """
    Automatic handling for functions with templated parameters and/or return types.
    """
    def __init__(self, parameter_helper, return_helper):
        """

        :param parameter_helper:            (Subclass of) FunctionParameterHelper.
        :param return_helper:               (Subclass of) FunctionReturnHelper.
        """
        super(FunctionExpander, self).__init__()
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
            while parent and parent.kind not in [CursorKind.CLASS_DECL, CursorKind.TRANSLATION_UNIT]:
                parent = parent.semantic_parent
            return parent.kind == CursorKind.CLASS_DECL

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
        # TODO: When should the logic be bracketed by Py_BEGIN_ALLOW_THREADS/Py_END_ALLOW_THREADS
        # versus the form:
        #
        #    try
        #    {
        #        stuff;
        #    }
        #    catch(...)
        #    {
        #        sipRaiseUnknownException();
        #        return NULL;
        #    }
        #
        # is it to do with exception handling support in SIP?
        #
        if function.kind == CursorKind.CONSTRUCTOR:
            fn = fqn(function, "")[:-2].replace("::", "_")
            callsite = """    Py_BEGIN_ALLOW_THREADS
    sipCpp = new sip{fn}({args});
    Py_END_ALLOW_THREADS
"""
            callsite = callsite.replace("{fn}", fn)
            callsite = callsite.replace("{args}", ", ".join(sip_stars))
            code += callsite
        elif function.spelling.startswith("operator") and \
                function.spelling.endswith(("*=", "/=", "%=", "+=", "-=", ">>=", "<<=", "&=", "^=", "|=")):
            #
            # This is a compound assignment.
            #
            callsite = """    Py_BEGIN_ALLOW_THREADS
    sipCpp->{fn}({args});
    Py_END_ALLOW_THREADS
"""
            callsite = callsite.replace("{fn}", function.spelling)
            callsite = callsite.replace("{args}", ", ".join(sip_stars))
            code += callsite
        else:
            fn = function.spelling
            if function.is_static_method() or not in_class(function):
                fn = fqn(function)
                callsite = """    cxxvalue = {fn}({args});
"""
            elif function.access_specifier == AccessSpecifier.PROTECTED:
                if function.is_virtual_method():
                    callsite = """#if defined(SIP_PROTECTED_IS_PUBLIC)
    cxxvalue = sipSelfWasArg ? sipCpp->{qn}{fn}({args}) : sipCpp->{fn}({args});
#else
    cxxvalue = sipCpp->sipProtectVirt_{fn}(sipSelfWasArg{sep}{args});
#endif
"""
                    if parameters:
                        callsite = callsite.replace("{sep}", ", ", 1)
                    else:
                        callsite = callsite.replace("{sep}", "", 1)
                    callsite = callsite.replace("{qn}", fqn(function, ""))
                else:
                    callsite = """#if defined(SIP_PROTECTED_IS_PUBLIC)
    cxxvalue = sipCpp->{fn}({args});
#else
    cxxvalue = sipCpp->sipProtect_{fn}({args});
#endif
"""
            else:
                if function.is_virtual_method():
                    callsite = """    cxxvalue = sipSelfWasArg ? sipCpp->{qn}{fn}({args}) : sipCpp->{fn}({args});
"""
                    callsite = callsite.replace("{qn}", fqn(function, ""))
                else:
                    callsite = """    cxxvalue = sipCpp->{fn}({args});
"""
            callsite = callsite.replace("{fn}", fn)
            callsite = callsite.replace("{args}", ", ".join(sip_stars))
            code += """    Py_BEGIN_ALLOW_THREADS
"""
            if result.category == HeldAs.VOID:
                code += callsite.replace("cxxvalue = ", "")
            else:
                code += """    typedef {} CxxvalueT;
""".format(entries["cxx_fn_result"])
                code += callsite.replace("cxxvalue = ", "CxxvalueT cxxvalue = ")
                code += result.declare_type_helpers("result", "return 0;")
                code += result.cxx_to_py("sipRes", False, "cxxvalue")
            code += """    Py_END_ALLOW_THREADS
"""
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

    def analyse_function(self, rule, cursor, sip):
        """
        Analyse a function, and return the results via the sip.

        :param rule:            The caller asking for the template expansion.
        :param cursor:          The CursorKind for whom the expansion is being performed.
                                This is the function whose parameters and/or return type
                                uses templates.
        :param sip:             The sip. Expected keys:

                                    decl            Optional. Name of the function.
                                    foo             dd
        """
        annotations = initialise_cxx_decl(sip)
        #
        # Deal with function result.
        #
        result_h = self.return_helper(sip["fn_result"], cursor.result_type.get_canonical())
        sip["fn_result"] = result_h.py_fn_result(cursor.kind == CursorKind.CONSTRUCTOR)
        #
        # Now the function parameters.
        #
        clang_types = [c.type.get_canonical() for c in cursor.get_children() if c.kind == CursorKind.PARM_DECL]
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
            parameter_h = self.parameter_helper(t, clang_types[i])
            sip["parameters"][i] = parameter_h.py_parameter(t, v, rhs, annotations[i])
            parameters.append(parameter_h)
            p_types.append(t)
            p_outs.append("Out" in annotations[i])
        #
        # Run the template handler...
        #
        trace = trace_generated_for(cursor, rule, {"{}({})".format(result_h.cxx_t, result_h.category):
                                                       ["{}({})".format(p.cxx_t, p.category) for p in parameters]})
        entries = {
            "result": result_h,
            "parameters": parameters,
            "p_types": p_types,
            "p_outs": p_outs,
            "trace": trace,
            "cxx_fn_result": sip["cxx_fn_result"],
        }
        return entries


def function_uses_templates(container, function, sip, rule):
    """
    A FunctionDb-compatible function used to create %MethodCode expansions
    for C++ functions with templated return types and/or parameters.

    Rule writers can tailor the expansion using custom subclasses of
    FunctionExpander, FunctionParameterHelper and FunctionReturnHelper
    passed via sip attributes:

        - "template"            Provide the overall template.
        - "parameter_helper"    Tailored parameter handling.
        - "return_helper"       Tailored return value handling.
    """
    #
    # No generated code for signals, SIP does not support that.
    #
    if sip["is_signal"]:
        logger.warning(
        _("SIP does not support templated signals: {}").format(rule_helpers.item_describe(function)))
        return rule_helpers.SILENT_NOOP
    template = sip.get("template", FunctionExpander)
    parameter_helper = sip.get("parameter_helper", FunctionParameterHelper)
    return_helper = sip.get("return_helper", FunctionReturnHelper)
    template = template(parameter_helper, return_helper)
    entries = template.analyse_function(rule, function, sip)
    code = template.expand_template(function, entries)
    sip["code"] = code
