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

from clang.cindex import AccessSpecifier

import rules_engine
from PyQt_templates import function_uses_templates, dict_typecode, list_typecode, set_typecode, \
    qpair_parameter, qshareddatapointer_parameter
import common_methodcode
import common_modulecode
import common_typecode


RE_QSHAREDPTR = "(const )?(Q(Explicitly|)Shared(Data|)Pointer)<(.*)>"


def _container_discard_templated_bases(container, sip, matcher):
    sip["base_specifiers"] = [b for b in sip["base_specifiers"] if "<" not in b]


def _function_discard_class(container, fn, sip, matcher):
    sip["fn_result"] = sip["fn_result"].replace("class ", "")


def _function_discard_impl(container, fn, sip, matcher):
    if fn.extent.start.column == 1:
        rules_engine.function_discard(container, fn, sip, matcher)


def _function_discard_non_const(container, fn, sip, matcher):
    if not sip["suffix"]:
        rules_engine.function_discard(container, fn, sip, matcher)


def _function_discard_protected(container, fn, sip, matcher):
    if fn.access_specifier == AccessSpecifier.PROTECTED:
        rules_engine.function_discard(container, fn, sip, matcher)


def _parameter_rewrite_without_colons(container, fn, parameter, sip, matcher):
    sip["decl"] = sip["decl"].replace("::", "")


def _parameter_transfer_to_parent(container, fn, parameter, sip, matcher):
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
        rules_engine.variable_discard(container, variable, sip, matcher)


