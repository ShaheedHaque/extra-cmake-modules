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
SIP binding customisation for PyKF5.Akonadi. This modules describes:

    * Supplementary SIP file generator rules.
"""

import builtin_rules
import rule_helpers
from rule_helpers import trace_generated_for
import PyQt_templates


def _function_rewrite_using_decl(container, function, sip, matcher):
    sip["parameters"] = ["const QModelIndex &current", "const QModelIndex &previous"]
    sip["prefix"] = "virtual "


def _function_rewrite_using_decl2(container, function, sip, matcher):
    sip["parameters"] = ["const Akonadi::Collection &collection"]


def _parameter_restore_default(container, function, parameter, sip, matcher):
    sip["init"] = "Q_NULLPTR"


def _parameter_use_qstring(container, function, parameter, sip, matcher):
    sip["decl"] = "const QString &" + sip["name"]


def _typedef_add_collections(container, typedef, sip, rule):
    parameter = sip["decl"]
    value = {
        "type": parameter,
        "base_type": parameter,
    }
    value_h = PyQt_templates.GenerateMappedHelper(value, None)
    handler = PyQt_templates.ListExpander()
    for qt_type in ["QList", "QVector"]:
        mapped_type = "{}<{}>".format(qt_type, parameter)
        trace = trace_generated_for(typedef, rule, {"value": value_h.category})
        code = handler.expand_generic(qt_type, {"value": value_h})
        code = "%MappedType " + mapped_type + "\n{\n" + trace + code + "};\n"
        sip["modulecode"][mapped_type] = code


def _variable_array_to_star(container, variable, sip, matcher):
    builtin_rules.variable_rewrite_array_nonfixed(container, variable, sip, matcher)
    builtin_rules.variable_rewrite_static(container, variable, sip, matcher)


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_make_local(filename, sip, rule, "QMap<QString, QVariant>")
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QModelIndex>", "QSharedPointer<T>", "QSharedPointer<U>",
                                   "QVector<T>", "QVector<int>")
    rule_helpers.module_add_classes(filename, sip, rule, "Akonadi::Protocol::Command /External/",
                                    "Akonadi::ServerManagerPrivate /External/", "KConfigGroup", "KCoreConfigSkeleton")
    rule_helpers.module_add_includes(filename, sip, rule, "<akonadi/private/protocol_p.h>")


def module_fix_mapped_types_agentbase(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QSet<Akonadi::Tag>", "QSet<QByteArray>",
                                   "QVector<Akonadi::Collection>", "QVector<Akonadi::Item>",
                                   "QVector<Akonadi::Relation>", "QVector<Akonadi::Tag>", "QVector<QByteArray>",
                                   "QVector<long long>")
    rule_helpers.module_add_classes(filename, sip, entry, "QDBusContext /External/", "Akonadi::ImapSet",
                                    "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate")
    rule_helpers.module_add_imports(filename, sip, entry, "QtDBus/QtDBusmod.sip")


def module_fix_mapped_types_calendar(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QSet<QByteArray>", "QSharedPointer<KCalCore::Attendee>",
                                   "QSharedPointer<KCalCore::Event>", "QSharedPointer<KCalCore::FreeBusy>",
                                   "QSharedPointer<KCalCore::Incidence>", "QSharedPointer<KCalCore::IncidenceBase>",
                                   "QSharedPointer<KCalCore::Journal>", "QSharedPointer<KCalCore::Person>",
                                   "QSharedPointer<KCalCore::Todo>", "QVector<Akonadi::Collection>",
                                   "QVector<Akonadi::Item>", "QVector<QSharedPointer<KCalCore::Incidence> >",
                                   "QVector<QSharedPointer<KCalCore::Alarm> >", "QVector<long long>")
    rule_helpers.module_add_classes(filename, sip, entry, "KTimeZone", "KTimeZoneBackend", "KTimeZoneData",
                                    "KTimeZoneSource", "icalcomponent_impl", "_icaltimezone",
                                    "KCalCore::_MSSystemTime", "KCalCore::_MSTimeZone", "KDateTime",
                                    "KDateTime::Spec", "VObject", "QLatin1String", "MailTransport::MessageQueueJob",
                                    "KIdentityManagement::Identity", "Akonadi::Protocol::Command",
                                    "Akonadi::ServerManagerPrivate")


def module_fix_mapped_types_contact(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QVector<Akonadi::Collection>", "QVector<Akonadi::Item>",
                                   "QVector<KContacts::ContactGroup>")
    rule_helpers.module_add_classes(filename, sip, rule, "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate",
                                    "Akonadi::AbstractContactEditorWidget", "KLineEdit", "KLocalizedString")
    rule_helpers.module_add_includes(filename, sip, rule, "<akonadi/private/protocol_p.h>")


def module_fix_mapped_types_debug(filename, sip, entry):
    rule_helpers.module_add_classes(filename, sip, entry, "KConfigGroup", "KCoreConfigSkeleton",
                                    "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate")


def module_fix_mapped_types_kmime(filename, sip, rule):
    rule_helpers.modulecode_delete(filename, sip, rule, "QVector<Akonadi::Collection>", "QVector<Akonadi::Item>",
                                   "QSet<QByteArray>")
    rule_helpers.module_add_classes(filename, sip, rule, "Akonadi::SpecialMailCollectionsPrivate",
                                    "KLocalizedString", "Akonadi::Protocol::Command",
                                    "Akonadi::ServerManagerPrivate")
    rule_helpers.module_add_imports(filename, sip, rule, "KMime/KMime/KMimemod.sip")
    rule_helpers.module_add_includes(filename, sip, rule, "<akonadi/private/protocol_p.h>")


def module_fix_mapped_types_notes(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QSharedPointer<KMime::Message>", "QMap<QString, QString>")
    rule_helpers.module_add_classes(filename, sip, entry, "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate",
                                    "KConfigGroup", "KCoreConfigSkeleton")
    rule_helpers.module_add_imports(filename, sip, entry, "KMime/KMime/KMimemod.sip")


def module_fix_mapped_types_pim(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<long long>")
    rule_helpers.module_add_classes(filename, sip, entry, "KConfigGroup", "KCoreConfigSkeleton",
                                    "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate")


def module_fix_mapped_types_socialutils(filename, sip, entry):
    rule_helpers.module_add_classes(filename, sip, entry, "KConfigGroup", "KCoreConfigSkeleton",
                                    "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate")


def module_fix_mapped_types_widgets(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<long long>", "QVector<Akonadi::Collection>",
                                   "QVector<Akonadi::Item>", "QVector<Akonadi::Tag>", "QVector<Akonadi::AgentInstance>")
    rule_helpers.module_add_classes(filename, sip, entry, "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate")


def module_fix_mapped_types_xml(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QVector<Akonadi::Collection>", "QVector<Akonadi::Item>",
                                   "QVector<Akonadi::Tag>")
    rule_helpers.module_add_classes(filename, sip, rule, "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate",
                                    "KConfigGroup", "KCoreConfigSkeleton")
    rule_helpers.module_add_includes(filename, sip, rule, "<akonadi/private/protocol_p.h>")


_akonadi_qobject_ctscc = """
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QObject'
    sipType = NULL;

    if (dynamic_cast<Akonadi::AgentActionManager*>(sipCpp))
        sipType = sipType_Akonadi_AgentActionManager;
    else if (dynamic_cast<Akonadi::AgentBase*>(sipCpp))
        {
        sipType = sipType_Akonadi_AgentBase;
        if (dynamic_cast<Akonadi::PreprocessorBase*>(sipCpp))
            sipType = sipType_Akonadi_PreprocessorBase;
        else if (dynamic_cast<Akonadi::ResourceBase*>(sipCpp))
            sipType = sipType_Akonadi_ResourceBase;
        }
    else if (dynamic_cast<Akonadi::AgentFactoryBase*>(sipCpp))
        sipType = sipType_Akonadi_AgentFactoryBase;
    else if (dynamic_cast<Akonadi::AgentManager*>(sipCpp))
        sipType = sipType_Akonadi_AgentManager;
    else if (dynamic_cast<Akonadi::Control*>(sipCpp))
        sipType = sipType_Akonadi_Control;
    else if (dynamic_cast<Akonadi::EntityTreeViewStateSaver*>(sipCpp))
        sipType = sipType_Akonadi_EntityTreeViewStateSaver;
    else if (dynamic_cast<Akonadi::Monitor*>(sipCpp))
        {
        sipType = sipType_Akonadi_Monitor;
        if (dynamic_cast<Akonadi::ChangeRecorder*>(sipCpp))
            sipType = sipType_Akonadi_ChangeRecorder;
        }
    else if (dynamic_cast<Akonadi::ServerManager*>(sipCpp))
        sipType = sipType_Akonadi_ServerManager;
    else if (dynamic_cast<Akonadi::Session*>(sipCpp))
        sipType = sipType_Akonadi_Session;
    else if (dynamic_cast<Akonadi::SpecialCollections*>(sipCpp))
        {
        sipType = sipType_Akonadi_SpecialCollections;
        if (dynamic_cast<Akonadi::SpecialMailCollections*>(sipCpp))
            sipType = sipType_Akonadi_SpecialMailCollections;
        }
    else if (dynamic_cast<Akonadi::StandardActionManager*>(sipCpp))
        sipType = sipType_Akonadi_StandardActionManager;
    else if (dynamic_cast<Akonadi::StandardMailActionManager*>(sipCpp))
        sipType = sipType_Akonadi_StandardMailActionManager;
    else if (dynamic_cast<Akonadi::ResourceBaseSettings*>(sipCpp))
        {
        sipType = sipType_Akonadi_ResourceBaseSettings;
        if (dynamic_cast<Akonadi::ResourceSettings*>(sipCpp))
            sipType = sipType_Akonadi_ResourceSettings;
        }
    else if (dynamic_cast<Akonadi::AgentInstanceCreateJob*>(sipCpp))
        sipType = sipType_Akonadi_AgentInstanceCreateJob;
    else if (dynamic_cast<Akonadi::CollectionAttributesSynchronizationJob*>(sipCpp))
        sipType = sipType_Akonadi_CollectionAttributesSynchronizationJob;
    else if (dynamic_cast<Akonadi::PartFetcher*>(sipCpp))
        sipType = sipType_Akonadi_PartFetcher;
    else if (dynamic_cast<Akonadi::RecursiveItemFetchJob*>(sipCpp))
        sipType = sipType_Akonadi_RecursiveItemFetchJob;
    else if (dynamic_cast<Akonadi::ResourceSynchronizationJob*>(sipCpp))
        sipType = sipType_Akonadi_ResourceSynchronizationJob;
    else if (dynamic_cast<Akonadi::Job*>(sipCpp))
        {
        sipType = sipType_Akonadi_Job;
        if (dynamic_cast<Akonadi::CollectionCopyJob*>(sipCpp))
            sipType = sipType_Akonadi_CollectionCopyJob;
        else if (dynamic_cast<Akonadi::CollectionCreateJob*>(sipCpp))
            sipType = sipType_Akonadi_CollectionCreateJob;
        else if (dynamic_cast<Akonadi::CollectionDeleteJob*>(sipCpp))
            sipType = sipType_Akonadi_CollectionDeleteJob;
        else if (dynamic_cast<Akonadi::CollectionFetchJob*>(sipCpp))
            sipType = sipType_Akonadi_CollectionFetchJob;
        else if (dynamic_cast<Akonadi::CollectionModifyJob*>(sipCpp))
            sipType = sipType_Akonadi_CollectionModifyJob;
        else if (dynamic_cast<Akonadi::CollectionMoveJob*>(sipCpp))
            sipType = sipType_Akonadi_CollectionMoveJob;
        else if (dynamic_cast<Akonadi::CollectionStatisticsJob*>(sipCpp))
            sipType = sipType_Akonadi_CollectionStatisticsJob;
        else if (dynamic_cast<Akonadi::ItemCopyJob*>(sipCpp))
            sipType = sipType_Akonadi_ItemCopyJob;
        else if (dynamic_cast<Akonadi::ItemCreateJob*>(sipCpp))
            sipType = sipType_Akonadi_ItemCreateJob;
        else if (dynamic_cast<Akonadi::ItemDeleteJob*>(sipCpp))
            sipType = sipType_Akonadi_ItemDeleteJob;
        else if (dynamic_cast<Akonadi::ItemFetchJob*>(sipCpp))
            sipType = sipType_Akonadi_ItemFetchJob;
        else if (dynamic_cast<Akonadi::ItemModifyJob*>(sipCpp))
            sipType = sipType_Akonadi_ItemModifyJob;
        else if (dynamic_cast<Akonadi::ItemMoveJob*>(sipCpp))
            sipType = sipType_Akonadi_ItemMoveJob;
        else if (dynamic_cast<Akonadi::ItemSearchJob*>(sipCpp))
            sipType = sipType_Akonadi_ItemSearchJob;
        else if (dynamic_cast<Akonadi::ItemSync*>(sipCpp))
            sipType = sipType_Akonadi_ItemSync;
        else if (dynamic_cast<Akonadi::LinkJob*>(sipCpp))
            sipType = sipType_Akonadi_LinkJob;
        else if (dynamic_cast<Akonadi::SearchCreateJob*>(sipCpp))
            sipType = sipType_Akonadi_SearchCreateJob;
        else if (dynamic_cast<Akonadi::TransactionBeginJob*>(sipCpp))
            sipType = sipType_Akonadi_TransactionBeginJob;
        else if (dynamic_cast<Akonadi::TransactionCommitJob*>(sipCpp))
            sipType = sipType_Akonadi_TransactionCommitJob;
        else if (dynamic_cast<Akonadi::TransactionRollbackJob*>(sipCpp))
            sipType = sipType_Akonadi_TransactionRollbackJob;
        else if (dynamic_cast<Akonadi::TransactionSequence*>(sipCpp))
            {
            sipType = sipType_Akonadi_TransactionSequence;
            if (dynamic_cast<Akonadi::SpecialCollectionsRequestJob*>(sipCpp))
                {
                sipType = sipType_Akonadi_SpecialCollectionsRequestJob;
                if (dynamic_cast<Akonadi::SpecialMailCollectionsRequestJob*>(sipCpp))
                    sipType = sipType_Akonadi_SpecialMailCollectionsRequestJob;
                }
            }
        else if (dynamic_cast<Akonadi::TrashJob*>(sipCpp))
            sipType = sipType_Akonadi_TrashJob;
        else if (dynamic_cast<Akonadi::TrashRestoreJob*>(sipCpp))
            sipType = sipType_Akonadi_TrashRestoreJob;
        else if (dynamic_cast<Akonadi::UnlinkJob*>(sipCpp))
            sipType = sipType_Akonadi_UnlinkJob;
        }
    else if (dynamic_cast<Akonadi::ETMViewStateSaver*>(sipCpp))
        sipType = sipType_Akonadi_ETMViewStateSaver;
    else if (dynamic_cast<Akonadi::CollectionStatisticsDelegate*>(sipCpp))
        sipType = sipType_Akonadi_CollectionStatisticsDelegate;
    else if (dynamic_cast<Akonadi::AgentInstanceModel*>(sipCpp))
        sipType = sipType_Akonadi_AgentInstanceModel;
    else if (dynamic_cast<Akonadi::AgentTypeModel*>(sipCpp))
        sipType = sipType_Akonadi_AgentTypeModel;
    else if (dynamic_cast<Akonadi::CollectionModel*>(sipCpp))
        {
        sipType = sipType_Akonadi_CollectionModel;
        if (dynamic_cast<Akonadi::CollectionStatisticsModel*>(sipCpp))
            sipType = sipType_Akonadi_CollectionStatisticsModel;
        }
    else if (dynamic_cast<Akonadi::EntityTreeModel*>(sipCpp))
        sipType = sipType_Akonadi_EntityTreeModel;
    else if (dynamic_cast<Akonadi::MessageThreaderProxyModel*>(sipCpp))
        sipType = sipType_Akonadi_MessageThreaderProxyModel;
    else if (dynamic_cast<Akonadi::SelectionProxyModel*>(sipCpp))
        {
        sipType = sipType_Akonadi_SelectionProxyModel;
        if (dynamic_cast<Akonadi::FavoriteCollectionsModel*>(sipCpp))
            sipType = sipType_Akonadi_FavoriteCollectionsModel;
        }
    else if (dynamic_cast<Akonadi::AgentFilterProxyModel*>(sipCpp))
        sipType = sipType_Akonadi_AgentFilterProxyModel;
    else if (dynamic_cast<Akonadi::CollectionFilterProxyModel*>(sipCpp))
        sipType = sipType_Akonadi_CollectionFilterProxyModel;
    else if (dynamic_cast<Akonadi::EntityMimeTypeFilterModel*>(sipCpp))
        sipType = sipType_Akonadi_EntityMimeTypeFilterModel;
    else if (dynamic_cast<Akonadi::EntityOrderProxyModel*>(sipCpp))
        sipType = sipType_Akonadi_EntityOrderProxyModel;
    else if (dynamic_cast<Akonadi::StatisticsProxyModel*>(sipCpp))
        sipType = sipType_Akonadi_StatisticsProxyModel;
    else if (dynamic_cast<Akonadi::EntityRightsFilterModel*>(sipCpp))
        sipType = sipType_Akonadi_EntityRightsFilterModel;
    else if (dynamic_cast<Akonadi::RecursiveCollectionFilterProxyModel*>(sipCpp))
        sipType = sipType_Akonadi_RecursiveCollectionFilterProxyModel;
    else if (dynamic_cast<Akonadi::TrashFilterProxyModel*>(sipCpp))
        sipType = sipType_Akonadi_TrashFilterProxyModel;
    else if (dynamic_cast<Akonadi::ItemModel*>(sipCpp))
        {
        sipType = sipType_Akonadi_ItemModel;
        if (dynamic_cast<Akonadi::MessageModel*>(sipCpp))
            sipType = sipType_Akonadi_MessageModel;
        }
    else if (dynamic_cast<Akonadi::AgentInstanceWidget*>(sipCpp))
        sipType = sipType_Akonadi_AgentInstanceWidget;
    else if (dynamic_cast<Akonadi::AgentTypeWidget*>(sipCpp))
        sipType = sipType_Akonadi_AgentTypeWidget;
    else if (dynamic_cast<Akonadi::CollectionPropertiesPage*>(sipCpp))
        sipType = sipType_Akonadi_CollectionPropertiesPage;
    else if (dynamic_cast<Akonadi::CollectionComboBox*>(sipCpp))
        sipType = sipType_Akonadi_CollectionComboBox;
    else if (dynamic_cast<Akonadi::AgentTypeDialog*>(sipCpp))
        sipType = sipType_Akonadi_AgentTypeDialog;
    else if (dynamic_cast<Akonadi::CollectionDialog*>(sipCpp))
        sipType = sipType_Akonadi_CollectionDialog;
    else if (dynamic_cast<Akonadi::CollectionPropertiesDialog*>(sipCpp))
        sipType = sipType_Akonadi_CollectionPropertiesDialog;
    else if (dynamic_cast<Akonadi::CollectionRequester*>(sipCpp))
        sipType = sipType_Akonadi_CollectionRequester;
    else if (dynamic_cast<Akonadi::EntityListView*>(sipCpp))
        sipType = sipType_Akonadi_EntityListView;
    else if (dynamic_cast<Akonadi::CollectionView*>(sipCpp))
        sipType = sipType_Akonadi_CollectionView;
    else if (dynamic_cast<Akonadi::EntityTreeView*>(sipCpp))
        sipType = sipType_Akonadi_EntityTreeView;
    else if (dynamic_cast<Akonadi::ItemView*>(sipCpp))
        sipType = sipType_Akonadi_ItemView;
