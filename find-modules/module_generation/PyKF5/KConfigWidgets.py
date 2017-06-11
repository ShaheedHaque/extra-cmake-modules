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
SIP binding customisation for PyKF5.KConfigWidgets. This modules describes:

    * Supplementary SIP file generator rules.
"""


import rules_engine


def _function_rewrite_using_decl(container, function, sip, matcher):
    sip["parameters"] = ["QAction* action"]
    sip["code"] = """    //void triggered(int index);
    void triggered(const QString &text);
"""


def _delete_duplicate_content(filename, sip, entry):
    if sip["name"] == "ktip.h":
        sip["decl"] = ""


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    del sip["modulecode"]["QList<QVariant>"]


def function_rules():
    return [
        #
        # Rewrite using declaration.
        #
        ["KCodecAction", "triggered", ".*", ".*", "", _function_rewrite_using_decl],
    ]


def parameter_rules():
    return [
        #
        # Override the default "parent" rule.
        #
        ["KStandardAction", ".*", "parent", ".*", ".*", rules_engine.noop]
    ]


def typecode():
    return {
        "kcolorscheme.h::KStatefulBrush": {
            "code":
                """
                %TypeHeaderCode
                // SIP does not always generate a derived class. Fake one!
                #define sipKStatefulBrush KStatefulBrush
                %End
                """
        },
    }


def modulecode():
    return {
        "ktipdialog.h": {
            "code": _delete_duplicate_content
        },
        "KConfigWidgetsmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
