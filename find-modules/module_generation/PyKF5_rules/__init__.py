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
import os
import re
import sys

from clang.cindex import AccessSpecifier, CursorKind

import rules_engine
from builtin_rules import make_cxx_declaration
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_methodcode
import common_modulecode
import common_typecode
import Akonadi
import KAuth
import KBookmarks
import KCalCore
import KCoreAddons
import KCodecs
import KCompletion
import KConfigCore
import KConfigGui
import KConfigWidgets
import KContacts
import KCrash
import KF5KDEGames
import KGeoMap
import kio
import KIOCore
import KI18n
import KJobWidgets
import KLDAP
import KMime
import KNotifyConfig
import KNotifications
import KService
import KStyle
import KUnitConversion
import KWidgetsAddons
import KXmlGui
import MessageCore
import Sonnet
import Syndication
import PyQt_templates
from PyQt_templates import typecode_cfttc_dict, typecode_cfttc_list, typecode_cfttc_set
from sip_generator import trace_generated_for
from builtin_rules import HeldAs, fqn


RE_PARAMETER_TYPE = re.compile(r"(.*\b)\w+")
RE_QSHAREDPTR = re.compile("(const )?(Q(Explicitly|)Shared(Data|)Pointer)<(.*)>")


def _container_discard_templated_bases(container, sip, matcher):
    sip["base_specifiers"] = [b for b in sip["base_specifiers"] if not "<" in b]


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


class QSharedHelper(HeldAs):
    def __init__(self, cxx_t, clang_kind, manual_t=None):
        is_qshared = RE_QSHAREDPTR.match(cxx_t)
        if is_qshared:
            template_type = is_qshared.group(2)
            template_args = [(is_qshared.group(1) or "") + is_qshared.group(5)]
            cxx_t = template_args[0] + " *"
        super(QSharedHelper, self).__init__(cxx_t, clang_kind, manual_t)
        self.is_qshared = is_qshared


class RewriteResultHelper(QSharedHelper):
    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        if self.is_qshared:
            cxx_i += ".data()"
        return super(RewriteResultHelper, self).cxx_to_py(name, needs_reference, cxx_i, cxx_po)

    cxx_to_py_templates = {
        HeldAs.INTEGER:
            """    {name} = {cxx_i};
#if PY_MAJOR_VERSION >= 3
    return PyLong_FromLong((long){name});
#else
    return PyInt_FromLong((long){name});
#endif
""",
        HeldAs.FLOAT:
            """    {name} = {cxx_i};
    return PyFloat_FromDouble((double){name});
""",
        HeldAs.POINTER:
            """    {name} = {cxx_i};
    return sipConvertFromType({name}, genresultT, {transfer});
""",
        HeldAs.OBJECT:
            """    {name} = &{cxx_i};
    return sipConvertFromType({name}, genresultT, {transfer});
""",
    }

    def cxx_to_py_template(self):
        return self.cxx_to_py_templates[self.category]


