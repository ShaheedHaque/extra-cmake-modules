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
SIP binding customisation for PyKF5.KService. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers


def _function_rewrite_using_decl(container, function, sip, matcher):
    sip["parameters"] = ["const QString &name"]
    sip["fn_result"] = "QVariant"
    sip["suffix"] = " const"


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QExplicitlySharedDataPointer<KSycocaEntry> >",
                                   "QList<QVariant>", "QVector<KPluginMetaData>")
    rule_helpers.module_add_includes(filename, sip, rule, "<QExplicitlySharedDataPointer>", "<KService>")


def container_rules():
    return [
        ["ksycocaentry.h", "KSycocaEntry", ".*", ".*", ".*QSharedData.*", rule_helpers.container_discard_QSharedData_base],
        ["kplugininfo.h", "KPluginInfo", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]


def function_rules():
    return [
        #
        # Provide %MethodCode and a C++ signature.
        #
        ["KMimeTypeTrader|KServiceTypeTrader", "preferredService", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KPluginInfo", "KPluginInfo", ".*", ".*", ".*SharedData.*", rule_helpers.function_discard],
        ["KPluginInfo", "service", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KService", "service.*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KServiceGroup", "root|group|childGroup|addEntry", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KServiceType", "parentType|serviceType", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KSycoca", "stream", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # No KSycocaFactory or KSycocaFactoryList.
        #
        ["KSycoca", "addFactory|factories", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # There is no KServiceOffer.
        #
        ["KMimeTypeTrader", "filterMimeTypeOffers", ".*", ".*", ".*KServiceOffer.*", rule_helpers.function_discard],
        ["KServiceTypeTrader", "weightedOffers", ".*", ".*KServiceOffer.*", ".*", rule_helpers.function_discard],
        ["KService", "_k_accessServiceTypes", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Rewrite using declaration.
        #
        ["KService", "property", ".*", ".*", "", _function_rewrite_using_decl],
    ]


def typedef_rules():
    return [
        #
        # There is no KServiceOffer.
        #
        ["k(mime|service)typetrader.h", "KServiceOfferList", ".*", ".*", rule_helpers.typedef_discard],
    ]


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kservicegroup.h::KServiceGroup": {  # KServiceGroup : KSycocaEntry
            "code":
                """
                %ConvertToSubClassCode

                    if (dynamic_cast<KServiceGroup*>(sipCpp))
                        sipClass = sipClass_KServiceGroup;
                    else if (dynamic_cast<KServiceSeparator*>(sipCpp))
                        sipClass = sipClass_KServiceSeparator;
                    else
                        sipClass = NULL;
                %End
                """
        },
    }


def modulecode():
    return {
        "KServicemod.sip": {
            "code": module_fix_mapped_types,
        },
    }
