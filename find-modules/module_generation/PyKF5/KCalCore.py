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
SIP binding customisation for PyKF5.KCalCore. This modules describes:

    * Supplementary SIP file generator rules.
"""

import os

import rule_helpers


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_make_local(filename, sip, entry, "QMap<QByteArray, QString>")
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<int>", "QList<T>")
    rule_helpers.module_add_classes(filename, sip, entry, "KTimeZone", "KTimeZoneBackend", "KTimeZoneData",
                                    "KTimeZoneSource", "icalcomponent_impl", "_icaltimezone", "KCalCore::_MSSystemTime",
                                    "KCalCore::_MSTimeZone", "KDateTime", "KDateTime::Spec",
                                    # Uncommenting this causes SIP to crash.
                                    # "VObject",
                                    "QLatin1String")


def typedef_duplicate_discard(container, typedef, sip, matcher):
    """
    There are multiple definitions like this:

        typedef KCalCore::SortableList<KDateTime> DateTimeList;

    We need to get rid of the second one.
    """
    filename = os.path.basename(container.translation_unit.spelling)
    if filename != "incidencebase.h":
        rule_helpers.typedef_discard(container, typedef, sip, matcher)


def container_rules():
    return [
        #
        # Duplicate Akonadi::SuperClass.
        #
        ["(event|journal|todo).h", "Akonadi", ".*", ".*", ".*", rule_helpers.container_discard],
    ]


def function_rules():
    return [
        #
        # Delete non-const.
        #
        ["KCalCore::Attendee", "customProperties", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        #
        # SIP needs help with the semantics of KCalCore::SortableList<>.
        #
        ["KCalCore::Recurrence", "set(R|Ex)Date(|Time)s", ".*", ".*", ".*", rule_helpers.function_discard],
    ]


def typedef_rules():
    return [
        ["KCalCore", "Date(Time|)List", ".*", ".*", typedef_duplicate_discard],
    ]


def modulecode():
    return {
        "KCalCore/KCalCore/KCalCoremod.sip": {
            "code": module_fix_mapped_types,
        },
    }
