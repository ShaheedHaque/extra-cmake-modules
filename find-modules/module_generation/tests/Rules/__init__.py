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
SIP binding customisation for tests.
"""
import os

import builtin_rules
import rule_helpers
import rules_engine

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def container_discard_templated_bases(container, sip, matcher):
    sip["base_specifiers"] = []


def container_emit_modulecode(container, sip, matcher):
    container_discard_templated_bases(container, sip, matcher)
    sip["modulecode"][sip["name"]] = """
%ModuleHeaderCode
#define ModuleCodeTypeCheck 1
%End
"""


def function_emit_modulecode(container, function, sip, matcher):
    sip["modulecode"][sip["name"]] = """
%ModuleHeaderCode
#define ModuleCodeFunctionCheck 1
%End
"""
    sip["code"] = """
%MethodCode
#ifndef ModuleCodeTypeCheck
#error Could not find ModuleCodeTypeCheck
#endif
#ifndef ModuleCodeTypedefCheck
#error Could not find ModuleCodeTypedefCheck
#endif
#ifndef ModuleCodeFunctionCheck
#error Could not find ModuleCodeFunctionCheck
#endif
#ifndef ModuleCodeParameterCheck
#error Could not find ModuleCodeParameterCheck
#endif
%End
"""


def fn_cxx_decl(container, function, sip, matcher):
    builtin_rules.initialise_cxx_decl(sip)


def parameter_emit_modulecode(container, function, parameter, sip, matcher):
    sip["modulecode"][sip["name"]] = """
%ModuleHeaderCode
#define ModuleCodeParameterCheck 1
%End
"""


def parameter_in_out(container, function, parameter, sip, matcher):
    rule_helpers.parameter_out(container, function, parameter, sip, matcher)
    rule_helpers.parameter_in(container, function, parameter, sip, matcher)


def typedef_emit_modulecode(container, typedef, sip, matcher):
    sip["modulecode"][sip["name"]] = """
%ModuleHeaderCode
#define ModuleCodeTypedefCheck 1
%End
"""


def methodGenerator(function, sip, entry):
    sip["code"] = """
        %MethodCode
            sipRes = {} + myAcumulate(a0);
        %End
    """.format(entry["param"])


def container_rules():
    return [
        #
        # Discard Qt metatype system.
        #
        [".*", "(QMetaTypeId|QTypeInfo)", ".*", ".*", ".*", rule_helpers.container_discard],
        [".*", "Shared", ".*", ".*", ".*", rule_helpers.container_discard_QSharedData_base],
        [".*", "TemplateDerivative", ".*", ".*", ".*", container_discard_templated_bases],
        [".*", "ModuleCodeType", ".*", ".*", ".*", container_emit_modulecode],
    ]


def forward_declaration_rules():
    return [
        [".*", "ExternalFwdDecl", ".*", rule_helpers.forward_declaration_mark_external],
    ]


def function_rules():
    return [
        #
        # Discard functions emitted by QOBJECT.
        #
        [".*", "metaObject|qt_metacast|tr|trUtf8|qt_metacall|qt_check_for_QOBJECT_macro", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # SIP does not support operator=.
        #
        [".*", "operator=", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # TODO: Temporarily remove any functions which require std templates.
        #
        [".*", ".*", ".*", ".*", ".*std::function.*", rule_helpers.function_discard],
        [".*", ".*", ".*", ".*", ".*std::numeric_limits.*", rule_helpers.function_discard],
        ["TypedefUser", "setTagPattern", ".*", ".*", ".*", rule_helpers.function_discard],
        ["Sample1_1", "markedInOutCxxDecl", ".*", ".*", ".*", fn_cxx_decl],
    ]


def parameter_rules():
    return [
        ["Sample1_1", "markedInOut.*", "scursor", ".*", ".*", parameter_in_out],
        ["Sample1_1", "markedInOut.*", "result", ".*", ".*", rule_helpers.parameter_out],
    ]


def typedef_rules():
    return []


def unexposed_rules():
    return []


def variable_rules():
    return [
        #
        # Discard variable emitted by QOBJECT.
        #
        [".*", "staticMetaObject", ".*", rule_helpers.variable_discard],
    ]


def methodcode():
    return {
        "SomeNS": {
            "customMethod": {
                "code": """
                %MethodCode
                    sipRes = myAcumulate(a0);
                %End
                """
            }
        },
        "ObscureSyntax": {
            "defaultsAndParameterTemplate": {
                "code": """
                    %MethodCode
                    sipRes = ObscureSyntax::INCORRECT;
                    if ((*a0 == Qt::MatchWrap) &&
                        (*a1 == Qt::MatchFlags(Qt::MatchStartsWith | Qt::MatchWrap)) &&
                        (*a2 == (Qt::MatchStartsWith | Qt::MatchWrap)) &&
                        (a3 == 1) &&
                        (a4 == 2) &&
                        (a5 == 2) &&
                        (a6 == ObscureSyntax::INCORRECT) &&
                        (a7 == MyObject::Val2) &&
                        (a8.isEmpty()) &&
                        (a9 != NULL)) {
                        sipRes = ObscureSyntax::CORRECT;
                    }
                    %End
                    """,
                "cxx_decl": [
                    "Qt::MatchFlags flagsOne",
                    "Qt::MatchFlags flagsMultiple",
                    "int simple",
                    "int complex",
                    "int brackets",
                    "LocalEnum anEnum",
                    "QMap<const char *, int> chachacha"
                ],
                "cxx_fn_result": "int",
            },
            "returnTemplate": {
                "code": """
                    %MethodCode
                    sipRes = sipCpp->returnTemplate();
                    sipRes->insert("foo", ObscureSyntax::CORRECT);
                    %End
                    """,
                "cxx_decl": [
                ],
                "cxx_fn_result": "QMap<const char *, int> *",
            },
        },
        "cpplib.h": {
            "anotherCustomMethod": {
                "code": methodGenerator,
                "param": 42
            }
        }
    }


def modulecode():
    return {
        "cpplib.h": {
            "code": """
