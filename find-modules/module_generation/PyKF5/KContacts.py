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


def function_rules():
    return [
        ["KContacts::ContactGroup", "contact.*Reference|data", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        ["KContacts::Field", "Field", ".*", ".*", ".*Private.*", ".*", ".*", rule_helpers.function_discard],
    ]


def typecode():
    return {
        "KContacts::Address": {
            "code":
                """
                %TypeHeaderCode
                // SIP does not always generate a derived class. Fake one!
                #define sipKContacts_Address KContacts::Address
                %End
                """
        },
        "KContacts::AddresseeList": {
            "code":
                """
                %TypeHeaderCode
                // SIP does not always generate a derived class. Fake one!
                #define sipKContacts_AddresseeList KContacts::AddresseeList
                %End
                """
        },
        "KContacts::PhoneNumber": {
            "code":
                """
                %TypeHeaderCode
                // SIP does not always generate a derived class. Fake one!
                #define sipKContacts_PhoneNumber KContacts::PhoneNumber
                %End
                """
        },
    }


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
