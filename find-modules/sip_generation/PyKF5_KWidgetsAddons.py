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
import PyKF5_typecode


def noop(*args):
    pass


def function_rules():
    return [
        ["KRatingWidget", "ratingChanged|set.*Rating", ".*", ".*", "unsigned.*", rules_engine.function_discard],
    ]


def parameter_rules():
    return [
        ["KStandardGuiItem", "back|forward", "useBidi", ".*", ".*", rules_engine.parameter_qualify_enum_initialiser],
        ["KMessageBox", ".*", "options", ".*", ".+", rules_engine.parameter_qualify_enum_initialiser],
        #
        # Override the default "parent" rule.
        #
        ["KMessageBox", ".*", "parent", ".*", ".*", noop]
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
            "code": PyKF5_typecode._kdeui_qobject_ctscc
        },
    }
