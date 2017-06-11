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


def parameter_rewrite_quotes(container, function, parameter, sip, matcher):
    tmp = sip["init"].split('"')
    sip["init"] = tmp[0] + tmp[2]


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rules_engine.modulecode_delete(filename, sip, entry, "QList<int>")
    sip["code"] = """
%ModuleHeaderCode
class KConfig;
%End
"""


def forward_declaration_rules():
    return [
        ["(k|)highscore.h|kchatbase.h", "KConfig", ".*", rules_engine.container_mark_forward_declaration_external],
        ["kgame.h", "KRandomSequence", ".*", rules_engine.container_mark_forward_declaration_external],
        ["kgamethemeselector.h", "KConfigSkeleton", ".*", rules_engine.container_mark_forward_declaration_external],
        ["kstandardgameaction.h", "K(RecentFiles|Select|Toggle)Action", ".*", rules_engine.container_mark_forward_declaration_external],
        ["kg(ame|)difficulty.h", "KXmlGuiWindow", ".*", rules_engine.container_mark_forward_declaration_external],
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
        #
        # Duplicate.
        #
        ["kgamerenderer.h", "qHash", ".*", ".*", ".*", rules_engine.function_discard],
        [".*", "GAMES_.*", ".*", "const QLoggingCategory &", ".*", rules_engine.function_discard],
        ["KScoreDialog", "addScore", ".*", ".*", ".*FieldInfo.*", _function_fully_qualify_parm],
        ["KGamePropertyBase", "typeinfo", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # TBD: support various templates.
        #
        ["KGamePropertyHandler", "dict", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KMessageClient", "sendForward", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KMessageServer", "sendMessage", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # Delete non-const.
        #
        ["KGame", "(p|inactiveP)layerList", ".*", ".*", ".*", ".*", "(?! const)", rules_engine.function_discard],
        #
        # Unsupported signal argument type.
        #
        ["KGame", "signal(ReplacePlayerIO|LoadError)", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KGameIO", "signalPrepareTurn", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KGameKeyIO", "signalKeyEvent", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KGameMouseIO", "signalMouseEvent", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KGameProcessIO", "signalIOAdded", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KGamePropertyHandler", "signalSendMessage", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KMessageClient", "(forward|serverMessage)Received", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KMessageServer", "messageReceived", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # Suppress template stuff for now.
        #
        ["KGameProperty", "operator.*|typeinfo|value", ".*", ".*", ".*", rules_engine.function_discard],
    ]


def parameter_rules():
    return [
        #
        # Temporarily rewrite quote to workaround SIP 4.18.1 bug.
        # https://www.riverbankcomputing.com/pipermail/pyqt/2017-March/038989.html
        #
        ["KGameTheme", "KGameTheme", "themeGroup", ".*", ".*", parameter_rewrite_quotes],
        ["KGameThemeSelector", "KGameThemeSelector", "groupName|directory", ".*", ".*", parameter_rewrite_quotes],
        ["KgThemeProvider", "KgThemeProvider", "configKey", ".*", ".*", parameter_rewrite_quotes],
        #
        #  Override the default "parent" rule.
        #
        ["KStandardGameAction", ".*", "parent", ".*", ".*", rules_engine.noop]
    ]


def modulecode():
    return {
        "highscoremod.sip": {
            "code":
                """
                class KgDifficulty /External/;
                """
        },
        "libkdegamesprivatemod.sip": {
            "code":
                """
                class QMatrix /External/;
                """
        },
        "kgamemod.sip": {
            "code": module_fix_mapped_types,
        },
        "KDEmod.sip": {
            "code": module_remove_redundant
        }
    }
