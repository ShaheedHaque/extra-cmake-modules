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

import rules_engine


def module_fix_mapped_types(filename, sip, entry):
    sip["code"] = """
%If (!KCalCore_KCalCore_KCalCoremod)
class KTimeZone;
class KTimeZoneBackend;
class KTimeZoneData;
class KTimeZoneSource;
struct icalcomponent_impl;
struct _icaltimezone;
struct KCalCore::_MSSystemTime;
struct KCalCore::_MSTimeZone;
class KDateTime;
class KDateTime::Spec;
//struct VObject; Uncommenting this causes SIP to crash.
class QLatin1String /External/;
%End
"""


def typedef_duplicate_discard(container, typedef, sip, matcher):
    """
    There are multiple definitions like this:

        typedef KCalCore::SortableList<KDateTime> DateTimeList;

    We need to get rid of the second one.
    """
    filename = os.path.basename(container.translation_unit.spelling)
    if filename != "incidencebase.h":
        rules_engine.typedef_discard(container, typedef, sip, matcher)


def container_rules():
    return [
        #
        # Duplicate Akonadi::SuperClass.
        #
        ["(event|journal|todo).h", "Akonadi", ".*", ".*", ".*", rules_engine.container_discard],
    ]


def function_rules():
    return [
        #
        # Delete non-const.
        #
        ["KCalCore::Attendee", "customProperties", ".*", ".*", ".*", ".*", "(?! const)", rules_engine.function_discard],
    ]


def typedef_rules():
    return [
        ["KCalCore", "Date(Time|)List", ".*", ".*", typedef_duplicate_discard],
    ]


def modulecode():
    return {
        "KCalCoremod.sip": {
            "code": module_fix_mapped_types,
        },
    }
