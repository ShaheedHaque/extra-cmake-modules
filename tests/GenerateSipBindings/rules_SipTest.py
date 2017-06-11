
import os, sys

import rules_engine
sys.path.append(os.path.dirname(os.path.dirname(rules_engine.__file__)))
import Qt5Ruleset


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


def parameter_emit_modulecode(container, function, parameter, sip, matcher):
    sip["modulecode"][sip["name"]] = """
%ModuleHeaderCode
#define ModuleCodeParameterCheck 1
%End
"""


def typedef_emit_modulecode(container, typedef, sip, matcher):
    sip["modulecode"][sip["name"]] = """
%ModuleHeaderCode
#define ModuleCodeTypedefCheck 1
%End
"""


def local_container_rules():
    return [
        [".*", "(QMetaTypeId|QTypeInfo)", ".*", ".*", ".*", rules_engine.container_discard],
        [".*", "Shared", ".*", ".*", ".*", rules_engine.container_discard_QSharedData_base],
        [".*", "TemplateDerivative", ".*", ".*", ".*", container_discard_templated_bases],
        [".*", "ModuleCodeType", ".*", ".*", ".*", container_emit_modulecode],
    ]


def local_forward_declaration_rules():
    return [
        [".*", "ExternalFwdDecl", ".*", rules_engine.container_mark_forward_declaration_external],
    ]


def local_function_rules():
    return [
        ["TypedefUser", "setTagPattern", ".*", ".*", ".*", rules_engine.function_discard],
        [".*", "moduleCodeFunction", ".*", ".*", ".*", function_emit_modulecode],
    ]


def local_parameter_rules():
    return [
        [".*", "moduleCodeParameter", ".*", ".*", ".*", parameter_emit_modulecode],
    ]


def local_typedef_rules():
    return [
        [".*", "TagFormatter", rules_engine.typedef_discard],
        [".*", "ModuleCodeTypedef", typedef_emit_modulecode],
    ]


def methodGenerator(function, sip, entry):
    sip["code"] = """
        %MethodCode
            sipRes = {} + myAcumulate(a0);
        %End
    """.format(entry["param"])


class RuleSet(Qt5Ruleset.RuleSet):
    def __init__(self):
        super(RuleSet, self).__init__()
        self.add_rules(container_rules=local_container_rules, forward_declaration_rules=local_forward_declaration_rules,
                       function_rules=local_function_rules, typedef_rules=local_typedef_rules,
                       parameter_rules=local_parameter_rules, modulecode=lambda : {
            "cpplib.h": {
            "code": """
%ModuleHeaderCode
int myAcumulate(const QList<int> *list);
%End\n
%ModuleCode
int myAcumulate(const QList<int> *list) {
    return std::accumulate(list->begin(), list->end(), 0);
}
%End\n
            """
            }
            })

        self._methodcode = rules_engine.MethodCodeDb({
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
            })
