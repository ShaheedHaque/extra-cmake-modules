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
SIP binding customisation for PyKF5.Attica. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def container_fix_typename(container, sip, rule):
    rule_helpers.container_add_typedefs(container, sip, rule, "typename T::List")


def module_fix_mapped_types(filename, sip, rule):
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QUrl>")
    rule_helpers.module_add_imports(filename, sip, rule, "Attica/attica/atticamod.sip")


def container_rules():
    return [
        #
        # SIP cannot handle "typename ...".
        #
        ["Attica", "ListJob", ".*", ".*", ".*", container_fix_typename],
    ]


def function_rules():
    return [
        ["Attica::DownloadDescription", "id|type|isDownloadtypLink|hasPrice|category|name|link|distributionType"
                                        "|priceReason|priceAmount|size|gpgFingerprint|gpgSignature|packageName"
                                        "|repository", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        ["Attica::Provider", "hasCredentials", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        ["Attica::Provider", "voteForContent", ".*", ".*", ".*bool positiveVote", rule_helpers.function_discard],
    ]


def typedef_rules():
    return [
        #
        # SIP thinks there are duplicate signatures.
        #
        ["postjob.h", "StringMap", ".*", ".*", rule_helpers.typedef_discard],
    ]


def modulecode():
    return {
        "Attica/Attica/Atticamod.sip": {
            "code": module_fix_mapped_types,
        },
    }