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
SIP binding customisation for PyKF5.MessageViewer. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers

#
# For these two types, SIP generate %MappedType filenames which are too long
# for the filesystem:
#
#   "typedef std::multimap<const char *, const MessageViewer::Interface::BodyPartFormatter *, MessageViewer::ltstr, "
#       "std::allocator<std::pair<const char *const, const MessageViewer::Interface::BodyPartFormatter *> > > SubtypeRegistry;"
#   "typedef std::map<const char *, std::multimap<const char *, const MessageViewer::Interface::BodyPartFormatter *, MessageViewer::ltstr, "
#       "std::allocator<std::pair<const char *const, const MessageViewer::Interface::BodyPartFormatter *> > >, MessageViewer::ltstr, "
#           "std::allocator<std::pair<const char *const, std::multimap<const char *, const MessageViewer::Interface::BodyPartFormatter *, MessageViewer::ltstr, "
#               "std::allocator<std::pair<const char *const, const MessageViewer::Interface::BodyPartFormatter *> > > > > > TypeRegistry;
#
# The following typedefs are used to shorten the names. (Notice that the logic
# in container_add_typedefs would create SIP class definitions which clashed
# with the %MappedType names if the whole type were typedef'd).
#
TYPEDEF_0 = "__MessageViewer0_t"
TYPEDEF_1 = "__MessageViewer1_t"
TYPEDEF_2 = "__MessageViewer2_t"
FORMATTER = "MessageViewer::Interface::BodyPartFormatter"
ALLOCATOR_1 = "std::allocator<std::pair<const char *const, const MessageViewer::Interface::BodyPartFormatter *> >" \
    .replace(FORMATTER, TYPEDEF_0)
ALLOCATOR_2 = "std::allocator<std::pair<const char *const, std::multimap<const char *, const MessageViewer::Interface::BodyPartFormatter *, MessageViewer::ltstr, " \
               "std::allocator<std::pair<const char *const, const MessageViewer::Interface::BodyPartFormatter *> > > > >" \
    .replace(FORMATTER, TYPEDEF_0).replace(ALLOCATOR_1, TYPEDEF_1)
MULTIMAP = "std::multimap<const char *, const MessageViewer::Interface::BodyPartFormatter *, MessageViewer::ltstr, " \
               "std::allocator<std::pair<const char *const, const MessageViewer::Interface::BodyPartFormatter *> > >" \
    .replace(FORMATTER, TYPEDEF_0).replace(ALLOCATOR_1, TYPEDEF_1)
MAP = "std::map<const char *, std::multimap<const char *, const MessageViewer::Interface::BodyPartFormatter *, MessageViewer::ltstr, " \
        "std::allocator<std::pair<const char *const, const MessageViewer::Interface::BodyPartFormatter *> > >, MessageViewer::ltstr, " \
           "std::allocator<std::pair<const char *const, std::multimap<const char *, const MessageViewer::Interface::BodyPartFormatter *, MessageViewer::ltstr, " \
               "std::allocator<std::pair<const char *const, const MessageViewer::Interface::BodyPartFormatter *> > > > > >" \
    .replace(FORMATTER, TYPEDEF_0).replace(ALLOCATOR_1, TYPEDEF_1).replace(ALLOCATOR_2, TYPEDEF_2)

def container_add_typedefs_to_shorten_name(container, sip, rule):
    rule_helpers.container_add_typedefs(container, sip, rule, FORMATTER, ALLOCATOR_1, ALLOCATOR_2)


def function_pass_callable_ia(container, fn, sip, rule):
    sip["code"] = """
%MethodCode
    // Make sure the callable doesn't get garbage collected.
    Py_INCREF(a0);
    Py_BEGIN_ALLOW_THREADS
    sipCpp->injectAttachments([a0, &sipIsErr]()->QString{
        PyObject *innerResult;
        QString *innerCxxResult;
        SIP_BLOCK_THREADS
        innerResult = sipCallMethod(NULL, a0, "");
        Py_DECREF(a0);
        if (!innerResult) {
            PyErr_SetString(PyExc_TypeError, "invalid result from injectAttachments");
        } else {
            innerCxxResult = reinterpret_cast<QString *>(sipConvertToType(innerResult, sipType_QString, NULL, SIP_NO_CONVERTORS, 0, &sipIsErr));
            Py_DECREF(innerResult);
        }
        SIP_UNBLOCK_THREADS
        return *innerCxxResult;
    });
    Py_END_ALLOW_THREADS
%End
"""


