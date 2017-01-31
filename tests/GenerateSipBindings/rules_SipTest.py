
import os, sys

import rules_engine
sys.path.append(os.path.dirname(os.path.dirname(rules_engine.__file__)))
import Qt5Ruleset

def local_container_rules():
    return [
        [".*", "Shared", ".*", ".*", ".*", rules_engine.discard_QSharedData_base]
    ]

def local_forward_declaration_rules():
    return [
        [".*", "ExternalFwdDecl", ".*", rules_engine.mark_forward_declaration_external]
    ]

def local_function_rules():
    return [
        ["TypedefUser", "setTagPattern", ".*", ".*", ".*", rules_engine.function_discard],
    ]

def local_typedef_rules():
    return [
        [".*", "TagFormatter", rules_engine.typedef_discard],
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
                       modulecode=lambda : {
            "cpplib.h": {
            "code": """
%ModuleCode
int myAcumulate(const QList<int> *list) {
    return std::accumulate(list->begin(), list->end(), 0);
}
%End\n
            """
            }
            },
                        methodcode=lambda : {
            "SomeNS": {
                "customMethod": {
                    "code": """
                    %MethodCode
                        sipRes = myAcumulate(a0);
                    %End
                    """
                }
            },
            "cpplib.h": {
                "anotherCustomMethod": {
                    "code": methodGenerator,
                    "param": 42
                }
            }
            })
