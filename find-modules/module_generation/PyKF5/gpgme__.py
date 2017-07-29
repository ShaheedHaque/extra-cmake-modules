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
import rule_helpers


def container_fix_includes(container, sip, matcher):
    rule_helpers.container_add_supplementary_includes(container, sip, matcher, "<gpgme++/error.h>", "<gpgme++/data.h>")


def parameter_out(container, function, parameter, sip, matcher):
    sip["decl"] = "const char **" + parameter.spelling


def module_fix_interfaces(filename, sip, matcher):
    rule_helpers.module_add_classes(filename, sip, matcher, "GpgME::Error", "GpgME::Data")


def container_rules():
    return [
        #
        # Remove unsupported signature.
        #
        ["GpgME", "AssuanTransaction", ".*", ".*", ".*", container_fix_includes],
    ]


def function_rules():
    return [
        #
        # Remove unsupported signature.
        #
        ["GpgME::Configuration::(Argument|Component|Option)", "operator void.*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["GpgME::Error", "operator void.*", ".*", ".*", ".*", rule_helpers.function_discard],
    ]


def parameter_rules():
    return [
        ["GpgME::Context", "startKeyListing|exportPublicKeys|startPublicKeyExport", "pattern(s|)", ".*\[\]", ".*", parameter_out],
    ]


def modulecode():
    return {
        "interfacesmod.sip": {
            "code": module_fix_interfaces,
        },
    }
