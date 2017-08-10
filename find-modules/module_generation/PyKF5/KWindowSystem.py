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
SIP binding customisation for PyKF5.KWindowSystem. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def function_get_array(container, function, sip, rule):
    rule_helpers.initialise_cxx_decl(sip)
    sip["fn_result"] = "SIP_PYLIST"
    sip["code"] += """%MethodCode
// TBD
%End
"""


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<int>")
    rule_helpers.module_add_classes(filename, sip, rule, "_XEvent", "xcb_generic_event_t", "xcb_key_press_event_t",
                                    "xcb_connection_t", "_XDisplay", "xcb_window_t")


def module_fix_mapped_types_private(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QSize>", "QList<unsigned long long>")
    rule_helpers.module_add_classes(filename, sip, rule, "_XEvent", "xcb_generic_event_t", "xcb_key_press_event_t",
                                    "xcb_connection_t", "_XDisplay", "xcb_window_t")


def container_rules():
    return [
        ["kwindowinfo_p.h", "KWindowInfoPrivate", ".*", ".*", ".*", rule_helpers.container_discard_QSharedData_base],
        ["kwindowinfo.h", "KWindowInfo", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]


def function_rules():
    return [
        ["KStartupInfo", "KStartupInfo", ".*", ".*", "bool.*", rule_helpers.function_discard],
        ["NETRootInfo", "(clientList(|Stacking))|virtualRoots", ".*", ".*", ".*", function_get_array],
        ["NETWinInfo", "iconSizes", ".*", ".*", ".*", function_get_array],
        #
        # SIP unsupported signal argument type.
        #
        ["KWindowSystem", "windowChanged", ".*", ".*", ".*", rule_helpers.function_discard],
    ]


def modulecode():
    return {
        "KWindowSystem/KWindowSystemmod.sip": {
            "code": module_fix_mapped_types,
        },
        "KWindowSystem/private/privatemod.sip": {
            "code": module_fix_mapped_types_private,
        },
    }
