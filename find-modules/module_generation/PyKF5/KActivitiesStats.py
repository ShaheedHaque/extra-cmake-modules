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
SIP binding customisation for PyKF5.KActivitiesStats. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers


def _delete_duplicate_content(filename, sip, rule):
    sip["decl"] = ""


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QHash<int, QByteArray>")
    rule_helpers.module_add_classes(filename, sip, rule, "std::random_access_iterator_tag")
    #rule_helpers.module_add_includes(filename, sip, rule, "<iterator>")


def function_rules():
    return [
        #
        # Remove unsupported signature.
        #
        ["KActivities::Stats::Query", "Query", ".*", ".*", ".*&&.*", rule_helpers.function_discard],
        ["KActivities::Stats::ResultSet", "ResultSet", ".*", ".*", ".*&&.*", rule_helpers.function_discard],
        ["KActivities::Stats::ResultSet::Result", "Result", ".*", ".*", ".*&&.*", rule_helpers.function_discard],
        ["KActivities::Stats::ResultSet::const_iterator", "operator\*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KActivities::Stats::ResultSet::const_iterator", "operator->", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KActivities::Stats::ResultSet::const_iterator", "operator(-|\+).*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KActivities::Stats::ResultSet::const_iterator", "operator\[\]", ".*", ".*", ".*", rule_helpers.function_discard],
    ]


def modulecode():
    return {
        "KActivitiesStats/KActivities/Stats/Statsmod.sip": {
            "code": module_fix_mapped_types,
        },
        "KActivitiesStats/kactivitiesstats/cleaning.h": {
            "code": _delete_duplicate_content,
        },
        "KActivitiesStats/kactivitiesstats/query.h": {
            "code": _delete_duplicate_content,
        },
        "KActivitiesStats/kactivitiesstats/resultmodel.h": {
            "code": _delete_duplicate_content,
        },
        "KActivitiesStats/kactivitiesstats/resultset.h": {
            "code": _delete_duplicate_content,
        },
        "KActivitiesStats/kactivitiesstats/resultwatcher.h": {
            "code": _delete_duplicate_content,
        },
        "KActivitiesStats/kactivitiesstats/terms.h": {
            "code": _delete_duplicate_content,
        },
    }
