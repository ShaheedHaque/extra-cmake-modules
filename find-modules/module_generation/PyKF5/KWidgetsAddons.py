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
    sip["decl"] = ""


def parameter_rewrite_template(container, function, parameter, sip, matcher):
    sip["decl"] = "DragObjectFactory factory"


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_make_local(filename, sip, rule, "QMap<QString, QString>")
    rule_helpers.modulecode_delete(filename, sip, rule, "QPair<int, int>", "QVector<unsigned int>")
    rule_helpers.module_add_imports(filename, sip, rule, "KConfigCore/KConfigCoremod.sip")


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
        "KWidgetsAddons/KWidgetsAddonsmod.sip": {
            "code": module_fix_mapped_types,
        },
        "KWidgetsAddons/KMimeTypeChooserDialog": {
            "code": _delete_duplicate_content
        },
        "KWidgetsAddons/KMultiTabBarButton": {
            "code": _delete_duplicate_content
        },
        "KWidgetsAddons/KMultiTabBarTab": {
            "code": _delete_duplicate_content
        },
        "KWidgetsAddons/KPageWidgetItem": {
            "code": _delete_duplicate_content
        },
        "KWidgetsAddons/KGradientSelector": {
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

def methodcode():
    return {
        "KFontChooser": {
            "KFontChooser": {
                #
                # SIP needs help with the semantics of argument 5.
                #
                "parameters": [
                    "QWidget *parent /TransferThis/ = nullptr",
                    "const QFlags<KFontChooser::DisplayFlag> &flags = KFontChooser::DisplayFrame",
                    "const QStringList &fontList = QStringList()",
                    "int visibleListSize = 8",
                    "SIP_PYOBJECT sizeIsRelativeState = nullptr"
                ],
                "code":
                    """
                    %MethodCode
                        Py_BEGIN_ALLOW_THREADS
                        ::Qt::CheckState *cxxa4 = nullptr;
                        if (a4 != nullptr) {
                            int a4Err;
                            cxxa4 = static_cast<decltype(cxxa4)>(sipForceConvertToType(a4, sipType_Qt_CheckState, NULL, SIP_NOT_NONE, NULL, &a4Err));
                            if (a4Err) {
                                sipError = sipBadCallableArg(4, a4);
                                return NULL;
                            }
                        }
                        sipCpp = new sipKFontChooser(a0, *a1, *a2, a3, cxxa4);
                        Py_END_ALLOW_THREADS
                    %End
                    """
            },
        },
    }
