#=============================================================================
# Copyright 2016 by Shaheed Haque (srhaque@theiet.org)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#=============================================================================
"""
SIP binding customisation for PyKF5. This modules describes:

    * The SIP file generator rules.

    * The SIP compilation rules.

"""

from __future__ import print_function

from clang.cindex import AccessSpecifier

import rules_engine
from PyKF5_rules import common_methodcode
from PyKF5_rules import common_modulecode
from PyKF5_rules import common_typecode
from PyKF5_rules import Akonadi
from PyKF5_rules import KAuth
from PyKF5_rules import KBookmarks
from PyKF5_rules import KCoreAddons
from PyKF5_rules import KCodecs
from PyKF5_rules import KCompletion
from PyKF5_rules import KConfig
from PyKF5_rules import KConfigGui
from PyKF5_rules import KConfigWidgets
from PyKF5_rules import KF5KDEGames
from PyKF5_rules import KGuiAddons
from PyKF5_rules import KIOCore
from PyKF5_rules import KI18n
from PyKF5_rules import KJobWidgets
from PyKF5_rules import KLDAP
from PyKF5_rules import KService
from PyKF5_rules import KWidgetsAddons
from PyKF5_rules import KXmlGui
from PyKF5_rules import Syndication
from PyKF5_rules.PyQt_template_typecode import dict_cfttc, list_cfttc, set_cfttc


def _function_discard_class(container, function, sip, matcher):
    sip["fn_result"] = sip["fn_result"].replace("class ", "")


def _function_discard_impl(container, function, sip, matcher):
    if function.extent.start.column == 1:
        rules_engine.function_discard(container, function, sip, matcher)


def _function_discard_non_const(container, function, sip, matcher):
    if not sip["suffix"]:
        rules_engine.function_discard(container, function, sip, matcher)


def _function_discard_protected(container, function, sip, matcher):
    if function.access_specifier == AccessSpecifier.PROTECTED:
        rules_engine.function_discard(container, function, sip, matcher)


def _parameter_in(container, function, parameter, sip, matcher):
    sip["annotations"].add("In")


def _parameter_out(container, function, parameter, sip, matcher):
    sip["annotations"].add("Out")


def _parameter_rewrite_without_colons(container, function, parameter, sip, matcher):
    sip["decl"] = sip["decl"].replace("::", "")


def _parameter_transfer_to_parent(container, function, parameter, sip, matcher):
    if function.is_static_method():
        sip["annotations"].add("Transfer")
    else:
        sip["annotations"].add("TransferThis")


def _parameter_set_max_int(container, function, parameter, sip, matcher):
    sip["init"] = "(uint)-1"


def _parameter_strip_class_enum(container, function, parameter, sip, matcher):
    sip["decl"] = sip["decl"].replace("class ", "").replace("enum ", "")


def _typedef_discard(container, typedef, sip, matcher):
    sip["name"] = ""


def _typedef_rewrite_as_int(container, typedef, sip, matcher):
    sip["decl"] = "int"


def _typedef_rewrite_without_colons(container, typedef, sip, matcher):
    sip["decl"] = sip["decl"].strip(":")


def _variable_discard(container, variable, sip, matcher):
    sip["name"] = ""


def _variable_discard_protected(container, variable, sip, matcher):
    if variable.access_specifier in [AccessSpecifier.PROTECTED, AccessSpecifier.PRIVATE]:
        _variable_discard(container, variable, sip, matcher)


def container_rules():

    return [
        #
        # SIP does not seem to be able to handle these.
        #
        [".*", "(QMetaTypeId|QTypeInfo)<.*>", ".*", ".*", ".*", rules_engine.container_discard],
        #
        # SIP does not seem to be able to handle empty containers.
        #
        ["KParts::ScriptableExtension", "Null|Undefined", ".*", ".*", ".*", rules_engine.container_discard],
        #
        # SIP does not seem to be able to handle templated containers.
        #
        [".*", ".*<.*", ".*", ".*", ".*", rules_engine.container_discard],
        ["KPluginFactory", "InheritanceChecker<impl>", ".*", ".*", ".*", rules_engine.container_discard],
        #
        # This is pretty much a disaster area. TODO: can we rescue some parts?
        #
        [".*", "KConfigCompilerSignallingItem", ".*", ".*", ".*", rules_engine.container_discard],
        ["ConversionCheck", ".*", ".*", ".*", ".*", rules_engine.container_discard],
    ]


