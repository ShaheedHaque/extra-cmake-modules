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

import rules_engine


def _function_rewrite_using_decl(container, function, sip, matcher):
    sip["parameters"] = ["const QString &name"]
    sip["fn_result"] = "QVariant"
    sip["suffix"] = " const"


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rules_engine.modulecode_delete(filename, sip, entry, "QList<QExplicitlySharedDataPointer<KSycocaEntry> >",
                                   "QList<QVariant>")
    #
    # No such things a KServiceOffer?
    #
    rules_engine.modulecode_delete(filename, sip, entry, "QList<KServiceOffer>")
    sip["code"] = """
%ModuleHeaderCode
#include <QExplicitlySharedDataPointer>
#include <KService>
%End
"""


def container_rules():
    return [
        ["ksycocaentry.h", "KSycocaEntry", ".*", ".*", ".*QSharedData.*", rules_engine.container_discard_QSharedData_base],
    ]


def function_rules():
    return [
        #
        # Provide %MethodCode and a C++ signature.
        #
        ["KMimeTypeTrader|KServiceTypeTrader", "preferredService", ".*", ".*", ".*", rules_engine.function_discard],
        ["KPluginInfo", "KPluginInfo", ".*", ".*", ".*SharedData.*", rules_engine.function_discard],
        ["KPluginInfo", "service", ".*", ".*", ".*", rules_engine.function_discard],
        ["KService", "service.*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KServiceGroup", "root|group|childGroup|addEntry", ".*", ".*", ".*", rules_engine.function_discard],
        ["KServiceType", "parentType|serviceType", ".*", ".*", ".*", rules_engine.function_discard],
        ["KSycoca", "stream", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # No KSycocaFactory or KSycocaFactoryList.
        #
        ["KSycoca", "addFactory|factories", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # There is no KServiceOffer.
        #
        ["KMimeTypeTrader", "filterMimeTypeOffers", ".*", ".*", ".*KServiceOffer.*", rules_engine.function_discard],
        ["KServiceTypeTrader", "weightedOffers", ".*", ".*KServiceOffer.*", ".*", rules_engine.function_discard],
        ["KService", "_k_accessServiceTypes", ".*", ".*", ".*", rules_engine.function_discard],
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
        ["k(mime|service)typetrader.h", "KServiceOfferList", ".*", ".*", rules_engine.typedef_discard],
    ]


def typecode():
    return {
        "kplugininfo.h::KPluginInfo": {
            "code":
                """
                %TypeHeaderCode
                // SIP does not always generate a derived class. Fake one!
                #define sipKPluginInfo KPluginInfo
                %End
                """
        },
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
