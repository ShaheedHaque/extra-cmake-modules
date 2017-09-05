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
SIP binding customisation for PyKF5.MessageCore. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QSharedPointer<KMime::Message>", "QList<long long>",
                                   "QVector<KMime::Types::Mailbox>", "QVector<KMime::Types::Address>")

    rule_helpers.module_delete_imports(filename, sip, rule, "Akonadi/KMime/KMimemod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "MessageCore::MessageCoreSettingsBase",
                                    "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate",
                                    "Akonadi::SpecialMailCollectionsPrivate", "KLocalizedString", "KConfigGroup",
                                    "KCoreConfigSkeleton", "Akonadi::MessageStatus")
    rule_helpers.modulecode_make_local(filename, sip, rule, "QList<QUrl>")


def container_rules():
    return [
        ["MessageCore", "MessageCoreSettings", ".*", ".*", ".*", rule_helpers.container_make_uncopyable]
    ]


def parameter_rules():
    return [
        ["MessageCore::AttachmentFromUrlUtils", "createAttachmentJob", "parent", ".*", ".*", rule_helpers.noop]
    ]


def typedef_rules():
    return [
       ["KMime::Types", "AddressList", ".*", ".*", rule_helpers.typedef_discard],
    ]


def modulecode():
    return {
        "MessageCore/MessageCoremod.sip": {
            "code": module_fix_mapped_types,
        },
    }
