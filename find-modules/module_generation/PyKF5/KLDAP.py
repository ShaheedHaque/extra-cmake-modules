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
SIP binding customisation for PyKF5.KLDAP. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers
from PyQt_templates import list_typecode


def variable_customise(container, variable, sip, matcher):
    sip["code"] = """
{
%GetCode
#include <KLDAP/kldap/ldapoperation.h>
%End
%SetCode
#include <KLDAP/kldap/ldapoperation.h>
%End
}"""


def module_fix_mapped_types(filename, sip, entry):
    rule_helpers.modulecode_make_local(filename, sip, entry, "QList<QByteArray>", "QList<QModelIndex>")


def function_rules():
    return [
        ["KLDAP::LdapOperation", "bind|bind_s", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KLDAP::LdapUrl", "extension", ".*", "QString", ".*", rule_helpers.function_discard],
    ]


def variable_rules():
    return [
        ["KLDAP::LdapOperation.*", "proc", "SASL_Callback_Proc.*", variable_customise],
    ]


def modulecode():
    return {
        "KLDAP/KLDAP/KLDAPmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
