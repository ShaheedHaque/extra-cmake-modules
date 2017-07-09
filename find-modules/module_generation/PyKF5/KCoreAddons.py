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
SIP binding customisation for PyKF5.KCoreAddons. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers


def _container_delete_base(container, sip, matcher):
    sip["base_specifiers"] = []



def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<T>")
    rule_helpers.modulecode_make_local(filename, sip, entry, "QList<QUrl>", "QList<QVariant>")


def container_rules():
    return [
        #
        # SIP cannot handle inline templates like "class Foo: Bar<Baz>" without an intermediate typedef. For now,
        # delete the base class.
        #
        ["kuser.h", "KUserId|KGroupId", ".*", ".*", ".*", _container_delete_base],
        ["KPluginFactory", "InheritanceChecker", ".*", ".*", ".*", rule_helpers.container_discard],
    ]


def function_rules():
    return [
        #
        # Strip protected functions which require private stuff to work.
        #
        ["KPluginFactory", "KPluginFactory", ".*", ".*", "KPluginFactoryPrivate.*", rule_helpers.function_discard],
        ["KJob", ".*", ".*", ".*", ".*KJob::QPrivateSignal.*", rule_helpers.function_discard],
        ["KCompositeJob", "KCompositeJob", ".*", ".*", "KCompositeJobPrivate.*", rule_helpers.function_discard],
        ["KUser", "KUser", ".*", ".*", ".*passwd.*", rule_helpers.function_discard],
        ["KUserGroup", "KUserGroup", ".*", ".*", ".*group.*", rule_helpers.function_discard],
        #
        # Use forward declared types.
        #
        ["KPluginFactory", "createPartObject", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KPluginFactory", "create", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KMacroExpanderBase", "expandMacrosShellQuote", ".*", ".*", "QString &str", rule_helpers.function_discard],
        #
        # This class has inline implementations in the header file.
        #
        ["KPluginName", ".*", ".*", ".*", ".*", rule_helpers.function_discard_impl],
        #
        # SIP cannot handle std::function.
        #
        ["KPluginLoader", "instantiatePlugins|findPlugins|forEachPlugin", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # SIP thinks there are duplicate signatures.
        #
        ["KRandomSequence", "setSeed", ".*", ".*", "int.*", rule_helpers.function_discard],
        #
        # kuser.h has inline operators.
        #
        [".*", "operator!=", ".*", ".*", "const KUser(Group){0,1} &other", rule_helpers.function_discard],
        #
        # Need typedef for argument, plus custom logic.
        #
        ["KPluginFactory", "registerPlugin", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # SIP: unsupported signal argument type, unsupported function argument type (QPair)
        #
        ["KJob|KJobTrackerInterface|KStatusBarJobTracker|KUiServerJobTracker|KWidgetJobTracker", "description", ".*", ".*", ".*", rule_helpers.function_discard],
    ]


def parameter_rules():
    return [
        ["KShell", "splitArgs", "err", ".*", ".*", rule_helpers.parameter_out],
    ]


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kautosavefile.h::KAutoSaveFile": {
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'QObject'
                    sipType = NULL;

                    if (dynamic_cast<KAuth::ActionWatcher*>(sipCpp))
                        sipType = sipType_KAuth_ActionWatcher;
                    else if (dynamic_cast<KAutostart*>(sipCpp))
                        sipType = sipType_KAutostart;
                    else if (dynamic_cast<KCoreConfigSkeleton*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton;
                    else if (dynamic_cast<KDEDModule*>(sipCpp))
                        sipType = sipType_KDEDModule;
                    else if (dynamic_cast<KJob*>(sipCpp))
                        {
                        sipType = sipType_KJob;
                        if (dynamic_cast<KCompositeJob*>(sipCpp))
                            sipType = sipType_KCompositeJob;
                        }
                    else if (dynamic_cast<KJobTrackerInterface*>(sipCpp))
                        sipType = sipType_KJobTrackerInterface;
                    else if (dynamic_cast<KJobUiDelegate*>(sipCpp))
                        sipType = sipType_KJobUiDelegate;
                    else if (dynamic_cast<KLibLoader*>(sipCpp))
                        sipType = sipType_KLibLoader;
                    else if (dynamic_cast<KLocalSocketServer*>(sipCpp))
                        sipType = sipType_KLocalSocketServer;
                    else if (dynamic_cast<KPluginFactory*>(sipCpp))
                        sipType = sipType_KPluginFactory;
                    else if (dynamic_cast<KSycoca*>(sipCpp))
                        sipType = sipType_KSycoca;
                    else if (dynamic_cast<KSystemTimeZones*>(sipCpp))
                        sipType = sipType_KSystemTimeZones;
                    else if (dynamic_cast<KToolInvocation*>(sipCpp))
                        sipType = sipType_KToolInvocation;
                    else if (dynamic_cast<KFilterDev*>(sipCpp))
                        sipType = sipType_KFilterDev;
                    else if (dynamic_cast<KPtyDevice*>(sipCpp))
                        sipType = sipType_KPtyDevice;
                    else if (dynamic_cast<KTcpSocket*>(sipCpp))
                        sipType = sipType_KTcpSocket;
                    else if (dynamic_cast<KLocalSocket*>(sipCpp))
                        sipType = sipType_KLocalSocket;
                    else if (dynamic_cast<KAutoSaveFile*>(sipCpp))
                        sipType = sipType_KAutoSaveFile;
                    else if (dynamic_cast<KSaveFile*>(sipCpp))
                        sipType = sipType_KSaveFile;
                    else if (dynamic_cast<KTemporaryFile*>(sipCpp))
                        sipType = sipType_KTemporaryFile;
                    else if (dynamic_cast<KProcess*>(sipCpp))
                        {
                        sipType = sipType_KProcess;
                        if (dynamic_cast<KPtyProcess*>(sipCpp))
                            sipType = sipType_KPtyProcess;
                        }
                    else if (dynamic_cast<KLibrary*>(sipCpp))
                        sipType = sipType_KLibrary;
                    else if (dynamic_cast<KPluginLoader*>(sipCpp))
                        sipType = sipType_KPluginLoader;
                    else if (dynamic_cast<Sonnet::BackgroundChecker*>(sipCpp))
                        sipType = sipType_Sonnet_BackgroundChecker;
                %End
                """
        },
    }


def modulecode():
    return {
        "KCoreAddonsmod.sip": {
            "code": module_fix_mapped_types,
            },
    }
