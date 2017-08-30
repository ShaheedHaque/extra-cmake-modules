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
SIP binding customisation for PyKF5.KGAPI. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def fix_ktimezone_stuff(filename, sip, rule):
    rule_helpers.module_add_classes(filename, sip, rule, "KTimeZone", "KTimeZoneBackend", "KTimeZoneData",
                                    "KTimeZoneSource", "icalcomponent_impl", "_icaltimezone",
                                    "QNetworkAccessManager", "QNetworkRequest",
                                    "QNetworkReply", "KDateTime", "KDateTime::Spec", "QLatin1String", "VObject")
    rule_helpers.module_add_includes(filename, sip, rule, "<QtNetwork/QtNetwork>")


def module_fix_mapped_types(filename, sip, rule):
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QSharedPointer<T> >")
    fix_ktimezone_stuff(filename, sip, rule)
    rule_helpers.module_add_classes(filename, sip, rule, "KConfigGroup")
    rule_helpers.module_add_imports(filename, sip, rule, "KGAPI/KGAPI/Blogger/Bloggermod.sip",
                                    "KGAPI/KGAPI/Calendar/Calendarmod.sip",
                                    "KGAPI/KGAPI/Contacts/Contactsmod.sip",
                                    "KGAPI/KGAPI/Drive/Drivemod.sip",
                                    "KGAPI/KGAPI/Latitude/Latitudemod.sip",
                                    "KGAPI/KGAPI/Tasks/Tasksmod.sip")


def module_fix_mapped_types_blogger(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QSharedPointer<KGAPI2::Object> >", "QList<QUrl>",
                                   "QSharedPointer<KGAPI2::Account>", "QSharedPointer<KGAPI2::Blogger::Comment>",
                                   "QSharedPointer<KGAPI2::Blogger::Page>", "QSharedPointer<KGAPI2::Blogger::Post>",
                                   "QList<QSharedPointer<KGAPI2::Blogger::Blog> >",
                                   "QSharedPointer<KGAPI2::Blogger::Blog>", "QSharedPointer<KGAPI2::Object>")
    rule_helpers.module_delete_imports(filename, sip, rule, "kjs/kjsmod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "KConfig", "_IO_FILE", "Kleo::DownloadJob",
                                    "Kleo::RefreshKeysJob", "QNetworkAccessManager", "QNetworkRequest", "QNetworkReply",
                                    "Akonadi::Protocol::Command", "KConfigGroup", "Akonadi::ServerManagerPrivate",
                                    "KCoreConfigSkeleton")
    rule_helpers.module_add_includes(filename, sip, rule, "<QtNetwork/QtNetwork>")


def module_fix_mapped_types_calendar(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QSharedPointer<KGAPI2::Calendar> >",
                                   "QList<QSharedPointer<KGAPI2::Event> >", "QList<QSharedPointer<KGAPI2::Object> >",
                                   "QSharedPointer<KGAPI2::Account>", "QSharedPointer<KGAPI2::Calendar>",
                                   "QSharedPointer<KGAPI2::Event>", "QList<QSharedPointer<KGAPI2::Reminder> >",
                                   "QSharedPointer<KGAPI2::Reminder>")
    rule_helpers.module_delete_imports(filename, sip, rule, "kjs/kjsmod.sip")
    fix_ktimezone_stuff(filename, sip, rule)


