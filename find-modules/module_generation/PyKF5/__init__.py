#
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
#
"""
SIP binding customisation for PyKF5. This modules describes:

    * The SIP file generator rules.

    * The SIP compilation rules.

"""

from __future__ import print_function
from importlib import import_module
import os
import re
import sys

from clang.cindex import AccessSpecifier

import PyQt_templates
import rule_helpers
import rules_engine
import common_methodcode
import common_modulecode
import common_typecode
from clangcparser import CursorKind


QT_DICT = "QHash|QMap"
QT_LIST = "QList|QVector"
QT_SET = "QSet"
QT_PAIR = "QPair"
QT_PTRS = PyQt_templates.QT_PTRS

RE_QT_DICT_TYPEDEF = "(" + QT_DICT + ")<(.*)>"
RE_QT_LIST_TYPEDEF = "(" + QT_LIST + ")<(.*)>"
RE_QT_SET_TYPEDEF = QT_SET + "<(.*)>"
RE_QT_PAIR_TYPEDEF = QT_PAIR + "<(.*)>"
RE_QT_PTRS_TYPEDEF = QT_PTRS + "<(.*)>"

RE_QT_DICT_PARAMETER = "(const )?" + RE_QT_DICT_TYPEDEF + ".*"
RE_QT_LIST_PARAMETER = "(const )?" + RE_QT_LIST_TYPEDEF + ".*"
RE_QT_SET_PARAMETER = "(const )?" + RE_QT_SET_TYPEDEF + ".*"
RE_QT_PAIR_PARAMETER = "(const )?" + RE_QT_PAIR_TYPEDEF + ".*"
RE_QT_PTRS_PARAMETER = "(const )?" + RE_QT_PTRS_TYPEDEF + ".*"

KNOWN_TEMPLATES = [
    QT_DICT, QT_LIST, QT_SET, QT_PAIR, QT_PTRS
]
RE_KNOWN_RESULTS = "(const )?((" + ")|(".join(KNOWN_TEMPLATES) + "))<(.*)>"


def _container_discard_templated_bases(container, sip, matcher):
    sip["base_specifiers"] = [b for b in sip["base_specifiers"] if "<" not in b]


def _function_discard_class(container, fn, sip, matcher):
    sip["fn_result"] = sip["fn_result"].replace("class ", "")


def _function_discard_impl(container, fn, sip, matcher):
    if fn.extent.start.column == 1:
        rule_helpers.function_discard(container, fn, sip, matcher)


def _function_discard_non_const(container, fn, sip, matcher):
    if not sip["suffix"]:
        rule_helpers.function_discard(container, fn, sip, matcher)


def _function_discard_protected(container, fn, sip, matcher):
    if fn.access_specifier == AccessSpecifier.PROTECTED:
        rule_helpers.function_discard(container, fn, sip, matcher)


def _parameter_rewrite_without_colons(container, fn, parameter, sip, matcher):
    sip["decl"] = sip["decl"].replace("::", "")


def _parameter_transfer_to_parent(container, fn, parameter, sip, matcher):
    if fn.kind != CursorKind.CONSTRUCTOR and \
        not fn.spelling.startswith("create"):
        #
        # This does not look like a constructor or a factory method.
        #
        return rule_helpers.SILENT_NOOP
    if fn.is_static_method():
        sip["annotations"].add("Transfer")
    else:
        sip["annotations"].add("TransferThis")


def _parameter_set_max_int(container, fn, parameter, sip, matcher):
    sip["init"] = "(uint)-1"


def _parameter_strip_class_enum(container, fn, parameter, sip, matcher):
    sip["decl"] = sip["decl"].replace("class ", "").replace("enum ", "")


def _typedef_discard(container, typedef, sip, matcher):
    sip["name"] = ""


def _typedef_rewrite_as_int(container, typedef, sip, matcher):
    sip["decl"] = "int"


def _typedef_rewrite_without_colons(container, typedef, sip, matcher):
    sip["decl"] = sip["decl"].strip(":")


def _variable_discard_protected(container, variable, sip, matcher):
    if variable.access_specifier in [AccessSpecifier.PROTECTED, AccessSpecifier.PRIVATE]:
        rule_helpers.variable_discard(container, variable, sip, matcher)


def container_rules():
    return [
        #
        # Discard Qt metatype system.
        #
        [".*", "(QMetaTypeId|QTypeInfo)", ".*", ".*", ".*", rule_helpers.container_discard],
        #
        # SIP cannot handle templated containers with a base which is a template parameter.
        #
        ["kimagecache.h", "KSharedPixmapCacheMixin", ".+", ".*", ".*", rule_helpers.container_discard],
        #
        # SIP does not seem to be able to handle templated base classes.
        #
        [".*", ".*", ".*", ".*", ".*<.*", _container_discard_templated_bases],
        #
        # SIP does not seem to be able to handle empty containers.
        #
        ["KParts::ScriptableExtension", "Null|Undefined", ".*", ".*", ".*", rule_helpers.container_discard],
        #
        # This is pretty much a disaster area. TODO: can we rescue some parts?
        #
        [".*", "KConfigCompilerSignallingItem", ".*", ".*", ".*", rule_helpers.container_discard],
        ["ConversionCheck", ".*", ".*", ".*", ".*", rule_helpers.container_discard],
    ]


