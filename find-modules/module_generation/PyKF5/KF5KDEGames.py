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

import rule_helpers
import rules_engine


def module_remove_redundant(filename, sip, matcher):
    lines = []
    for l in sip["decl"].split("\n"):
        if "KF5KDEGames/KF5KDEGamesmod.sip" in l:
            l = "// " + l
        lines.append(l)
    sip["decl"] = "\n".join(lines)


def _function_discard_class(container, function, sip, matcher):
    sip["fn_result"] = sip["fn_result"].replace("class ", "")


def _function_fully_qualify_parm(container, function, sip, matcher):
    sip["parameters"][0] = sip["parameters"][0].replace("FieldInfo", "KScoreDialog::FieldInfo")


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<int>")
    rule_helpers.module_add_classes(filename, sip, entry, "KConfig", "QMatrix")


def module_fix_mapped_types_private(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QMap<QByteArray, QString>", "QMap<int, QByteArray>",
                                   "QPair<QByteArray, QString>")
    rule_helpers.module_add_classes(filename, sip, entry, "QMatrix /External/")


def forward_declaration_rules():
    return [
        ["(k|)highscore.h|kchatbase.h", "KConfig", ".*", rule_helpers.forward_declaration_mark_external],
        ["kgame.h", "KRandomSequence", ".*", rule_helpers.forward_declaration_mark_external],
        ["kgamethemeselector.h", "KConfigSkeleton", ".*", rule_helpers.forward_declaration_mark_external],
        ["kstandardgameaction.h", "K(RecentFiles|Select|Toggle)Action", ".*", rule_helpers.forward_declaration_mark_external],
        ["kg(ame|)difficulty.h", "KXmlGuiWindow", ".*", rule_helpers.forward_declaration_mark_external],
    ]


def container_rules():
    return [
        ["KGamePropertyBase", "Flags", ".*", ".*", ".*", rule_helpers.container_discard],
    ]


def function_rules():
    return [
        #
        # Duplicate.
        #
        ["kgamerenderer.h", "qHash", ".*", ".*", ".*", rule_helpers.function_discard],
        [".*", "GAMES_.*", ".*", "const QLoggingCategory &", ".*", rule_helpers.function_discard],
        ["KScoreDialog", "addScore", ".*", ".*", ".*FieldInfo.*", _function_fully_qualify_parm],
        ["KGamePropertyBase", "typeinfo", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # TBD: support various templates.
        #
        ["KGamePropertyHandler", "dict", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KMessageClient", "sendForward", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KMessageServer", "sendMessage", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Delete non-const.
        #
        ["KGame", "(p|inactiveP)layerList", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        #
        # Unsupported signal argument type.
        #
        ["KGame", "signal(ReplacePlayerIO|LoadError)", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KGameIO", "signalPrepareTurn", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KGameKeyIO", "signalKeyEvent", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KGameMouseIO", "signalMouseEvent", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KGameProcessIO", "signalIOAdded", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KGamePropertyHandler", "signalSendMessage", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KMessageClient", "(forward|serverMessage)Received", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KMessageServer", "messageReceived", ".*", ".*", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Suppress template stuff for now.
        #
        ["KGameProperty", "operator.*|typeinfo|value", ".*", ".*", ".*", rule_helpers.function_discard],
    ]


def parameter_rules():
    return [
        #
        #  Override the default "parent" rule.
        #
        ["KStandardGameAction", ".*", "parent", ".*", ".*", rule_helpers.noop]
    ]


def modulecode():
    return {
        "KF5KDEGames/highscore/highscoremod.sip": {
            "code":
                """
                class KgDifficulty /External/;
                """
        },
        "KF5KDEGames/libkdegamesprivate/libkdegamesprivatemod.sip": {
            "code": module_fix_mapped_types_private,
        },
        "KF5KDEGames/libkdegamesprivate/kgame/kgamemod.sip": {
            "code": module_fix_mapped_types,
        },
        "KF5KDEGames/KDE/KDEmod.sip": {
            "code": module_remove_redundant
        }
    }
