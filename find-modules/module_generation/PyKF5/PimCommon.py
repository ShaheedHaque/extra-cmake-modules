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
SIP binding customisation for PyKF5.PimCommon. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def container_add_typedefs(container, sip, rule):
    rule_helpers.container_add_typedefs(container, sip, rule, "QMap<QByteArray, QFlags<KIMAP::Acl::Right> >")


def parameter_remove_default(container, fn, parameter, sip, rule):
    sip["init"] = ""


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QHash<QString, QString>", "QList<long long>",
                                   "QMap<QByteArray, QFlags<KIMAP::Acl::Right> >", "QVector<Akonadi::Collection>",
                                   "QVector<Akonadi::Item>")
    rule_helpers.module_add_imports(filename, sip, rule, "KIOCore/kio/kiomod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "KPIMTextEdit::PlainTextEditor",
                                    "PimCommon::PimCommonSettingsBase", "KActionCollection",
                                    "KPIMTextEdit::NestedListHelper", "KIO::Connection", "KService",
                                    "KIO::ClipboardUpdater", "Akonadi::Protocol::Command",
                                    "Akonadi::ServerManagerPrivate", "KIMAP::Message", "KUrlRequester", "QScriptEngine",
                                    "OrgKdeAkonadiImapSettingsInterface", "KXMLGUIClient", "KPIM::ProgressItem",
                                    "KWallet::Wallet", "PimCommon::StorageServiceTreeWidgetItem")


def container_rules():
    return [
        ["PimCommon", "ImapAclAttribute", ".*", ".*", ".*", container_add_typedefs],
        ["PimCommon", "Translator(|Result)TextEdit", ".*", ".*", ".*", rule_helpers.container_make_uncopyable],
        ["PimCommon", "PimCommonSettings", ".*", ".*", ".*", rule_helpers.container_make_uncopyable],
    ]


def parameter_rules():
    return [
        ["PimCommon::StorageServiceSettingsWidget", "setListService", "lstCap", ".*", ".*", parameter_remove_default],
    ]


def modulecode():
    return {
        "PimCommon/PimCommonmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
