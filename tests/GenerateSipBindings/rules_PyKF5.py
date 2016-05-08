
import os, sys

import rules_engine
sys.path.append(os.path.dirname(os.path.dirname(rules_engine.__file__)))
import Qt5Ruleset

from PyQt_template_typecode import HELD_AS, QList_cfttc, QMap_cfttc

def local_function_rules():
    return [
        ["MyObject", "fwdDecl", ".*", ".*", ".*", rules_engine.function_discard],
        ["MyObject", "fwdDeclRef", ".*", ".*", ".*", rules_engine.function_discard],
    ]

class RuleSet(Qt5Ruleset.RuleSet):
    def __init__(self, includes):
        Qt5Ruleset.RuleSet.__init__(self, includes)
        self._fn_db = rules_engine.FunctionRuleDb(lambda: local_function_rules() + Qt5Ruleset.function_rules())

        self._typecode = rules_engine.TypeCodeDb({
            "MyObject::MyIntegralMap": {
                "code": QMap_cfttc,
                "key": {
                    "type": "int",
                    "held_as": HELD_AS.INTEGRAL,
                },
                "value": {
                    "type": "int",
                    "held_as": HELD_AS.INTEGRAL,
                },
            },
            "MyObject::KeyBindingMap": {
                "code": QMap_cfttc,
                "key": {
                    "type": "MyObject::KeyBindingType",
                    "held_as": HELD_AS.INTEGRAL,
                },
                "value": {
                    "type": "QString",
                    "held_as": HELD_AS.OBJECT,
                },
            },
        })
