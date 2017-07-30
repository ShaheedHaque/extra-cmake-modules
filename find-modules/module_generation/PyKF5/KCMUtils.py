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
SIP binding customisation for PyKF5.KCMUtils. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QExplicitlySharedDataPointer<KService>",
                                   "QExplicitlySharedDataPointer<KSharedConfig>", "QList<KPluginInfo>")
    rule_helpers.module_add_classes(filename, sip, entry, "KTimeZone", "KTimeZoneBackend", "KTimeZoneData",
                                  "KTimeZoneSource", "icalcomponent_impl", "_icaltimezone", "KCalCore::_MSSystemTime",
                                  "KCalCore::_MSTimeZone", "KDateTime", "KDateTime::Spec", "VObject", "QLatin1String")


def module_fix_mapped_types_ksettings(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<KPluginInfo>")


def modulecode():
    return {
        "KCMUtilsmod.sip": {
            "code": module_fix_mapped_types,
        },
        "ksettingsmod.sip": {
            "code": module_fix_mapped_types_ksettings,
        },
    }


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kcmoduleproxy.h::KCModuleProxy": {
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'QObject'
                    sipType = NULL;

                    if (dynamic_cast<KEmoticons*>(sipCpp))
                        sipType = sipType_KEmoticons;
                    else if (dynamic_cast<KEmoticonsProvider*>(sipCpp))
                        sipType = sipType_KEmoticonsProvider;
                    else if (dynamic_cast<KIdleTime*>(sipCpp))
                        sipType = sipType_KIdleTime;
                    else if (dynamic_cast<KSettings::PluginPage*>(sipCpp))
                        sipType = sipType_KSettings_PluginPage;
                    else if (dynamic_cast<KCModuleProxy*>(sipCpp))
                        sipType = sipType_KCModuleProxy;
                    else if (dynamic_cast<KPluginSelector*>(sipCpp))
                        sipType = sipType_KPluginSelector;
                    else if (dynamic_cast<KCMultiDialog*>(sipCpp))
                        {
                        sipType = sipType_KCMultiDialog;
                        if (dynamic_cast<KSettings::Dialog*>(sipCpp))
                            sipType = sipType_KSettings_Dialog;
                        }
                    else if (dynamic_cast<KPrintPreview*>(sipCpp))
                        sipType = sipType_KPrintPreview;
                %End
                """
        },
        "kcmoduleinfo.h::KCModuleInfo": {
            "code":
                '''
                %TypeHeaderCode
                // SIP does not always generate a derived class. Fake one!
                #define sipKCModuleInfo KCModuleInfo
                %End
                '''
        },
    }
