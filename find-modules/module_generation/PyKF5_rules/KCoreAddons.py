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

import rules_engine


def _container_delete_base(container, sip, matcher):
    sip["base_specifiers"] = []


def container_rules():
    return [
        #
        # SIP cannot handle inline templates like "class Foo: Bar<Baz>" without an intermediate typedef. For now,
        # delete the base class.
        #
        ["kuser.h", "KUserId|KGroupId", ".*", ".*", ".*", _container_delete_base],
        ["KPluginFactory", "InheritanceChecker", ".*", ".*", ".*", rules_engine.container_discard],
    ]


def function_rules():
    return [
        #
        # Strip protected functions which require private stuff to work.
        #
        ["KPluginFactory", "KPluginFactory", ".*", ".*", "KPluginFactoryPrivate.*", rules_engine.function_discard],
        ["KJob", ".*", ".*", ".*", ".*KJob::QPrivateSignal.*", rules_engine.function_discard],
        ["KCompositeJob", "KCompositeJob", ".*", ".*", "KCompositeJobPrivate.*", rules_engine.function_discard],
        ["KUser", "KUser", ".*", ".*", ".*passwd.*", rules_engine.function_discard],
        ["KUserGroup", "KUserGroup", ".*", ".*", ".*group.*", rules_engine.function_discard],
        #
        # Use forward declared types.
        #
        ["KPluginFactory", "createPartObject", ".*", ".*", ".*", rules_engine.function_discard],
        ["KPluginFactory", "create", ".*", ".*", ".*", rules_engine.function_discard],
        ["KMacroExpanderBase", "expandMacrosShellQuote", ".*", ".*", "QString &str", rules_engine.function_discard],
        #
        # This class has inline implementations in the header file.
        #
        ["KPluginName", ".*", ".*", ".*", ".*", rules_engine.function_discard_impl],
        #
        # SIP thinks there are duplicate signatures.
        #
        ["KPluginLoader", "instantiatePlugins|findPlugins|forEachPlugin", ".*", ".*", ".*", rules_engine.function_discard],
        ["KRandomSequence", "setSeed", ".*", ".*", "int.*", rules_engine.function_discard],
        #
        # kuser.h has inline operators.
        #
        [".*", "operator!=", ".*", ".*", "const KUser(Group){0,1} &other", rules_engine.function_discard],
        #
        # Need typedef for argument, plus custom logic.
        #
        ["KPluginFactory", "registerPlugin", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # SIP: unsupported signal argument type, unsupported function argument type (QPair)
        #
        ["KJob|KJobTrackerInterface|KStatusBarJobTracker|KUiServerJobTracker|KWidgetJobTracker", "description", ".*", ".*", ".*", rules_engine.function_discard],
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
