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
SIP binding customisation for PyKF5.Akonadi. This modules describes:

    * Supplementary SIP file generator rules.
"""

import builtin_rules
import rules_engine


def _parameter_restore_default(container, function, paramter, sip, matcher):
    sip["init"] = "Q_NULLPTR"


def typedef_discard(container, typedef, sip, matcher):
    sip["name"] = ""


def _unexposed_discard(container, unexposed, sip, matcher):
    sip["name"] = ""


def _variable_array_to_star(container, variable, sip, matcher):
    builtin_rules.variable_rewrite_array_nonfixed(container, variable, sip, matcher)
    builtin_rules.variable_rewrite_extern(container, variable, sip, matcher)


def container_rules():
    return [
        #
        # SIP does not seem to be able to handle empty containers.
        #
        ["Akonadi::AkonadiCore", "Monitor|Protocol", ".*", ".*", ".*", rules_engine.container_discard],
    ]


def typedef_rules():
    return [
        #
        # SIP thinks there are duplicate signatures.
        #
        [".*", "QVariantMap", ".*", ".*", rules_engine.typedef_discard],
    ]


def unexposed_rules():
    return [
        #
        # Discard ....
        #
        ["Akonadi", ".*", ".*Item::setPayloadImpl.*", rules_engine.unexposed_discard],
        ["Akonadi", ".*", ".*std::enable_if.*", rules_engine.unexposed_discard],
        ["exception.h", ".*", ".*AKONADI_EXCEPTION_MAKE_TRIVIAL_INSTANCE.*", rules_engine.unexposed_discard],
    ]


def variable_rules():
    return [
        #
        # [] -> *
        #
        ["Akonadi::ContactPart", ".*", ".*", _variable_array_to_star],
        ["Akonadi::Item", "FullPayload", ".*", _variable_array_to_star],
        ["Akonadi::MessageFlags", ".*", ".*", _variable_array_to_star],
        ["Akonadi::MessagePart", ".*", ".*", _variable_array_to_star],
        ["Akonadi::Tag", "PLAIN|GENERIC", ".*", _variable_array_to_star],
    ]
