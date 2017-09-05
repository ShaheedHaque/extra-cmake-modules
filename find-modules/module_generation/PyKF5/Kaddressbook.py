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
SIP binding customisation for PyKF5.KaddressbookGrantlee. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def module_fix_mapped_types(filename, sip, rule):
    rule_helpers.module_add_imports(filename, sip, rule, "KIOCore/kio/kiomod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "KIO::Connection", "KService", "KIO::ClipboardUpdater",
                                    "KPIMTextEdit::PlainTextEditor", "PimCommon::PimCommonSettingsBase",
                                    "KActionCollection", "KPIMTextEdit::NestedListHelper",
                                    "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate", "KIMAP::Message",
                                    "KUrlRequester", "QScriptEngine", "OrgKdeAkonadiImapSettingsInterface",
                                    "KXMLGUIClient", "KPIM::ProgressItem", "KWallet::Wallet",
                                    "PimCommon::StorageServiceTreeWidgetItem", "Akonadi::AbstractContactEditorWidget",
                                    "KLocalizedString", "GrantleeTheme::Theme")


def modulecode():
    return {
        "KaddressbookGrantlee/KaddressbookGrantleemod.sip": {
            "code": module_fix_mapped_types,
        },
    }