def function_rules():
    return [
        #
        # Discard functions emitted by QOBJECT.
        #
        [".*", "metaObject|qt_metacast|tr|trUtf8|qt_metacall|qt_check_for_QOBJECT_macro", ".*", ".*", ".*", rule_helpers.function_discard],
        [".*", "d_func", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # SIP does not support operator=.
        #
        [".*", "operator=", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # TODO: Temporarily remove any functions which require templates.
        #
        [".*", ".*", ".+", ".*", ".*", rule_helpers.function_discard],
        [".*", ".*<.*>.*", ".*", ".*", ".*", rule_helpers.function_discard],
        [".*", ".*", ".*", RE_KNOWN_RESULTS + "( [&*]+)?", ".*", PyQt_templates.function_uses_templates],
        [".*", ".*", ".*", ".*", ".*" + RE_KNOWN_RESULTS + "( .*|[&*].*)", PyQt_templates.function_uses_templates],
        #
        # This class has inline implementations in the header file.
        #
        ["KIconEngine|KIconLoader::Group", ".*", ".*", ".*", ".*", _function_discard_impl],
        ["kiconloader.h", "operator\+\+", ".*", ".*", ".*", _function_discard_impl],
        #
        # kshell.h, kconfigbase.sip have inline operators.
        #
        [".*", "operator\|", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Inline operators.
        #
        ["KFileItem", "operator QVariant", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KService", "operator KPluginName", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KCalCore::Duration", "operator bool|operator!", ".*", ".*", "", rule_helpers.function_discard],
        ["KPageDialog", "pageWidget|buttonBox", ".*", ".*", "", _function_discard_non_const],
        [".*", ".*", ".*", ".*", ".*Private.*", _function_discard_protected],
        #
        # This fn does not exist.
        #
        [".*", "qt_check_for_QGADGET_macro", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # SIP thinks there are duplicate signatures.
        #
        [".*", "qobject_cast", ".*", ".*", ".*", rule_helpers.function_discard],
        [".*", "qobject_interface_iid", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # QDebug is not exposed.
        #
        [".*", "operator<<", ".*", "QDebug.*", ".*", rule_helpers.function_discard],
    ]


def parameter_rules():
    return [
        #
        # Annotate with Transfer or TransferThis when we see a parent object.
        #
        [".*", ".*", ".*", r"[KQ][A-Za-z_0-9]+\W*\*\W*parent", ".*", _parameter_transfer_to_parent],
        ["KCoreConfigSkeleton", "addItem.*", "reference", ".*", ".*", rule_helpers.parameter_in],
        ["KDateTime", "fromString", "negZero", ".*", ".*", rule_helpers.parameter_out],
        ["KPty", "tcGetAttr|tcSetAttr", "ttmode", ".*", ".*", _parameter_rewrite_without_colons],
        #
        # TODO: Temporarily trim any parameters which start "enum".
        #
        ["KAboutData", ".*", "licenseType", ".*", ".*", _parameter_strip_class_enum],
        #
        # Supplement Qt templates with %MappedTypes.
        #
        [".*", ".*", ".*", RE_QT_DICT_PARAMETER, ".*", PyQt_templates.dict_parameter],
        [".*", ".*", ".*", RE_QT_LIST_PARAMETER, ".*", PyQt_templates.list_parameter],
        [".*", ".*", ".*", RE_QT_SET_PARAMETER, ".*", PyQt_templates.set_parameter],
        [".*", ".*", ".*", RE_QT_PAIR_PARAMETER, ".*", PyQt_templates.pair_parameter],
        [".*", ".*", ".*", RE_QT_PTRS_PARAMETER, ".*", PyQt_templates.pointer_parameter],
    ]


def typedef_rules():
    return [
        #
        # Supplement Qt templates with manual code.
        #
        [".*", ".*", ".*", RE_QT_DICT_TYPEDEF, PyQt_templates.dict_typecode],
        [".*", ".*", ".*", RE_QT_LIST_TYPEDEF, PyQt_templates.list_typecode],
        [".*", ".*", ".*", RE_QT_SET_TYPEDEF, PyQt_templates.set_typecode],
        [".*", ".*", ".*", RE_QT_PAIR_TYPEDEF, PyQt_templates.pair_typecode],
        [".*", ".*", ".*", RE_QT_PTRS_TYPEDEF, PyQt_templates.pointer_typecode],
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
        [".*", "staticMetaObject", ".*", rule_helpers.variable_discard],
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
        super(RuleSet, self).__init__(rules_module=sys.modules[__name__], methodcode=common_methodcode.code,
                                      modulecode=common_modulecode.code, typecode=common_typecode.code)
        for rules_module in [
            "Akonadi",
            "FollowupReminder",
            "gpgme__",
            "KAlarmCal",
            "KAuth",
            "KBlog",
            "KBookmarks",
            "KCalCore",
            "KCalUtils",
            "KCMUtils",
            "KCoreAddons",
            "KCodecs",
            "KCompletion",
            "KConfigCore",
            "KConfigGui",
            "KConfigWidgets",
            "KContacts",
            "KCrash",
            "KDeclarative",
            "KdepimDBusInterfaces",
            "KEmoticons",
            "KF5KDEGames",
            "KGAPI",
            "KGeoMap",
            "KGlobalAccel",
            "KHtml",
            "KIMAP",
            "KIO",
            "KIPI",
            "KItemViews",
            "KI18n",
            "KItemModels",
            "KJobWidgets",
            "KJS",
            "KLDAP",
            "KMbox",
            "KMime",
            "KNewStuff3",
            "KNotifyConfig",
            "KNotifications",
            "KPackage",
            "KParts",
            "KPty",
            "Kross",
            "KRunner",
            "KScreen",
            "KService",
            "KStyle",
            "KTextEditor",
            "KTNEF",
            "KUnitConversion",
            "KWidgetsAddons",
            "KXmlGui",
            "Libkdepim",
            "MailImporter",
            "MailTransport",
            "MessageCore",
            "MessageList",
            "SendLater",
            "Solid",
            "Sonnet",
            "Syndication",
        ]:
            self.add_rules(
                rules_module=import_module("." + rules_module, self.__module__))
        self.pd_cache = None

    def _fill_cache(self):
        if self.pd_cache is None:
            self.pd_cache = rules_engine.get_platform_dependencies(os.path.dirname(os.path.realpath(__file__)))

    def _update_dir_set(self, result, key1, key2):
        self._fill_cache()
        for component, data in self.pd_cache[key1].items():
            dirlist = data[key2].split(";")
            dirlist = [os.path.normpath(i) for i in dirlist if i]
            result.update(dirlist)

    def cxx_source_root(self):
        self._fill_cache()
        return self.pd_cache["CXX_SOURCE_ROOT"]

    def cxx_sources(self):
        source_root = self.cxx_source_root() + os.path.sep
        result = set()
        self._update_dir_set(result, "CXX_SOURCES", "INCLUDE_DIRS")
        #
        # We exclude anything which is not under the source root: those are dependencies!
        #
        result = sorted([i for i in result if i.startswith(source_root)])
        #
        # Collapse any subdirectories.
        #
        i = 0
        j = 0
        c = "\x00"
        while i < len(result):
            if result[i].startswith(c + os.path.sep):
                pass
            else:
                c = result[i]
                result[j] = c
                j += 1
            i += 1
        result = result[:j]
        #
        # Akonadi private.
        #
        result.append(os.path.join(source_root, "akonadi", "abstractsearchplugin.h"))
        result.append(os.path.join(source_root, "akonadi", "private"))
        #
        # Include KIOCore/kio/job_base.h.
        #
        result.append(os.path.join(source_root, "KIOCore", "kio", "job_base.h"))
        #
        # KF5KIO is missing .../kio.
        # KF5JS is missing .../kjs and .../wtf.
        #
        result.append(os.path.join(source_root, "kio"))
        result.append(os.path.join(source_root, "kjs"))
        result.append(os.path.join(source_root, "wtf"))
        result.append(os.path.join(source_root, "MailTransport", "mailtransport", "sentactionattribute.h"))
        result.append(os.path.join(source_root, "MailTransport", "mailtransport", "transportbase.h"))
        result = sorted(result)
        return result

    def cxx_includes(self):
        source_root = self.cxx_source_root() + os.path.sep
        result = set()
        self._update_dir_set(result, "CXX_DEPENDENCIES", "INCLUDE_DIRS")
        #
        # We include anything which is not under the source root: those are dependencies too!
        #
        self._update_dir_set(result, "CXX_SOURCES", "INCLUDE_DIRS")
        result = [i for i in result if not i.startswith(source_root)]
        result = sorted(result)
        return result

    def cxx_compile_flags(self):
        result = set(self.pd_cache["CXX_COMPILE_OPTIONS"].split(";"))
        self._update_dir_set(result, "CXX_DEPENDENCIES", "COMPILE_FLAGS")
        self._update_dir_set(result, "CXX_DEPENDENCIES", "COMPILE_FLAGS")
        result = [i for i in result]
        result = sorted(result)
        return result

    def cxx_libraries(self):
        result = set()
        self._update_dir_set(result, "CXX_SOURCES", "LIBRARIES")
        self._update_dir_set(result, "CXX_DEPENDENCIES", "LIBRARIES")
        result = [i for i in result]
        result = sorted(result)
        return result

    @property
    def cxx_selector(self):
        return re.compile(".*")

    @property
    def cxx_omitter(self):
        return re.compile("KDELibs4Support|ksslcertificatemanager_p.h")

    def sip_package(self):
        self._fill_cache()
        return self.pd_cache["SIP_PACKAGE"]

    def sip_imports(self):
        self._fill_cache()
        result = set()
        dirlist = self.pd_cache["SIP_DEPENDENCIES"].split(";")
        result.update(dirlist)
        result = [i for i in result if i]
        result = sorted(result)
        return result
