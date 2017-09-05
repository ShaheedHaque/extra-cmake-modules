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
SIP binding customisation for PyKF5.MailCommon. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def function_make_callable(container, fn, sip, rule):
    sip["parameters"][-1] = "SIP_PYCALLABLE ignoreCollectionCallback = 0"


def parameter_fix_default(container, fn, parameter, sip, rule):
    lhs, rhs = sip["init"].split(")", 1)
    sip["init"] = "QFlags<" + lhs[:-1] + ">" + rhs + ")"


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QExplicitlySharedDataPointer<KSharedConfig>",
                                   "QMap<QByteArray, QByteArray>", "QVector<Akonadi::AgentInstance>",
                                   "QVector<Akonadi::Collection>", "QVector<Akonadi::Item>",
                                   "QVector<KMime::MDN::DispositionModifier>")
    rule_helpers.module_add_classes(filename, sip, rule, "KIO::Job", "MessageCore::MessageCoreSettingsBase",
                                    "KTimeZone", "KTimeZoneBackend", "KTimeZoneData", "KTimeZoneSource",
                                    "icalcomponent_impl", "_icaltimezone", "KDateTime", "KDateTime::Spec",
                                    "VObject", "MessageViewer::MessageViewerSettingsBase", "_IO_FILE",
                                    "Kleo::DownloadJob", "Kleo::RefreshKeysJob", "Akonadi::Protocol::Command",
                                    "Akonadi::ServerManagerPrivate")


def function_rules():
    return [
        ["MailCommon::Util", "nextUnreadCollection", ".*", ".*", ".*", function_make_callable],
    ]


def parameter_rules():
    return [
        ["MailCommon::FolderTreeWidget", "FolderTreeWidget", "options", ".*", ".*", parameter_fix_default],
        ["MailCommon::SearchPatternEdit", "SearchPatternEdit", "options", ".*", ".*", parameter_fix_default],
        ["MailCommon::SearchRuleWidget", "SearchRuleWidget", "options", ".*", ".*", parameter_fix_default],
        ["MailCommon::SearchRuleWidgetLister", "SearchRuleWidgetLister", "opt", ".*", ".*", parameter_fix_default],
    ]


def modulecode():
    return {
        "MailCommon/MailCommonmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
