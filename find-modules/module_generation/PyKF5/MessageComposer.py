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
SIP binding customisation for PyKF5.MessageComposer. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def container_not_abstract(container, sip, rule):
    sip["annotations"].remove("Abstract")


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QExplicitlySharedDataPointer<KService>", "QList<QByteArray>",
                                   "QList<QModelIndex>", "QList<QSharedPointer<KPIMTextEdit::EmbeddedImage> >",
                                   "QList<QSharedPointer<MessageCore::AttachmentPart> >", "QList<QUrl>",
                                   "QMap<QByteArray, QString>", "QSharedPointer<KMime::Message>",
                                   "QSharedPointer<KPIM::MultiplyingLineData>",
                                   "QSharedPointer<MessageCore::AttachmentPart>", "QVector<Akonadi::Item>",
                                   "QVector<KMime::Headers::Base *>", "QVector<KMime::MDN::DispositionModifier>",
                                   "QVector<KMime::Types::AddrSpec>", "QVector<KMime::Types::Mailbox>",
                                   "std::vector<GpgME::Key, std::allocator<GpgME::Key> >")
    rule_helpers.module_add_imports(filename, sip, rule, "KIOCore/kio/kiomod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "KPIMTextEdit::PlainTextEditor",
                                    "MessageCore::MessageCoreSettingsBase", "KTimeZone", "KTimeZoneBackend",
                                    "KTimeZoneData", "KTimeZoneSource", "icalcomponent_impl", "_icaltimezone",
                                    "KDateTime", "KDateTime::Spec", "MessageViewer::MessageViewerSettingsBase",
                                    "MessageComposer::ContentJobBase", "MessageComposer::AbstractEncryptJob",
                                    "MessageComposer::MessageComposerSettingsBase", "_IO_FILE", "Kleo::DownloadJob",
                                    "Kleo::RefreshKeysJob", "Akonadi::Protocol::Command",
                                    "Akonadi::ServerManagerPrivate", "KIO::Connection", "KIO::ClipboardUpdater",
                                    "KParts::ReadOnlyPart", "QLatin1String", "VObject", "KActionCollection",
                                    "Akonadi::SpecialMailCollectionsPrivate", "MessageViewer::ViewerPrivate",
                                    "KLocalizedString", "KPIMTextEdit::NestedListHelper",
                                    "MailTransport::TransportComboBox", "SendLater::SendLaterInfo",
                                    "MessageComposer::RecipientsPicker", "PimCommon::AutoCorrection",
                                    "MailTransport::MessageQueueJob")


def container_rules():
    return [
        #
        # There is a stray inlined destructor which confuses things...
        #
        ["messagesender.h", "MessageComposer", ".*", ".*", ".*", container_not_abstract],
        ["MessageComposer", "MessageComposerSettings", ".*", ".*", ".*", rule_helpers.container_make_uncopyable],
    ]


def variable_rules():
    return [
        #
        # SIP does not support global arrays:
        #
        # https://www.riverbankcomputing.com/pipermail/pyqt/2017-September/039553.html
        #
     #   ["kleo_util.h", "c(oncreteC|)ryptoMessageFormats", ".*", rule_helpers.variable_discard],
    ]


def modulecode():
    return {
        "MessageComposer/MessageComposermod.sip": {
            "code": module_fix_mapped_types,
        },
    }
