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
SIP binding customisation for PyKF5.KContacts. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers


def _container_discard_templated_bases_and_fake(container, sip, matcher):
    sip["base_specifiers"] = [b for b in sip["base_specifiers"] if "<" not in b]
    rule_helpers.container_fake_derived_class(container, sip, matcher)


def container_rules():
    return [
        ["KContacts", "Address", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
        ["KContacts", "AddresseeList", ".*", ".*", ".*", _container_discard_templated_bases_and_fake],
        ["KContacts", "PhoneNumber", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]


def function_rules():
    return [
        ["KContacts::ContactGroup", "contact.*Reference|data", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        ["KContacts::Field", "Field", ".*", ".*", ".*Private.*", ".*", ".*", rule_helpers.function_discard],
    ]


def modulecode():
    return {
        "KContactsmod.sip": {
            "code":
                """
                %If (!KContacts_KContacts_KContactsmod)
                class KConfigGroup /External/;
                %End
                """
        },
    }
