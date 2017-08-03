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
SIP binding customisation for PyKF5.KIMAP. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def module_fix_mapped_types(filename, sip, entry):
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<QByteArray>", "QSharedPointer<KMime::Message>",
                                   "QVector<long long>", "QMap<QByteArray, QByteArray>")


def modulecode():
    return {
        "KIMAP/KIMAP/KIMAPmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
