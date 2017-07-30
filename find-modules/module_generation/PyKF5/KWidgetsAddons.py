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
SIP binding customisation for PyKF5.KWidgetsAddons. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers
import common_typecode
import rules_engine


def _delete_duplicate_content(filename, sip, entry):
    if sip["name"] not in ["KMimeTypeChooser", "KMultiTabBar", "KPageWidgetModel", "KSelector"]:
        sip["decl"] = ""


def parameter_rewrite_template(container, function, parameter, sip, matcher):
    sip["decl"] = "DragObjectFactory factory"


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_make_local(filename, sip, entry, "QMap<QString, QString>")
    sip["code"] = """
%Import(name=KConfigCore/KConfigCoremod.sip)
"""


def forward_declaration_rules():
    return [
        ["kdatepicker.h", "KDateTable", ".*", rule_helpers.forward_declaration_mark_external],
    ]


def function_rules():
    return [
        ["KRatingWidget", "ratingChanged|set.*Rating", ".*", ".*", "unsigned.*", rule_helpers.function_discard],
        ["KPageDialog", "KPageDialog", ".*", ".*", "KPageDialogPrivate.*", rule_helpers.function_discard],
    ]


def parameter_rules():
    return [
        ["KDragWidgetDecorator", "setDragObjectFactory", "factory", ".*", ".*", parameter_rewrite_template],
        #
        # Override the default "parent" rule.
        #
        ["KMessageBox", ".*", "parent", ".*", ".*", rule_helpers.noop],
        ["KMessageBox", "createKMessageBox", "checkboxReturn", ".*", ".*", rule_helpers.parameter_out],
    ]


def modulecode():
    return {
        "KWidgetsAddonsmod.sip": {
            "code": module_fix_mapped_types,
        },
        "kmimetypechooser.h": {
            "code": _delete_duplicate_content
        },
        "kmultitabbar.h": {
            "code": _delete_duplicate_content
        },
        "kpagewidgetmodel.h": {
            "code": _delete_duplicate_content
        },
        "kselector.h": {
            "code": _delete_duplicate_content
        },
    }


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kratingwidget.h::KRatingWidget": {
            "code": common_typecode._kdeui_qobject_ctscc
        },
    }