%End
"""


def container_rules():
    return [
        #
        # SIP does not seem to be able to handle empty containers.
        #
        ["Akonadi::AkonadiCore", "Monitor|Protocol", ".*", ".*", ".*", rule_helpers.container_discard],
        #
        # We cannot handle templated containers which are this complicated.
        #
        ["Akonadi::Internal.*", ".*", ".+", ".*", ".*", rule_helpers.container_discard],
        ["Akonadi::NoteUtils", "NoteMessageWrapper", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]


def forward_declaration_rules():
    return [
        ["standard(contact|mail|calendar)actionmanager.h", "KActionCollection", ".*", rule_helpers.forward_declaration_mark_external],
        ["agentactionmanager.h", "KActionCollection|KLocalizedString", ".*", rule_helpers.forward_declaration_mark_external],
        ["collectionview.h", "KXMLGUIClient", ".*", rule_helpers.forward_declaration_mark_external],
    ]


def function_rules():
    return [
        #
        # Remove duplicate signatures.
        #
        ["Akonadi::(Item|Collection)", "parentCollection", ".*", "Akonadi::Collection", ".*", rule_helpers.function_discard],
        ["Akonadi::CollectionFetchScope", "ancestorFetchScope", ".*", "Akonadi::CollectionFetchScope", ".*", rule_helpers.function_discard],
        ["Akonadi::ItemFetchScope", "tagFetchScope", ".*", "Akonadi::TagFetchScope", ".*", rule_helpers.function_discard],
        #
        # boost templates.
        #
        ["Akonadi::Item", "setPayloadBaseV2|addPayloadBaseVariant|addToLegacyMappingImpl", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Rewrite using declaration.
        #
        ["Akonadi::(Collection|Entity(List|Tree)|Item)View", "currentChanged", ".*", ".*", "", _function_rewrite_using_decl],
        ["Akonadi::AgentBase::ObserverV2", "collectionChanged", ".*", ".*", "", _function_rewrite_using_decl2],
    ]


def parameter_rules():
    return [
        #
        # Clang seems not to be able to return the tokens for this parameter.
        #
        ["Akonadi::ImageProvider", "loadImage", "cache", ".*", ".*", _parameter_restore_default],
        #
        # Akonadi::AbstractDifferencesReporter does not #include <QString>, so Clang fills in with ints: fix this up.
        #
        ["Akonadi::AbstractDifferencesReporter", ".*", "title|name|leftValue|rightValue", ".*", ".*", _parameter_use_qstring],
    ]


def typedef_rules():
    return [
        #
        # SIP thinks there are duplicate signatures.
        #
        [".*", "QVariantMap", ".*", ".*", rule_helpers.typedef_discard],
        #
        # Without the needed typedefs, we need to generate QList<Id> and QVector<Id> by hand.
        #
        ["Akonadi::Collection", "Id", ".*", ".*", _typedef_add_collections],
        #
        # We cannot handle templated typedefs which are this complicated.
        #
        ["Akonadi::Internal.*", ".*", ".*", ".*<.*>.*", rule_helpers.typedef_discard],
    ]


def variable_rules():
    return [
        #
        # [] -> *
        #
        ["Akonadi::ContactPart", ".*", ".*", _variable_array_to_star],
        ["Akonadi::Item", "FullPayload", ".*", _variable_array_to_star],
        ["Akonadi::MessageFlags", ".*", ".*", _variable_array_to_star],
        ["Akonadi::MessagePart", ".*", ".*", _variable_array_to_star],
        ["Akonadi::Tag", "PLAIN|GENERIC", ".*", _variable_array_to_star],
    ]


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED Akonadi::AgentFilterProxyModel": { #AgentFilterProxyModel : QSortFilterProxyModel
            "code": _akonadi_qobject_ctscc
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED Akonadi::ItemSerializerPlugin": { #ItemSerializerPlugin /Abstract/
            "code":
            """
            %ConvertToSubClassCode
                // CTSCC for subclasses of 'ItemSerializerPlugin'
                sipType = NULL;

                if (dynamic_cast<Akonadi::ItemSerializerPluginV2*>(sipCpp))
                    sipType = sipType_Akonadi_ItemSerializerPluginV2;
            %End
            """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED Akonadi::ResourceSettings": { #ResourceSettings : Akonadi::ResourceBaseSettings
            "code": _akonadi_qobject_ctscc
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED Akonadi::AgentBase": { #AgentBase : QObject
            "code":
            """
            %ConvertToSubClassCode
                // CTSCC for subclasses of 'Observer'
                sipType = NULL;

                if (dynamic_cast<Akonadi::AgentBase::ObserverV2*>(sipCpp))
                    sipType = sipType_Akonadi_AgentBase_ObserverV2;
            %End
            """
            },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED Akonadi::SelectionProxyModel": { #SelectionProxyModel : KSelectionProxyModel
            "code": _akonadi_qobject_ctscc
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED Akonadi::AddressAttribute": { #AddressAttribute : Akonadi::Attribute
            "code":
            """
            %ConvertToSubClassCode
                // CTSCC for subclasses of 'Attribute'
                sipType = NULL;

                if (dynamic_cast<Akonadi::AddressAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_AddressAttribute;
                else if (dynamic_cast<Akonadi::CollectionQuotaAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_CollectionQuotaAttribute;
                else if (dynamic_cast<Akonadi::EntityDeletedAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_EntityDeletedAttribute;
                else if (dynamic_cast<Akonadi::EntityDisplayAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_EntityDisplayAttribute;
                else if (dynamic_cast<Akonadi::EntityHiddenAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_EntityHiddenAttribute;
                else if (dynamic_cast<Akonadi::IndexPolicyAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_IndexPolicyAttribute;
                else if (dynamic_cast<Akonadi::MessageFolderAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_MessageFolderAttribute;
                else if (dynamic_cast<Akonadi::MessageThreadingAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_MessageThreadingAttribute;
                else if (dynamic_cast<Akonadi::PersistentSearchAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_PersistentSearchAttribute;
            %End
            """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED Akonadi::Attribute": { #Attribute /Abstract/
            "code":
            """
            %ConvertToSubClassCode
                // CTSCC for subclasses of 'Attribute'
                sipType = NULL;

                if (dynamic_cast<Akonadi::AddressAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_AddressAttribute;
                else if (dynamic_cast<Akonadi::CollectionQuotaAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_CollectionQuotaAttribute;
                else if (dynamic_cast<Akonadi::EntityDisplayAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_EntityDisplayAttribute;
                else if (dynamic_cast<Akonadi::EntityHiddenAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_EntityHiddenAttribute;
                else if (dynamic_cast<Akonadi::MessageFolderAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_MessageFolderAttribute;
                else if (dynamic_cast<Akonadi::MessageThreadingAttribute*>(sipCpp))
                    sipType = sipType_Akonadi_MessageThreadingAttribute;
            %End
            """
        },
    }


def modulecode():
    return {
        "AkonadiCore/AkonadiCoremod.sip": {
            "code": module_fix_mapped_types,
        },
        "AkonadiAgentBase/AkonadiAgentBasemod.sip": {
            "code": module_fix_mapped_types_agentbase,
        },
        "Akonadi/Calendar/Calendarmod.sip": {
            "code": module_fix_mapped_types_calendar,
        },
        "Akonadi/Contact/Contactmod.sip": {
            "code": module_fix_mapped_types_contact,
        },
        "AkonadiSearch/Debug/Debugmod.sip": {
            "code": module_fix_mapped_types_debug,
        },
        "Akonadi/KMime/KMimemod.sip": {
            "code": module_fix_mapped_types_kmime,
        },
        "Akonadi/Notes/Notesmod.sip": {
            "code": module_fix_mapped_types_notes,
        },
        "AkonadiSearch/PIM/PIMmod.sip": {
            "code": module_fix_mapped_types_pim,
        },
        "Akonadi/SocialUtils/SocialUtilsmod.sip": {
            "code": module_fix_mapped_types_socialutils,
        },
        "AkonadiWidgets/AkonadiWidgetsmod.sip": {
            "code": module_fix_mapped_types_widgets,
        },
        "AkonadiXml/AkonadiXmlmod.sip": {
            "code": module_fix_mapped_types_xml,
        },
    }
