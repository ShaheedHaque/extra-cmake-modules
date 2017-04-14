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
SIP binding customisation for PyKF5.KF5KDEGames. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rules_engine


def module_remove_redundant(filename, sip, matcher):
    lines = []
    for l in sip["decl"].split("\n"):
        if "KF5KDEGames/KF5KDEGamesmod.sip" in l:
            l = "// " + l
        lines.append(l)
    sip["decl"] = "\n".join(lines)


def _container_delete_base(container, sip, matcher):
    sip["base_specifiers"] = []


def _function_discard_class(container, function, sip, matcher):
    sip["fn_result"] = sip["fn_result"].replace("class ", "")


def _function_fully_qualify_parm(container, function, sip, matcher):
    sip["parameters"][0] = sip["parameters"][0].replace("FieldInfo", "KScoreDialog::FieldInfo")


def forward_declaration_rules():
    return [
        ["kg(ame|)difficulty.h", "KXmlGuiWindow", ".*", rules_engine.mark_forward_declaration_external],
    ]


def container_rules():
    return [
        ["KGamePropertyBase", "Flags", ".*", ".*", ".*", rules_engine.container_discard],
        #
        # SIP cannot handle inline templates like "class Foo: Bar<Baz>" without an intermediate typedef. For now,
        # delete the base class.
        #
        ["kchatbasemodel.h", "KChatBaseMessage", ".*", ".*", ".*", _container_delete_base],
    ]


def function_rules():
    return [
        ["KGameCanvasAbstract|KGameCanvasAdapter", "topLevelCanvas", ".*", ".*", ".*", _function_discard_class],
        #
        # Duplicate.
        #
        ["kgamerenderer.h", "qHash", ".*", ".*", ".*", rules_engine.function_discard],
        [".*", "GAMES_.*", ".*", "const QLoggingCategory &", ".*", rules_engine.function_discard],
        ["KScoreDialog", "addScore", ".*", ".*", ".*FieldInfo.*", _function_fully_qualify_parm],
    ]


def modulecode():
    return {
        "highscoremod.sip": {
            "code":
                """
                class KConfig /External/;
                class KgDifficulty /External/;
                """
        },
        "KDEmod.sip": {
            "code": module_remove_redundant
        }
    }
