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

import rules_engine
import common_typecode


def parameter_rewrite_template(container, function, parameter, sip, matcher):
    sip["decl"] = "DragObjectFactory factory"


def forward_declaration_rules():
    return [
        ["kdatepicker.h", "KDateTable", ".*", rules_engine.mark_forward_declaration_external],
    ]


def function_rules():
    return [
        ["KRatingWidget", "ratingChanged|set.*Rating", ".*", ".*", "unsigned.*", rules_engine.function_discard],
    ]


def parameter_rules():
    return [
        ["KDragWidgetDecorator", "setDragObjectFactory", "factory", ".*", ".*", parameter_rewrite_template],
        #
        # Override the default "parent" rule.
        #
        ["KMessageBox", ".*", "parent", ".*", ".*", rules_engine.noop]
    ]


def modulecode():
    return {
        "KWidgetsAddonsmod.sip": {
            "code":
                """
                %Import(name=KConfigCore/KConfigCoremod.sip)
                """
        },
    }


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kratingwidget.h::KRatingWidget": {
            "code": common_typecode._kdeui_qobject_ctscc
        },
    }
