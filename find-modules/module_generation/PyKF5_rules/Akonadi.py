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
import rules_engine
from sip_generator import trace_generated_for
import PyQt_templates


def _function_rewrite_using_decl(container, function, sip, matcher):
    sip["parameters"] = ["const QModelIndex &current", "const QModelIndex &previous"]
    sip["prefix"] = "virtual "


def _parameter_restore_default(container, function, parameter, sip, matcher):
    sip["init"] = "Q_NULLPTR"


def _parameter_use_qstring(container, function, parameter, sip, matcher):
    sip["decl"] = "const QString &" + sip["name"]


def _typedef_add_collections(container, typedef, sip, matcher):
    parameter = sip["decl"]
    value = {
        "type": parameter,
        "base_type": parameter,
    }
    value_h = PyQt_templates.GenerateMappedHelper(value, None)
    handler = PyQt_templates.ListExpander()
    for qt_type in ["QList", "QVector"]:
        mapped_type = "{}<{}>".format(qt_type, parameter)
        trace = trace_generated_for(typedef, _typedef_add_collections, {"value": value_h.category})
        code = handler.expand_generic(qt_type, {"value": value_h})
        code = "%MappedType " + mapped_type + "\n{\n" + trace + code + "};\n"
        sip["module_code"][mapped_type] = code


def _variable_array_to_star(container, variable, sip, matcher):
    builtin_rules.variable_rewrite_array_nonfixed(container, variable, sip, matcher)
    builtin_rules.variable_rewrite_static(container, variable, sip, matcher)


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
        ["Akonadi::AkonadiCore", "Monitor|Protocol", ".*", ".*", ".*", rules_engine.container_discard],
    ]


def forward_declaration_rules():
    return [
        ["entityorderproxymodel.h", "KConfigGroup", ".*", rules_engine.mark_forward_declaration_external],
        ["specialcollections.h", "KCoreConfigSkeleton", ".*", rules_engine.mark_forward_declaration_external],
        ["standard(contact|mail|calendar)actionmanager.h", "KActionCollection", ".*", rules_engine.mark_forward_declaration_external],
        ["agentactionmanager.h", "KActionCollection|KLocalizedString", ".*", rules_engine.mark_forward_declaration_external],
        ["collectionview.h", "KXMLGUIClient", ".*", rules_engine.mark_forward_declaration_external],
    ]


def function_rules():
    return [
        #
        # Remove duplicate signatures.
        #
        ["Akonadi::(Item|Collection)", "parentCollection", ".*", "Akonadi::Collection", ".*", rules_engine.function_discard],
        ["Akonadi::CollectionFetchScope", "ancestorFetchScope", ".*", "Akonadi::CollectionFetchScope", ".*", rules_engine.function_discard],
        ["Akonadi::ItemFetchScope", "tagFetchScope", ".*", "Akonadi::TagFetchScope", ".*", rules_engine.function_discard],
        #
        # boost templates.
        #
        ["Akonadi::Item", "setPayloadBaseV2|addPayloadBaseVariant|addToLegacyMappingImpl", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # Rewrite using declaration.
        #
        ["Akonadi::(Collection|Entity(List|Tree)|Item)View", "currentChanged", ".*", ".*", "", _function_rewrite_using_decl],
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
        [".*", "QVariantMap", ".*", ".*", rules_engine.typedef_discard],
        #
        # Without the needed typedefs, we need to generate QList<Id> and QVector<Id> by hand.
        #
        ["Akonadi::Collection", "Id", ".*", ".*", _typedef_add_collections],
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
    "AkonadiCoremod.sip": {
        "code":
            """
            //
            // Solve the problem that the following are not part of the public API:
            //
            //  - Akonadi::Protocol::Command
            //  - Akonadi::ServerManager
            //
            namespace Akonadi {
                namespace Protocol {
                    class Command {
                    public:
                    };
                };
                class ServerManagerPrivate {
                public:
                };
            };
            %ModuleHeaderCode
            namespace Akonadi {
                namespace Protocol {
                    class Command {
                    public:
                    };
                };
                class ServerManagerPrivate {
                public:
                };
            };
            %End
            """
        },
    }
