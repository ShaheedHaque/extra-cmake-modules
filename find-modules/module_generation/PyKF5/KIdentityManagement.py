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
SIP binding customisation for PyKF5.KIdentityManagement. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def container_fix_types(container, sip, rule):
    clazz = "QList<KIdentityManagement::Identity>"
    rule_helpers.container_add_typedefs(container, sip, rule, clazz + "::Iterator",
                                        clazz + "::ConstIterator", clazz + "::iterator",
                                        clazz + "::const_iterator")


def module_fix_mapped_types(filename, sip, rule):
    rule_helpers.modulecode_delete(filename, sip, rule, "QSet<QString>")
    rule_helpers.module_add_classes(filename, sip, rule, "KPIMTextEdit::RichTextComposer")


def container_rules():
    return [
        ["KIdentityManagement", "IdentityManager", ".*", ".*", ".*", container_fix_types],
    ]


def modulecode():
    return {
        "KIdentityManagement/KIdentityManagement/KIdentityManagementmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