def function_pass_callable_rih(container, fn, sip, rule):
    sip["code"] = """
%MethodCode
    // Make sure the callable doesn't get garbage collected.
    Py_INCREF(a1);
    Py_BEGIN_ALLOW_THREADS
    sipRes = sipCpp->replaceInnerHtml(*a0, [a1, &sipIsErr]()->QString{
        PyObject *innerResult;
        QString *innerCxxResult;
        SIP_BLOCK_THREADS
        innerResult = sipCallMethod(NULL, a1, "");
        Py_DECREF(a1);
        if (!innerResult) {
            PyErr_SetString(PyExc_TypeError, "invalid result from replaceInnerHtml");
        } else {
            innerCxxResult = reinterpret_cast<QString *>(sipConvertToType(innerResult, sipType_QString, NULL, SIP_NO_CONVERTORS, 0, &sipIsErr));
            Py_DECREF(innerResult);
        }
        SIP_UNBLOCK_THREADS
        return *innerCxxResult;
    });
    Py_END_ALLOW_THREADS
%End
"""


def parameter_array_to_star(container, fn, parameter, sip, rule):
    sip["decl"] = "const char **" + sip["name"]


def parameter_callable(container, fn, parameter, sip, rule):
    sip["decl"] = "const SIP_PYCALLABLE &" + sip["name"]


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QExplicitlySharedDataPointer<KService>",
                                   "QHash<QString, QVariant>", "QList<QAction *>", "QSharedPointer<KCalCore::Event>",
                                   "QSharedPointer<KCalCore::Todo>", "QSharedPointer<KMime::Message>",
                                   "QVector<Akonadi::Item>", "QVector<KMime::Content *>",
                                   "QVector<KMime::Types::Mailbox>")
    rule_helpers.module_add_imports(filename, sip, rule, "QtDBus/QtDBusmod.sip", "KIOCore/kio/kiomod.sip")
    rule_helpers.module_delete_imports(filename, sip, rule, "Akonadi/KMime/KMimemod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "KTimeZone", "KTimeZoneBackend", "KTimeZoneData",
                                    "KTimeZoneSource", "icalcomponent_impl", "_icaltimezone", "KDateTime",
                                    "KDateTime::Spec", "VObject", "MessageViewer::MessageViewerSettingsBase",
                                    "_IO_FILE", "Kleo::DownloadJob", "Kleo::RefreshKeysJob",
                                    "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate", "KFileItemList",
                                    "KIO::Connection", "KIO::ClipboardUpdater", "KRemoteEncoding",
                                    "KParts::ReadOnlyPart", "QLatin1String", "KActionCollection",
                                    "Akonadi::SpecialMailCollectionsPrivate", "KLocalizedString",
                                    "MessageViewer::ViewerPrivate", "Akonadi::MessageStatus")
    dummy = """%MappedType {type}
{
%ConvertFromTypeCode
// TBD
%End
%ConvertToTypeCode
// TBD
%End
};

"""
    sip["modulecode"][MULTIMAP] = dummy.replace("{type}", MULTIMAP)
    sip["modulecode"][MAP] = dummy.replace("{type}", MAP)


def container_rules():
    return [
        ["MessageViewer", "MessageViewerSettings|FileHtmlWriter", ".*", ".*", ".*", rule_helpers.container_make_uncopyable],
        ["bodypartformatterbasefactory.h", "MessageViewer", ".*", ".*", ".*", container_add_typedefs_to_shorten_name],
    ]


def function_rules():
    return [
        ["MessageViewer::MailWebView", "injectAttachments", ".*", ".*", ".*", function_pass_callable_ia],
        ["MessageViewer::MailWebView", "replaceInnerHtml", ".*", ".*", ".*", function_pass_callable_rih],
    ]


def parameter_rules():
    return [
        #
        # [] -> *
        #
        ["MessageViewer::HeaderStrategy", "stringList", "headers", ".*", ".*", parameter_array_to_star],
        ["MessageViewer::MailWebView", "injectAttachments|replaceInnerHtml", "delayedHtml", ".*", ".*", parameter_callable],
        ["MessageViewer::Util", "createAppAction", "parent", ".*", ".*", rule_helpers.noop],
    ]


def modulecode():
    return {
        "MessageViewer/MessageViewermod.sip": {
            "code": module_fix_mapped_types,
        },
    }