def container_rules():
    return [
        #
        # Discard Qt metatype system.
        #
        [".*", "(QMetaTypeId|QTypeInfo)", ".*", ".*", ".*", rules_engine.container_discard],
        #
        # SIP cannot handle templated containers with a base which is a template parameter.
        #
        ["kimagecache.h", "KSharedPixmapCacheMixin", ".+", ".*", ".*", rules_engine.container_discard],
        #
        # SIP does not seem to be able to handle templated base classes.
        #
        [".*", ".*", ".*", ".*", ".*<.*", _container_discard_templated_bases],
        #
        # SIP does not seem to be able to handle empty containers.
        #
        ["KParts::ScriptableExtension", "Null|Undefined", ".*", ".*", ".*", rules_engine.container_discard],
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
        # TODO: Temporarily remove any functions which require templates.
        #
        [".*", ".*", ".+", ".*", ".*", rules_engine.function_discard],
        [".*", ".*<.*>.*", ".*", ".*", ".*", rules_engine.function_discard],
        [".*", ".*", ".*", RE_QSHAREDPTR, ".*", function_uses_templates],
        [".*", ".*", ".*", ".*", ".*" + RE_QSHAREDPTR + ".*", function_uses_templates],
        #
        # This class has inline implementations in the header file.
        #
        ["KIconEngine|KIconLoader::Group", ".*", ".*", ".*", ".*", _function_discard_impl],
        ["kiconloader.h", "operator\+\+", ".*", ".*", ".*", _function_discard_impl],
        #
        # kshell.h, kconfigbase.sip have inline operators.
        #
        [".*", "operator\|", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # Inline operators.
        #
        ["KFileItem", "operator QVariant", ".*", ".*", ".*", rules_engine.function_discard],
        ["KService", "operator KPluginName", ".*", ".*", ".*", rules_engine.function_discard],
        ["KCalCore::Duration", "operator bool|operator!", ".*", ".*", "", rules_engine.function_discard],
        ["KPageDialog", "pageWidget|buttonBox", ".*", ".*", "", _function_discard_non_const],
        [".*", ".*", ".*", ".*", ".*Private.*", _function_discard_protected],
        #
        # This fn does not exist.
        #
        [".*", "qt_check_for_QGADGET_macro", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # SIP thinks there are duplicate signatures.
        #
        [".*", "qobject_cast", ".*", ".*", ".*", rules_engine.function_discard],
        [".*", "qobject_interface_iid", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # QDebug is not exposed.
        #
        [".*", "operator<<", ".*", "QDebug.*", ".*", rules_engine.function_discard],
    ]


def parameter_rules():
    return [
        #
        # Annotate with Transfer or TransferThis when we see a parent object.
        #
        [".*", ".*", ".*", r"[KQ][A-Za-z_0-9]+\W*\*\W*parent", ".*", _parameter_transfer_to_parent],
        ["KCoreConfigSkeleton", "addItem.*", "reference", ".*", ".*", rules_engine.parameter_in],
        ["KDateTime", "fromString", "negZero", ".*", ".*", rules_engine.parameter_out],
        ["KPty", "tcGetAttr|tcSetAttr", "ttmode", ".*", ".*", _parameter_rewrite_without_colons],
        #
        # TODO: Temporarily trim any parameters which start "enum".
        #
        ["KAboutData", ".*", "licenseType", ".*", ".*", _parameter_strip_class_enum],
        #
        # Create %MappedTypes.
        #
        [".*", ".*", ".*", "(const )?QPair<.*>.*", ".*", qpair_parameter],
        [".*", ".*", ".*", RE_QSHAREDPTR + ".*", ".*", qshareddatapointer_parameter],
    ]


def typedef_rules():
    return [
        #
        # Supplement Qt templates with manual code.
        #
        [".*", ".*", ".*", "QHash<.*>", dict_typecode],
        [".*", ".*", ".*", "QList<.*>", list_typecode],
        [".*", ".*", ".*", "QMap<.*>", dict_typecode],
        [".*", ".*", ".*", "QSet<.*>", set_typecode],
        [".*", ".*", ".*", "QVector<.*>", list_typecode],
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
        [".*", "staticMetaObject", ".*", rules_engine.variable_discard],
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
            container_rules=container_rules, forward_declaration_rules=lambda: [],
            function_rules=function_rules, parameter_rules=parameter_rules, typedef_rules=typedef_rules,
            unexposed_rules=unexposed_rules, variable_rules=variable_rules,
            methodcode=common_methodcode.code, modulecode=common_modulecode.code, typecode=common_typecode.code)
        for rules_module in [
            "Akonadi",
            "KAuth",
            "KBookmarks",
            "KCalCore",
            "KCoreAddons",
            "KCodecs",
            "KCompletion",
            "KConfigCore",
            "KConfigGui",
            "KConfigWidgets",
            "KContacts",
            "KCrash",
            "KdepimDBusInterfaces",
            "KF5KDEGames",
            "KGeoMap",
            "kio",
            "KIOCore",
            "KItemViews",
            "KI18n",
            "KJobWidgets",
            "KLDAP",
            "KMime",
            "KNotifyConfig",
            "KNotifications",
            "KParts",
            "KService",
            "KStyle",
            "KTextEditor",
            "KUnitConversion",
            "KWidgetsAddons",
            "KXmlGui",
            "MessageCore",
            "Sonnet",
            "Syndication",
        ]:
            rules_module = import_module("." + rules_module, self.__module__)
            self.add_rules(
                container_rules=getattr(rules_module, "container_rules", None),
                forward_declaration_rules=getattr(rules_module, "forward_declaration_rules", None),
                function_rules=getattr(rules_module, "function_rules", None),
                parameter_rules=getattr(rules_module, "parameter_rules", None),
                typedef_rules=getattr(rules_module, "typedef_rules", None),
                unexposed_rules=getattr(rules_module, "unexposed_rules", None),
                variable_rules=getattr(rules_module, "variable_rules", None),
                methodcode=getattr(rules_module, "methodcode", None),
                modulecode=getattr(rules_module, "modulecode", None),
                typecode=getattr(rules_module, "typecode", None))
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
        result = [i for i in result if i.startswith(source_root)]
        #
        # Include KIOCore/kio/job_base.h.
        #
        for source in result:
            if source.endswith("KIOCore"):
                result.append(os.path.join(source, "kio", "job_base.h"))
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
        QT5_COMPILE_FLAGS = ["-fPIC", "-std=gnu++14"]
        return QT5_COMPILE_FLAGS

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