def function_rules():

    return [
        #
        # Discard functions emitted by QOBJECT.
        #
        [".*", "metaObject|qt_metacast|tr|trUtf8|qt_metacall|qt_check_for_QOBJECT_macro", ".*", ".*", ".*", rules_engine.function_discard],
        [".*", "d_func", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # SIP does not support operator=.
        #
        [".*", "operator=", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # TODO: Temporarily remove any functions which require templates. SIP seems to support, e.g. QPairs,
        # but we have not made them work yet.
        #
        [".*", ".*", ".+", ".*", ".*", rules_engine.function_discard],
        [".*", ".*<.*>.*", ".*", ".*", ".*", rules_engine.function_discard],
        [".*", ".*", ".*", ".*", ".*QPair.*", rules_engine.function_discard],
        [".*", ".*", ".*", ".*QPair.*", ".*", rules_engine.function_discard],
        #
        # This class has inline implementations in the header file.
        #
        ["KIconEngine|KIconLoader::Group", ".*", ".*", ".*", ".*", _function_discard_impl],
        ["kiconloader.h", "operator\+\+", ".*", ".*", ".*", _function_discard_impl],
        #
        # kshell.h, kconfigbase.sip have inline operators.
        #
        [".*", "operator\|", ".*", ".*", "", rules_engine.function_discard],
        #
        # Inline operators.
        #
        ["KFileItem", "operator QVariant", ".*", ".*", ".*", rules_engine.function_discard],
        ["KService", "operator KPluginName", ".*", ".*", ".*", rules_engine.function_discard],
        ["KMultiTabBar", "button|tab", ".*", ".*", ".*", _function_discard_class],
        ["KCalCore::Duration", "operator bool|operator!", ".*", ".*", "", rules_engine.function_discard],
        ["KPageDialog", "pageWidget|buttonBox", ".*", ".*", "", _function_discard_non_const],
        [".*", ".*", ".*", ".*", ".*Private.*", _function_discard_protected],
        #
        # This function does not exist.
        #
        [".*", "qt_check_for_QGADGET_macro", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # SIP thinks there are duplicate signatures.
        #
        [".*", "qobject_cast", ".*", ".*", ".*", rules_engine.function_discard],
        [".*", "qobject_interface_iid", ".*", ".*", ".*", rules_engine.function_discard],
    ]


def parameter_rules():

    return [
        #
        # Annotate with Transfer or TransferThis when we see a parent object.
        #
        [".*", ".*", ".*", r"[KQ][A-Za-z_0-9]+\W*\*\W*parent", ".*", _parameter_transfer_to_parent],
        ["KCoreConfigSkeleton", "addItem.*", "reference", ".*", ".*", _parameter_in],
        ["KDateTime", "fromString", "negZero", ".*", ".*", _parameter_out],
        ["KPty", "tcGetAttr|tcSetAttr", "ttmode", ".*", ".*", _parameter_rewrite_without_colons],
        #
        # TODO: Temporarily trim any parameters which start "enum".
        #
        ["KAboutData", ".*", "licenseType", ".*", ".*", _parameter_strip_class_enum],
        ["KMultiTabBarButton", ".*Event", ".*", ".*", ".*", _parameter_strip_class_enum],
        ["KRockerGesture", "KRockerGesture", ".*", ".*", ".*", _parameter_strip_class_enum],
    ]


def typedef_rules():

    return [
        #
        # Supplement Qt templates with manual code.
        #
        [".*", ".*", ".*", "QHash<.*>", dict_cfttc],
        [".*", ".*", ".*", "QList<.*>", list_cfttc],
        [".*", ".*", ".*", "QMap<.*>", dict_cfttc],
        [".*", ".*", ".*", "QSet<.*>", set_cfttc],
        [".*", ".*", ".*", "QVector<.*>", list_cfttc],
        #
        # Rewrite uid_t, gid_t as int.
        #
        [".*", ".*", ".*", "uid_t|gid_t", _typedef_rewrite_as_int],
        #
        # Rewrite without leading "::".
        #
        ["org::kde", "KDirNotify", "", ".*", _typedef_rewrite_without_colons],
        ["org::kde", "KSSLDInterface", "", ".*", _typedef_rewrite_without_colons],
        #
        # There are two version of KSharedConfigPtr in ksharedconfig.h and kconfiggroup.h.
        #
        [".*", "KSharedConfigPtr", ".*", "QExplicitlySharedDataPointer<KSharedConfig>", _typedef_discard],
        #
        # There are two version of Display in kstartupinfo.h and kxmessages.h.
        #
        ["kstartupinfo.h|kxmessages.h", "Display", ".*", ".*", _typedef_discard],
        ["kmimetypetrader.h", "KServiceOfferList", ".*", ".*", _typedef_discard],
        #
        # Redundant typedef.
        #
        ["agenttype.h", "QVariantMap", ".*", ".*", _typedef_discard],
    ]


def unexposed_rules():

    return [
    ]


def variable_rules():

    return [
        #
        # Discard variable emitted by QOBJECT.
        #
        [".*", "staticMetaObject", ".*", _variable_discard],
        #
        # Discard "private" variables (check they are protected!).
        #
        [".*", "d_ptr", ".*", _variable_discard_protected],
        [".*", "d", ".*Private.*", _variable_discard_protected],
    ]


class RuleSet(rules_engine.RuleSet):
    """
    SIP file generator rules. This is a set of (short, non-public) functions
    and regular expression-based matching rules.
    """
    def __init__(self):
        super(RuleSet, self).__init__(
            container_rules=container_rules, function_rules=function_rules,
            parameter_rules=parameter_rules, typedef_rules=typedef_rules,
            unexposed_rules=unexposed_rules, variable_rules=variable_rules,
            methodcode=common_methodcode.code, modulecode=common_modulecode.code, typecode=common_typecode.code)
        self.add_rules(
            container_rules=Akonadi.container_rules,
            typedef_rules=Akonadi.typedef_rules,
            unexposed_rules=Akonadi.unexposed_rules,
            variable_rules=Akonadi.variable_rules)
        self.add_rules(
            function_rules=KAuth.function_rules,
            modulecode=KAuth.modulecode)
        self.add_rules(
            container_rules=KBookmarks.container_rules,
            variable_rules=KBookmarks.variable_rules,
            modulecode=KBookmarks.modulecode,
            typecode=KBookmarks.typecode)
        self.add_rules(
            function_rules=KCoreAddons.function_rules,
            parameter_rules=KCoreAddons.parameter_rules,
            typecode=KCoreAddons.typecode)
        self.add_rules(
            container_rules=KCodecs.container_rules,
            function_rules=KCodecs.function_rules,
            parameter_rules=KCodecs.parameter_rules)
        self.add_rules(
            function_rules=KCompletion.function_rules)
        self.add_rules(
            container_rules=KConfig.container_rules,
            function_rules=KConfig.function_rules,
            modulecode=KConfig.modulecode,
            methodcode=KConfig.methodcode,
            typecode=KConfig.typecode)
        self.add_rules(
            parameter_rules=KConfigWidgets.parameter_rules,
            modulecode=KConfigWidgets.modulecode)
        self.add_rules(
            modulecode=KConfigGui.modulecode)
        self.add_rules(
            container_rules=KF5KDEGames.container_rules,
            function_rules=KF5KDEGames.function_rules,
            modulecode=KF5KDEGames.modulecode)
        self.add_rules(
            parameter_rules=KGuiAddons.parameter_rules)
        self.add_rules(
            function_rules=KIOCore.function_rules,
            typecode=KIOCore.typecode)
        self.add_rules(
            function_rules=KI18n.function_rules)
        self.add_rules(
            modulecode=KJobWidgets.modulecode,
            typecode=KJobWidgets.typecode)
        self.add_rules(
            parameter_rules=KLDAP.parameter_rules,
            variable_rules=KLDAP.variable_rules,
            typedef_rules=KLDAP.typedef_rules)
        self.add_rules(
            container_rules=KService.container_rules,
            typecode=KService.typecode)
        self.add_rules(
            function_rules=KWidgetsAddons.function_rules,
            parameter_rules=KWidgetsAddons.parameter_rules,
            modulecode=KWidgetsAddons.modulecode,
            typecode=KWidgetsAddons.typecode)
        self.add_rules(
            modulecode=KXmlGui.modulecode,
            methodcode=KXmlGui.methodcode)
        self.add_rules(
            function_rules=Syndication.function_rules,
            typedef_rules=Syndication.typedef_rules)

    def container_rules(self):
        return self._container_db

    def function_rules(self):
        return self._fn_db

    def parameter_rules(self):
        return self._param_db

    def typedef_rules(self):
        return self._typedef_db

    def unexposed_rules(self):
        return self._unexposed_db

    def variable_rules(self):
        return self._var_db

    def methodcode_rules(self):
        return self._methodcode

    def modulecode_rules(self):
        return self._modulecode

    def typecode_rules(self):
        return self._typecode

    def methodcode(self, function, sip):
        return self._methodcode.apply(function, sip)

    def modulecode(self, filename, sip):
        return self._modulecode.apply(filename, sip)

    def typecode(self, container, sip):
        return self._typecode.apply(container, sip)

    def modules(self):
        """
        The SIP modules we want to actually generate compiled bindings from.
        """
        return [
            "AkonadiAgentBase/AkonadiAgentBasemod.sip",
            "akonadi/akonadimod.sip",
            "Akonadi/Calendar/Calendarmod.sip",
            "Akonadi/Contact/Contactmod.sip",
            "AkonadiCore/AkonadiCoremod.sip",
            "Akonadi/KMime/KMimemod.sip",
            "Akonadi/Notes/Notesmod.sip",
            "akonadi/private/privatemod.sip",
            "AkonadiSearch/Debug/Debugmod.sip",
            "AkonadiSearch/PIM/PIMmod.sip",
            "Akonadi/SocialUtils/SocialUtilsmod.sip",
            "AkonadiWidgets/AkonadiWidgetsmod.sip",
            "AkonadiXml/AkonadiXmlmod.sip",
            "Attica/Attica/Atticamod.sip",
            "BalooWidgets/Baloo/Baloomod.sip",
            "BluezQt/BluezQt/BluezQtmod.sip",
            "gpgme++/gpgme++mod.sip",
            "gpgme++/interfaces/interfacesmod.sip",
            "KActivities/KActivities/KActivitiesmod.sip",
            "KAlarmCal/KAlarmCal/KAlarmCalmod.sip",
            "KArchive/KArchivemod.sip",
            "KAuth/KAuthmod.sip",
            "KBlog/KBlog/KBlogmod.sip",
            "KBookmarks/KBookmarksmod.sip",
            "KCalCore/KCalCore/KCalCoremod.sip",
            "KCalUtils/KCalUtils/KCalUtilsmod.sip",
            "KCMUtils/KCMUtilsmod.sip",
            "KCMUtils/ksettings/ksettingsmod.sip",
            "KCodecs/KCodecsmod.sip",
            "KCompletion/KCompletionmod.sip",
            "KConfigCore/KConfigCoremod.sip",
            "KConfigGui/KConfigGuimod.sip",
            "KConfigWidgets/KConfigWidgetsmod.sip",
            "KContacts/KContacts/KContactsmod.sip",
            "KCoreAddons/KCoreAddonsmod.sip",
            "KCrash/KCrashmod.sip",
            "KDBusAddons/KDBusAddonsmod.sip",
            "KDeclarative/CalendarEvents/CalendarEventsmod.sip",
            "KDeclarative/KDeclarative/KDeclarativemod.sip",
            "KDeclarative/KQuickAddons/KQuickAddonsmod.sip",
            "KDeclarative/QuickAddons/QuickAddonsmod.sip",
            "KDESu/KDESu/KDESumod.sip",
            "KDEWebKit/KDEWebKitmod.sip",
            "KDNSSD/DNSSD/DNSSDmod.sip",
            "KEmoticons/KEmoticonsmod.sip",
            "KF5KDEGames/highscore/highscoremod.sip",
            "KF5KDEGames/KDE/KDEmod.sip",
            "KF5KDEGames/KF5KDEGamesmod.sip",
            "KF5KDEGames/libkdegamesprivate/kgame/kgamemod.sip",
            "KF5KDEGames/libkdegamesprivate/libkdegamesprivatemod.sip",
            "KF5KMahjongg/KF5KMahjonggmod.sip",
            "KFileMetaData/KFileMetaData/KFileMetaDatamod.sip",
            "KGAPI/KGAPI/Blogger/Bloggermod.sip",
            "KGAPI/KGAPI/Calendar/Calendarmod.sip",
            "KGAPI/KGAPI/Contacts/Contactsmod.sip",
            "KGAPI/KGAPI/Drive/Drivemod.sip",
            "KGAPI/KGAPI/KGAPImod.sip",
            "KGAPI/KGAPI/Latitude/Latitudemod.sip",
            "KGAPI/KGAPI/Maps/Mapsmod.sip",
            "KGAPI/KGAPI/Tasks/Tasksmod.sip",
            "KGlobalAccel/KGlobalAccelmod.sip",
            "KGlobalAccel/private/privatemod.sip",
            "KGuiAddons/KGuiAddonsmod.sip",
            "KHolidays/KHolidays/KHolidaysmod.sip",
            "KHtml/dom/dommod.sip",
            "KHtml/KHtmlmod.sip",
            "KI18n/KI18nmod.sip",
            "KIconThemes/KIconThemesmod.sip",
            "KIdentityManagement/KIdentityManagement/KIdentityManagementmod.sip",
            "KIdleTime/KIdleTimemod.sip",
            "KIdleTime/private/privatemod.sip",
            "KIMAP/KIMAP/KIMAPmod.sip",
            "kimaptest/kimaptestmod.sip",
            "KIOCore/KIOCoremod.sip",
            "KIOCore/KIO/KIOmod.sip",
            "KIOFileWidgets/KIOFileWidgetsmod.sip",
            "kio/kiomod.sip",
            "KIOWidgets/KIO/KIOmod.sip",
            "KIOWidgets/KIOWidgetsmod.sip",
            "KItemModels/KItemModelsmod.sip",
            "KItemViews/KItemViewsmod.sip",
            "KJobWidgets/KJobWidgetsmod.sip",
            "kjs/bytecode/bytecodemod.sip",
            "KJsEmbed/KJsEmbed/KJsEmbedmod.sip",
            "kjs/kjsmod.sip",
            "KLDAP/KLDAP/KLDAPmod.sip",
            "KMbox/KMbox/KMboxmod.sip",
            "KMediaPlayer/KMediaPlayer/KMediaPlayermod.sip",
            "KMime/KMime/KMimemod.sip",
            "KNewStuff3/KNS3/KNS3mod.sip",
            "KNotifications/KNotificationsmod.sip",
            "KNotifyConfig/KNotifyConfigmod.sip",
            "KontactInterface/KontactInterface/KontactInterfacemod.sip",
            "KPackage/KPackage/KPackagemod.sip",
            "KParts/KParts/KPartsmod.sip",
            "KParts/KPartsmod.sip",
            "KPeople/KPeopleBackend/KPeopleBackendmod.sip",
            "KPeople/KPeople/KPeoplemod.sip",
            "KPeople/KPeople/Widgets/Widgetsmod.sip",
            "KPIMTextEdit/KPIMTextEdit/KPIMTextEditmod.sip",
            "KPlotting/KPlottingmod.sip",
            "KPty/KPtymod.sip",
            "KrossCore/Kross/Core/Coremod.sip",
            "KrossUi/Kross/Ui/Uimod.sip",
            "KRunner/KRunner/KRunnermod.sip",
            "KScreen/KScreen/KScreenmod.sip",
            "KService/KServicemod.sip",
            "KStyle/KStylemod.sip",
            "KTextEditor/KTextEditor/KTextEditormod.sip",
            "KTextWidgets/KTextWidgetsmod.sip",
            "KTNEF/KTNEF/KTNEFmod.sip",
            "KUnitConversion/KUnitConversion/KUnitConversionmod.sip",
            "KWallet/KWalletmod.sip",
            "KWidgetsAddons/KWidgetsAddonsmod.sip",
            "KWindowSystem/KWindowSystemmod.sip",
            "KWindowSystem/private/privatemod.sip",
            "KXmlGui/KXmlGuimod.sip",
            "KXmlRpcClient/KXmlRpcClient/KXmlRpcClientmod.sip",
            "MailTransport/MailTransport/MailTransportmod.sip",
            "NetworkManagerQt/NetworkManagerQt/NetworkManagerQtmod.sip",
            "Plasma/Plasmamod.sip",
            "plasma/scripting/scriptingmod.sip",
            "PRISON/prison/prisonmod.sip",
            "purpose/Purpose/Purposemod.sip",
            "purposewidgets/PurposeWidgets/PurposeWidgetsmod.sip",
            "qgpgme/qgpgmemod.sip",
            "Solid/Solid/Solidmod.sip",
            "SonnetCore/Sonnet/Sonnetmod.sip",
            "SonnetUi/Sonnet/Sonnetmod.sip",
            "Syndication/Syndication/Atom/Atommod.sip",
            "Syndication/Syndication/Rdf/Rdfmod.sip",
            "Syndication/Syndication/Rss2/Rss2mod.sip",
            "Syndication/Syndication/Syndicationmod.sip",
            "ThreadWeaver/ThreadWeaver/ThreadWeavermod.sip",
            "wtf/wtfmod.sip",
            "XsltKde/XsltKdemod.sip",
        ]
