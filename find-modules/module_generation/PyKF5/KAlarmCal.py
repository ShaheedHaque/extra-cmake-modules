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
SIP binding customisation for PyKF5.KAlarmCal. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rules_engine


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rules_engine.modulecode_delete(filename, sip, entry, "QSharedPointer<KCalCore::Calendar>",
                                   "QSharedPointer<KCalCore::Event>",
                                   "QSharedPointer<KCalCore::ToDo>",
                                   "QSharedPointer<KCalCore::Todo>",
                                   "QVector<QSharedPointer<KCalCore::Person> >",
                                   "QVector<int>")
    sip["code"] = """
%If (!KAlarmCal_KAlarmCal_KAlarmCalmod)
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
class QLatin1String;
class VObject;
class KConfigGroup;
class KCoreConfigSkeleton;
%End
"""


def function_rules():
    return [
        ["KAlarmCal::Repetition", "operator(!| bool)", ".*", ".*", ".*", rules_engine.function_discard],
    ]


def modulecode():
    return {
    "KAlarmCalmod.sip": {
        "code": module_fix_mapped_types,
        },
    }