def fn_result_is_qt_template(container, function, sip, matcher):
    def in_class(item):
        parent = item.semantic_parent
        while parent and parent.kind != CursorKind.CLASS_DECL:
            parent = parent.semantic_parent
        return True if parent else False

    make_cxx_declaration(sip)
    #
    # Deal with function result.
    #
    result_h = RewriteResultHelper(sip["fn_result"], None)
    if function.kind != CursorKind.CONSTRUCTOR and result_h.category == HeldAs.OBJECT:
        sip["fn_result"] += " *"
    #
    # Now the function parameters.
    #
    clang_kinds = [c.type.get_canonical() for c in function.get_children() if c.kind == CursorKind.PARM_DECL]
    parameters_h = []
    sip_parameters = []
    sip_stars = []
    code = """%MethodCode
{}
"""
    #
    # Generate parameter list, unwrapping shared data as needed.
    #
    for i, p in enumerate(sip["cxx_parameters"]):
        #
        # Get to type by removing any default value then stripping the name.
        #
        type_text = p.split("=", 1)[0].strip()
        type_text = RE_PARAMETER_TYPE.match(type_text).group(1).strip()
        parameter_h = QSharedHelper(type_text, clang_kinds[i].kind)
        if parameter_h.is_qshared:
            sip["parameters"][i] = sip["parameters"][i].replace(type_text, parameter_h.cxx_t)
            code += """            typedef """ + type_text + """ Cxxa0T;
            Cxxa0T *cxxa0;
            cxxa0 = new Cxxa0T(a0);
""".replace("a0", "a{}".format(i))
            sip_parameters.append("cxxa{}".format(i))
            sip_stars.append("*cxxa{}".format(i))
        else:
            sip_parameters.append("a{}".format(i))
            if parameter_h.category == HeldAs.OBJECT:
                sip_stars.append("*a{}".format(i))
            else:
                sip_stars.append("a{}".format(i))
        parameters_h.append(parameter_h)
    trace = trace_generated_for(function, fn_result_is_qt_template,
                                [(result_h.cxx_t, result_h.category), [(p.cxx_t, p.category) for p in parameters_h]])
    code = code.format(trace)
    #
    # Generate function name.
    #
    fn = function.spelling
    if "static " in sip["prefix"] or not in_class(function):
        fn = fqn(container, fn)
    elif function.kind == CursorKind.CONSTRUCTOR:
        fn = "sip" + fqn(container, "")[:-2].replace("::", "_")
    elif not fn.startswith("operator"):
        if function.access_specifier == AccessSpecifier.PROTECTED:
            fn = "sipCpp->sipProtect_" + fn
        else:
            fn = "sipCpp->" + fn
    #
    # Generate function call, unwrapping shared data result as needed.
    #
    if result_h.category == HeldAs.VOID:
        code += """    Py_BEGIN_ALLOW_THREADS
    {}({});
    Py_END_ALLOW_THREADS""".format(fn, ", ".join(sip_stars))
    elif function.kind == CursorKind.CONSTRUCTOR:
        code += """    Py_BEGIN_ALLOW_THREADS
    sipCpp = new {}({});
    Py_END_ALLOW_THREADS""".format(fn, ", ".join(sip_stars))
    else:
        code += """    typedef {} CxxvalueT;
        CxxvalueT cxxvalue;

        Py_BEGIN_ALLOW_THREADS
        cxxvalue = {}({});
        Py_END_ALLOW_THREADS
""".format(sip["cxx_fn_result"], fn, ", ".join(sip_stars))
        if result_h.is_qshared:
            sip["fn_result"] = result_h.cxx_t
        code += result_h.declare_type_helpers("result", "return 0;")
        code += result_h.cxx_to_py("sipRes", False, "cxxvalue")
    code += """
%End
"""
    if "virtual" in sip["prefix"]:
        if result_h.category == HeldAs.VOID:
            code += """%VirtualCatcherCode
{}
        PyObject *result = PyObject_CallFunctionObjArgs(sipMethod, {}NULL);
        if (result == NULL) {{
            sipIsErr = 1;

            // TBD: Free all the pyobjects.
        }}
%End
""".format(trace, "".join([p + ", " for p in sip_parameters]))
        else:
            code += """%VirtualCatcherCode
{}
        PyObject *result = PyObject_CallFunctionObjArgs(sipMethod, {}NULL);
        if (result == NULL) {{
            sipIsErr = 1;

            // TBD: Free all the pyobjects.
        }} else {{
            // Convert the result to the C++ type. TBD: Figure out type encodings?
            sipParseResult(&sipIsErr, sipMethod, result, "i", &sipRes);
            Py_DECREF(result);
        }}
%End
""".format(trace, "".join([p + ", " for p in sip_parameters]))
    sip["code"] = code


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
        [".*", "(QMetaTypeId|QTypeInfo)<.*>", ".*", ".*", ".*", rules_engine.container_discard],
        #
        # SIP does not seem to be able to handle templated containers.
        #
        [".*", ".*<.*", ".*", ".*", ".*", rules_engine.container_discard],
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
        [".*", ".*", ".*", "(?!QFlags)Q[A-Za-z0-9_]+<.*>", ".*", fn_result_is_qt_template],
        [".*", ".*", ".*", ".*", "(?!QFlags)Q[A-Za-z0-9_]+<.*>.*", fn_result_is_qt_template],
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
        # This function does not exist.
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
        ["KCoreConfigSkeleton", "addItem.*", "reference", ".*", ".*", _parameter_in],
        ["KDateTime", "fromString", "negZero", ".*", ".*", _parameter_out],
        ["KPty", "tcGetAttr|tcSetAttr", "ttmode", ".*", ".*", _parameter_rewrite_without_colons],
        #
        # TODO: Temporarily trim any parameters which start "enum".
        #
        ["KAboutData", ".*", "licenseType", ".*", ".*", _parameter_strip_class_enum],
        #
        # Create %MappedTypes.
        #
        [".*", ".*", ".*", "(const )?QPair<.*>.*", ".*", PyQt_templates.qpair_parameter],
        [".*", ".*", ".*", "(const )?Q(Explicitly|)SharedDataPointer<.*>.*", ".*", PyQt_templates.qshareddatapointer_parameter],
    ]


