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


def typedef_duplicate_discard(container, typedef, sip, rule):
    if container.translation_unit.spelling.endswith("storejob.h"):
        rule_helpers.typedef_discard(container, typedef, sip, rule)
    else:
        return rule_helpers.SILENT_NOOP


def module_fix_mapped_types(filename, sip, rule):
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QByteArray>", "QSharedPointer<KMime::Message>",
                                   "QVector<long long>", "QMap<QByteArray, QByteArray>")
    rule_helpers.module_add_imports(filename, sip, rule, "KIOCore/kio/kiomod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate",
                                    "KIO::Connection", "KService", "KIO::ClipboardUpdater", "KIMAP::Message")


def container_rules():
    return [
        ["KIMAP", "Term", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]



def typedef_rules():
    return [
        ["KIMAP", "MessageFlags", ".*", ".*", typedef_duplicate_discard],
    ]


def modulecode():
    return {
        "KIMAP/KIMAP/KIMAPmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