def module_fix_mapped_types_contacts(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QSharedPointer<KGAPI2::Contact> >",
                                   "QSharedPointer<KGAPI2::Account>", "QList<QSharedPointer<KGAPI2::Object> >",
                                   "QList<QSharedPointer<KGAPI2::ContactsGroup> >",
                                   "QSharedPointer<KGAPI2::Contact>", "QSharedPointer<KGAPI2::ContactsGroup>")
    rule_helpers.module_delete_imports(filename, sip, rule, "kjs/kjsmod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "KIO::Job")
    rule_helpers.module_add_imports(filename, sip, rule, "KIOCore/KIOCoremod.sip")


def module_fix_mapped_types_drive(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QSharedPointer<KGAPI2::Drive::ChildReference> >",
                                   "QList<QSharedPointer<KGAPI2::Drive::File> >",
                                   "QList<QSharedPointer<KGAPI2::Drive::ParentReference> >",
                                   "QList<QSharedPointer<KGAPI2::Drive::Permission> >",
                                   "QList<QSharedPointer<KGAPI2::Drive::Revision> >",
                                   "QList<QSharedPointer<KGAPI2::Object> >", "QSharedPointer<KGAPI2::Account>",
                                   "QSharedPointer<KGAPI2::Drive::About>",
                                   "QSharedPointer<KGAPI2::Drive::ChildReference>",
                                   "QSharedPointer<KGAPI2::Drive::File>",
                                   "QSharedPointer<KGAPI2::Drive::ParentReference>",
                                   "QSharedPointer<KGAPI2::Drive::Permission>",
                                   "QSharedPointer<KGAPI2::Drive::Revision>",
                                   "QList<QSharedPointer<KGAPI2::Drive::App> >",
                                   "QList<QSharedPointer<KGAPI2::Drive::Change> >",
                                   "QList<QSharedPointer<KGAPI2::Drive::User> >",
                                   "QSharedPointer<KGAPI2::Drive::App>",
                                   "QSharedPointer<KGAPI2::Drive::Change>",
                                   "QSharedPointer<KGAPI2::Drive::User>")
    rule_helpers.module_delete_imports(filename, sip, rule, "kjs/kjsmod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "KIO::Job")
    rule_helpers.module_add_imports(filename, sip, rule, "KIOCore/KIOCoremod.sip")


def module_fix_mapped_types_latitude(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QSharedPointer<KGAPI2::Object> >",
                                   "QSharedPointer<KGAPI2::Account>", "QSharedPointer<KGAPI2::Location>")
    rule_helpers.module_delete_imports(filename, sip, rule, "kjs/kjsmod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "KIO::Job")
    rule_helpers.module_add_imports(filename, sip, rule, "KIOCore/KIOCoremod.sip")


def module_fix_mapped_types_maps(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QVector<KContacts::Address>")
    rule_helpers.module_add_classes(filename, sip, rule, "KIO::Job")
    rule_helpers.module_add_imports(filename, sip, rule, "KIOCore/KIOCoremod.sip")


def module_fix_mapped_types_tasks(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QSharedPointer<KGAPI2::Object> >",
                                   "QList<QSharedPointer<KGAPI2::Task> >", "QList<QSharedPointer<KGAPI2::TaskList> >",
                                   "QSharedPointer<KGAPI2::Account>", "QSharedPointer<KGAPI2::Task>",
                                   "QSharedPointer<KGAPI2::TaskList>")
    fix_ktimezone_stuff(filename, sip, rule)
    rule_helpers.module_delete_imports(filename, sip, rule, "kjs/kjsmod.sip")


def container_rules():
    return [
        #
        # SIP does not seem to be able to handle these type specialization, but we can live without them?
        #
        ["KGAPI2", "Account|Object|Reminder", "", ".*", ".*", rule_helpers.container_make_unassignable],
    ]


def modulecode():
    return {
        "KGAPI/KGAPI/KGAPImod.sip": {
            "code": module_fix_mapped_types,
        },
        "KGAPI/KGAPI/Blogger/Bloggermod.sip": {
            "code": module_fix_mapped_types_blogger,
        },
        "KGAPI/KGAPI/Calendar/Calendarmod.sip": {
            "code": module_fix_mapped_types_calendar,
        },
        "KGAPI/KGAPI/Contacts/Contactsmod.sip": {
            "code": module_fix_mapped_types_contacts,
        },
        "KGAPI/KGAPI/Drive/Drivemod.sip": {
            "code": module_fix_mapped_types_drive,
        },
        "KGAPI/KGAPI/Latitude/Latitudemod.sip": {
            "code": module_fix_mapped_types_latitude,
        },
        "KGAPI/KGAPI/Maps/Mapsmod.sip": {
            "code": module_fix_mapped_types_maps,
        },
        "KGAPI/KGAPI/Tasks/Tasksmod.sip": {
            "code": module_fix_mapped_types_tasks,
        },
    }
