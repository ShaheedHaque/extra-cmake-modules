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


def function_fully_qualify(container, function, sip, matcher):
    sip["fn_result"] = sip["fn_result"].replace("Ldap", "KLDAP::Ldap")


def parameter_rewrite_fn_ptr(container, function, parameter, sip, matcher):
    sip["decl"] = "KLDAP::LdapOperation::SASL_Callback_Proc saslproc"


def parameter_rewrite_vector(container, function, parameter, sip, matcher):
    sip["decl"] = "ModOps ops"


def typedef_list_typecode(container, typedef, sip, matcher):
    sip["types"] = ["KLDAP::LdapOperation::ModOp"]
    sip["base_types"] = ["KLDAP::LdapOperation::ModOp"]
    list_typecode(container, typedef, sip, matcher)


def variable_fully_qualify(container, variable, sip, matcher):
    sip["decl"] = "KLDAP::LdapOperation::" + sip["decl"]


def variable_customise(container, variable, sip, matcher):
    sip["decl"] = "KLDAP::LdapOperation::SASL_Callback_Proc"
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
        #
        # Fully qualify names.
        #
        ["KLDAP::LdapOperation", "clientControls|serverControls|controls", ".*", ".*", ".*", function_fully_qualify],
        ["KLDAP::LdapObject", "attributes|values", ".*", ".*", ".*", function_fully_qualify],
        ["KLDAP::LdapServer", "scope", ".*", ".*", ".*", function_fully_qualify],
        ["KLDAP::LdapOperation", "bind|bind_s", ".*", ".*", ".*", rules_engine.function_discard],
        ["KLDAP::LdapUrl", "extension", ".*", "QString", ".*", rules_engine.function_discard],
    ]


def parameter_rules():
    return [
        #
        # Rewrite function pointer to use the typedef.
        #
        ["KLDAP::LdapOperation", "bind|bind_s", "saslproc", ".*", ".*", parameter_rewrite_fn_ptr],
        ["KLDAP::LdapOperation", "add|add_s|modify|modify_s", "ops", ".*", ".*", parameter_rewrite_vector],
    ]


def variable_rules():
    return [
        #
        # Fully qualify names.
        #
        ["KLDAP::LdapOperation.*", "type", "ModType", variable_fully_qualify],
        ["KLDAP::LdapOperation.*", "proc", "SASL_Callback_Proc.*", variable_customise],
    ]


def typedef_rules():
    return [
        #
        # De-anonymise structs.
        #
        ["KLDAP::LdapOperation", ".*", ".*", "QVector<.*>", typedef_list_typecode],
    ]
