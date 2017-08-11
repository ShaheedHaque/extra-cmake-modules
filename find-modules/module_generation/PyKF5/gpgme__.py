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
SIP binding customisation for PyKF5.gpgme__. This modules describes:

    * Supplementary SIP file generator rules.
"""
import re

import builtin_rules
import rule_helpers


def function_fix_callable(container, fn, sip, rule):
    rule_helpers.initialise_cxx_decl(sip)
    sip["parameters"][0] = sip["parameters"][0].replace("IdleFunction", "SIP_PYCALLABLE", 1)
    sip["fn_result"] = "SIP_PYCALLABLE"
    sip["code"] += """%MethodCode\n// TBD\n%End\n"""


def parameter_out(container, fn, parameter, sip, rule):
    sip["decl"] = "const char **" + parameter.spelling


def module_fix_includes(filename, sip, rule):
    rule_helpers.module_add_includes(filename, sip, rule, "<stdio.h>", "<gpg-error.h>")
    rule_helpers.module_add_classes(filename, sip, rule, "_IO_FILE")
    sip["code"] += "typedef int gpg_err_code_t;"


def module_fix_includes_if(filename, sip, rule):
    rule_helpers.module_add_includes(filename, sip, rule, "<gpgme++/error.h>", "<gpgme++/data.h>")


def module_fix_interfaces(filename, sip, rule):
    rule_helpers.module_add_classes(filename, sip, rule, "GpgME::Error", "GpgME::Data")


def module_fix_ordering(filename, sip, rule):
    """
    SIP does not properly support forward declaration. So we physically yank
    things into place.
    """
    child = "^    class " + sip["ctx"]["child"] + "\n    {.*?(^    };)$"
    parent = "^    class " + sip["ctx"]["parent"] + ";$"
    child = re.search(child, sip["decl"], re.DOTALL | re.MULTILINE)
    tmp = sip["decl"][:child.start(0)] + "// Yanked from here" + sip["decl"][child.end(0):]
    parent = re.search(parent, tmp, re.DOTALL | re.MULTILINE)
    sip["decl"] = tmp[:parent.start(0)] + "// Yanked to here\n" + child.group(0) + "\n" + tmp[parent.end(0):]


def container_rules():
    return [
        ["GpgME::Configuration", "Component", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
        ["GpgME::Configuration", "Option", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
        ["GpgME", "CreatedSignature|Import|Invalid(Recipient|SigningKey)|Key|Notation|Signature|Subkey|UserID", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
        ["GpgME::UserID", "Signature", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]


def forward_declaration_rules():
    return [
        ["global.h", "_GIOChannel", ".*", rule_helpers.noop],
        ["gpgmefw.h", ".*", ".*", rule_helpers.noop],
        ["GpgME::(Context|Data|(Signing|Import|Encryption)Result)", "Private", ".*", rule_helpers.noop],
        ["GpgME", "Import", ".*", rule_helpers.noop],
    ]


def function_rules():
    return [
        #
        # Remove unsupported signature.
        #
        ["GpgME::Configuration::(Argument|Component|Option)", "operator void.*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["GpgME::Error", "operator void.*", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # SIP needs help with std::basic_ostream<char>.
        #
        ["GpgME.*", "operator<<", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # SIP needs help with std::__cxx11::basic_string<char>.
        #
        ["GpgME::Configuration::Option", "createString(|List)Argument", ".*", ".*", ".*", rule_helpers.function_discard],
        ["GpgME::GpgAddUserIDEditInteractor", "set(Name|Email|Comment)Utf8", ".*", ".*", ".*", rule_helpers.function_discard],
        ["GpgME::GpgAddUserIDEditInteractor", "(name|email|comment)Utf8", ".*", ".*", ".*", rule_helpers.function_discard],
        ["GpgME::GpgSetExpiryTimeEditInteractor", "GpgSetExpiryTimeEditInteractor", ".*", ".*", ".*", rule_helpers.function_discard],
        ["GpgME::DefaultAssuanTransaction", "data", ".*", ".*", ".*", rule_helpers.function_discard],
        ["GpgME", "registerIdleFunction", ".*", ".*", ".*", function_fix_callable],
        ["GpgME::(Context|Data)", "impl", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        ["GpgME::InvalidRecipient", "InvalidRecipient", ".*", ".*", ".*", builtin_rules.function_uses_templates],
        ["GpgME::Import", "Import", ".*", ".*", ".*", builtin_rules.function_uses_templates],
        ["GpgME::Notation", "Notation", ".*", ".*", ".*", builtin_rules.function_uses_templates],
        ["GpgME::InvalidSigningKey", "InvalidSigningKey", ".*", ".*", ".*", builtin_rules.function_uses_templates],
        ["GpgME::CreatedSignature", "CreatedSignature", ".*", ".*", ".*", builtin_rules.function_uses_templates],
        ["GpgME::Signature", "Signature", ".*", ".*", ".*", builtin_rules.function_uses_templates],
        #
        # Get rid of de-facto private stuff.
        #
        ["GpgME::(Data|Key.*)", "Data|Key.*", ".*", ".*", ".*::Null.*", rule_helpers.function_discard],
    ]


def parameter_rules():
    return [
        ["GpgME::Context", "startKeyListing|exportPublicKeys|startPublicKeyExport", "pattern(s|)", ".*\[\]", ".*", parameter_out],
    ]


def variable_rules():
    return [
        #
        # Get rid of de-facto private stuff.
        #
        ["GpgME::(Data|Key)", "null", ".*", rule_helpers.variable_discard],
    ]


def modulecode():
    return {
        "gpgme++/decryptionresult.h": {
            "code": rule_helpers.module_yank_scoped_class,
            "ctx": {"child": "Recipient", "parent": "DecryptionResult"},
        },
        "gpgme++/key.h": {
            "code": rule_helpers.module_yank_scoped_class,
            "ctx": {"child": "Signature", "parent": "UserID"},
        },
        "gpgme++/importresult.h": {
            "code": module_fix_ordering,
            "ctx": {"child": "Import", "parent": "Import"},
        },
        "gpgme++/interfaces/assuantransaction.h": {
            "code": module_fix_includes_if,
        },
        "gpgme__/interfaces/interfacesmod.sip": {
            "code": module_fix_interfaces,
        },
        "gpgme__/gpgme__mod.sip": {
            "code": module_fix_includes,
        },
    }