%ModuleHeaderCode
int myAcumulate(const QList<int> *list);
%End\n
%ModuleCode
int myAcumulate(const QList<int> *list) {
    return std::accumulate(list->begin(), list->end(), 0);
}
%End\n"""
        }

    }


def typecode():
    return {}


class RuleSet(rules_engine.RuleSet):
    """
    SIP file generator rules. This is a set of (short, non-public) functions
    and regular expression-based matching rules.
    """
    def __init__(self):
        super(RuleSet, self).__init__(
            container_rules=container_rules, forward_declaration_rules=forward_declaration_rules,
            function_rules=function_rules, parameter_rules=parameter_rules, typedef_rules=typedef_rules,
            unexposed_rules=unexposed_rules, variable_rules=variable_rules, methodcode=methodcode,
            modulecode=modulecode, typecode=typecode)
        self.pd_cache = None

    def _fill_cache(self):
        if self.pd_cache is None:
            self.pd_cache = rules_engine.get_platform_dependencies(os.path.dirname(os.path.realpath(__file__)))

    def _update_dir_set(self, result, key1, key2):
        self._fill_cache()
        for component, data in self.pd_cache[key1].items():
            dirlist = data[key2].split(";")
            dirlist = [os.path.normpath(i) for i in dirlist if i]
            result.update(dirlist)

    def cxx_source_root(self):
        return os.path.join(os.path.dirname(SCRIPT_DIR), "sources")

    def cxx_sources(self):
        return []

    def cxx_includes(self):
        source_root = self.cxx_source_root() + os.path.sep
        result = set()
        self._update_dir_set(result, "CXX_DEPENDENCIES", "INCLUDE_DIRS")
        #
        # We include anything which is not under the source root: those are dependencies too!
        #
        self._update_dir_set(result, "CXX_SOURCES", "INCLUDE_DIRS")
        result = [i for i in result if not i.startswith(source_root)]
        result = sorted(result)
        return result

    def cxx_compile_flags(self):
        QT5_COMPILE_FLAGS = ["-fPIC", "-std=gnu++14"]
        return QT5_COMPILE_FLAGS

    def cxx_libraries(self):
        result = set()
        self._update_dir_set(result, "CXX_SOURCES", "LIBRARIES")
        self._update_dir_set(result, "CXX_DEPENDENCIES", "LIBRARIES")
        result = [i for i in result]
        result = sorted(result)
        return result

    def sip_package(self):
        self._fill_cache()
        return self.pd_cache["SIP_PACKAGE"]

    def sip_imports(self):
        self._fill_cache()
        result = set()
        dirlist = self.pd_cache["SIP_DEPENDENCIES"].split(";")
        result.update(dirlist)
        result = [i for i in result if i]
        result = sorted(result)
        return result
