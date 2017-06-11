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
SIP binding customisation for PyKF5.KNotifications. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rules_engine


def _function_rewrite_using_decl(container, function, sip, matcher):
    sip["parameters"] = ["QEvent *event"]
    sip["fn_result"] = "bool"
    sip["prefix"] = "virtual "


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rules_engine.modulecode_delete(filename, sip, entry, "QPair<QString, QString>", "QList<QUrl>",
                                        "QList<QVariant>")


def function_rules():
    return [
        #
        # Rewrite using declaration.
        #
        ["KNotification", "event", ".*", ".*", "", _function_rewrite_using_decl],
    ]


def typecode():
    return {
        "knotifyconfig.h::KNotifyConfig": {
            "code":
                """
                %TypeHeaderCode
                // SIP does not always generate a derived class. Fake one!
                #define sipKNotifyConfig KNotifyConfig
                %End
                """
        },
    }


def modulecode():
    return {
        "KNotificationsmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
