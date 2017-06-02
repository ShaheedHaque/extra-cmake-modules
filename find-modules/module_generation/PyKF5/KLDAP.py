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

import rules_engine
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


def function_rules():
    return [
        ["KLDAP::LdapOperation", "bind|bind_s", ".*", ".*", ".*", rules_engine.function_discard],
        ["KLDAP::LdapUrl", "extension", ".*", "QString", ".*", rules_engine.function_discard],
    ]


def variable_rules():
    return [
        ["KLDAP::LdapOperation.*", "proc", "SASL_Callback_Proc.*", variable_customise],
    ]