def typedef_rules():

    return [
        #
        # Supplement Qt templates with manual code.
        #
        [".*", ".*", ".*", "QHash<.*>", typecode_cfttc_dict],
        [".*", ".*", ".*", "QList<.*>", typecode_cfttc_list],
        [".*", ".*", ".*", "QMap<.*>", typecode_cfttc_dict],
        [".*", ".*", ".*", "QSet<.*>", typecode_cfttc_set],
        [".*", ".*", ".*", "QVector<.*>", typecode_cfttc_list],
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
            container_rules=container_rules, forward_declaration_rules=lambda: [],
            function_rules=function_rules, parameter_rules=parameter_rules, typedef_rules=typedef_rules,
            unexposed_rules=unexposed_rules, variable_rules=variable_rules,
            methodcode=common_methodcode.code, modulecode=common_modulecode.code, typecode=common_typecode.code)
        self.add_rules(
            container_rules=Akonadi.container_rules,
            forward_declaration_rules=Akonadi.forward_declaration_rules,
            function_rules=Akonadi.function_rules,
            parameter_rules=Akonadi.parameter_rules,
            typedef_rules=Akonadi.typedef_rules,
            variable_rules=Akonadi.variable_rules,
            typecode=Akonadi.typecode,
            modulecode=Akonadi.modulecode)
        self.add_rules(
            function_rules=KAuth.function_rules,
            modulecode=KAuth.modulecode)
        self.add_rules(
            container_rules=KBookmarks.container_rules,
            function_rules=KBookmarks.function_rules,
            variable_rules=KBookmarks.variable_rules,
            modulecode=KBookmarks.modulecode,
            typecode=KBookmarks.typecode)
        self.add_rules(
            typedef_rules=KCalCore.typedef_rules)
        self.add_rules(
            container_rules=KCoreAddons.container_rules,
            function_rules=KCoreAddons.function_rules,
            typecode=KCoreAddons.typecode)
        self.add_rules(
            container_rules=KCodecs.container_rules,
            function_rules=KCodecs.function_rules)
        self.add_rules(
            container_rules=KCompletion.container_rules,
            function_rules=KCompletion.function_rules,
            parameter_rules=KCompletion.parameter_rules)
        self.add_rules(
            container_rules=KConfigCore.container_rules,
            function_rules=KConfigCore.function_rules,
            typedef_rules=KConfigCore.typedef_rules,
            modulecode=KConfigCore.modulecode,
            methodcode=KConfigCore.methodcode,
            typecode=KConfigCore.typecode)
        self.add_rules(
            container_rules=KConfigGui.container_rules,
            modulecode=KConfigGui.modulecode)
        self.add_rules(
            function_rules=KConfigWidgets.function_rules,
            parameter_rules=KConfigWidgets.parameter_rules,
            modulecode=KConfigWidgets.modulecode)
        self.add_rules(
            forward_declaration_rules=KContacts.forward_declaration_rules,
            function_rules=KContacts.function_rules)
        self.add_rules(
            parameter_rules=KCrash.parameter_rules)
        self.add_rules(
            forward_declaration_rules=KF5KDEGames.forward_declaration_rules,
            container_rules=KF5KDEGames.container_rules,
            function_rules=KF5KDEGames.function_rules,
            parameter_rules=KF5KDEGames.parameter_rules,
            modulecode=KF5KDEGames.modulecode)
        self.add_rules(
            modulecode=KGeoMap.modulecode)
        self.add_rules(
            container_rules=KIOCore.container_rules,
            function_rules=KIOCore.function_rules,
            typedef_rules=KIOCore.typedef_rules,
            modulecode=KIOCore.modulecode,
            typecode=KIOCore.typecode)
        self.add_rules(
            variable_rules=kio.variable_rules)
        self.add_rules(
            container_rules=KI18n.container_rules,
            function_rules=KI18n.function_rules)
        self.add_rules(
            modulecode=KJobWidgets.modulecode,
            typecode=KJobWidgets.typecode)
        self.add_rules(
            function_rules=KLDAP.function_rules,
            parameter_rules=KLDAP.parameter_rules,
            variable_rules=KLDAP.variable_rules,
            typedef_rules=KLDAP.typedef_rules)
        self.add_rules(
            parameter_rules=KMime.parameter_rules,
            modulecode=KMime.modulecode)
        self.add_rules(
            forward_declaration_rules=KNotifyConfig.forward_declaration_rules)
        self.add_rules(
            function_rules=KNotifications.function_rules,
            modulecode=KNotifications.modulecode)
        self.add_rules(
            container_rules=KService.container_rules,
            function_rules=KService.function_rules,
            typedef_rules=KService.typedef_rules,
            typecode = KService.typecode,
            modulecode=KService.modulecode)
        self.add_rules(
            function_rules=KStyle.function_rules)
        self.add_rules(
            function_rules=KUnitConversion.function_rules)
        self.add_rules(
            forward_declaration_rules=KWidgetsAddons.forward_declaration_rules,
            function_rules=KWidgetsAddons.function_rules,
            parameter_rules=KWidgetsAddons.parameter_rules,
            modulecode=KWidgetsAddons.modulecode,
            typecode=KWidgetsAddons.typecode)
        self.add_rules(
            function_rules=KXmlGui.function_rules,
            parameter_rules=KXmlGui.parameter_rules,
            modulecode=KXmlGui.modulecode,
            methodcode=KXmlGui.methodcode)
        self.add_rules(
            typedef_rules=MessageCore.typedef_rules)
        self.add_rules(
            function_rules=Sonnet.function_rules,
            modulecode = Sonnet.modulecode)
        self.add_rules(
            function_rules=Syndication.function_rules,
            typedef_rules=Syndication.typedef_rules,
            modulecode=Syndication.modulecode)

