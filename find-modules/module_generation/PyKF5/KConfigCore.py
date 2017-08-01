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
SIP binding customisation for PyKF5.KConfigCore. This modules describes:

    * Supplementary SIP file generator rules.
"""

from copy import deepcopy

import rule_helpers
import rules_engine


def _container_delete_base(container, sip, matcher):
    sip["base_specifiers"] = []


def _mark_abstract_and_discard_QSharedData(container, sip, matcher):
    rule_helpers.container_mark_abstract(container, sip, matcher)
    rule_helpers.container_discard_QSharedData_base(container, sip, matcher)


def _function_fixup_template_params(container, function, sip, matcher):
    sip["parameters"] = ["const T &v"]


def _function_rewrite_using_decl(container, function, sip, matcher):
    flags = "QFlags<KConfigBase::WriteConfigFlag> flags = KConfigBase::Normal"
    sip["parameters"] = ["const QByteArray & group", flags]
    sip["code"] = """    void deleteGroup(const QString &group, {});
    void deleteGroup(const char *group, {});
""".format(flags, flags)


def _discard_non_const_suffixes(container, function, sip, matcher):
    rule_helpers.function_discard(container, function, sip, matcher)


def parameter_add_brackets(container, function, parameter, sip, matcher):
    sip["init"] += "()"


def _kcoreconfigskeleton_add_item_xxx(function, sip, entry):
    sip["code"] = """
%MethodCode
        Py_BEGIN_ALLOW_THREADS
        sipRes = new PyItem{}(sipCpp->currentGroup(), a3->isNull() ? *a0 : *a3, a1, a2);
        sipCpp->addItem(sipRes, *a0);
        Py_END_ALLOW_THREADS
%End
""".format(sip["ctx"])


def _kcoreconfigskeleton_item_xxx(function, sip, entry):
    sip["cxx_parameters"] = deepcopy(sip["parameters"])
    sip["cxx_fn_result"] = ""
    sip["code"] = """
%MethodCode
        Py_BEGIN_ALLOW_THREADS
        sipCpp = (sipKCoreConfigSkeleton_Item{} *)(new KCoreConfigSkeleton::Item{}(*a0, *a1, a2, a3));
        Py_END_ALLOW_THREADS
%End
""".replace("{}", sip["ctx"])
    sip["parameters"][2] = sip["parameters"][2].replace("&", "")


def _kcoreconfigskeleton_item_enum(function, sip, entry):
    sip["cxx_parameters"] = deepcopy(sip["parameters"])
    sip["cxx_fn_result"] = ""
    sip["code"] = """
%MethodCode
        Py_BEGIN_ALLOW_THREADS
        sipCpp = (sipKCoreConfigSkeleton_Item{} *)(new KCoreConfigSkeleton::Item{}(*a0, *a1, a2, *a3, a4));
        Py_END_ALLOW_THREADS
%End
""".replace("{}", sip["ctx"])
    sip["parameters"][2] = sip["parameters"][2].replace("&", "")


def _kcoreconfigskeleton_item_add_py_subclass(filename, sip, entry):
    result = """
%ModuleHeaderCode
#include <kcoreconfigskeleton.h>
"""
    for ctx in ({"Type": "Bool", "cpptype": "bool", "defaultValue": 1},
                {"Type": "Int", "cpptype": "qint32", "defaultValue": 1},
                {"Type": "UInt", "cpptype": "quint32", "defaultValue": 1},
                {"Type": "LongLong", "cpptype": "qint64", "defaultValue": 1},
                {"Type": "ULongLong", "cpptype": "quint64", "defaultValue": 1},
                {"Type": "Double", "cpptype": "double", "defaultValue": 1},
        ):
        result += """
class PyItem{Type} : public KCoreConfigSkeleton::Item{Type}
{{
public:
    PyItem{Type} (const QString &group, const QString &key, {cpptype}& val, {cpptype} defaultValue = {defaultValue}) :
        KCoreConfigSkeleton::Item{Type} (group, key, this->value, defaultValue),
        value(val)
    {{
    }}

private:
    {cpptype} value;
}};
""".format(**ctx)

    result += """
class PyItemEnum : public KCoreConfigSkeleton::ItemEnum
{
public:
    PyItemEnum (const QString& group, const QString& key, int& val, const QList<KCoreConfigSkeleton::ItemEnum::Choice>& choices, int defaultValue = 0) :
        KCoreConfigSkeleton::ItemEnum(group, key, this->value, choices, defaultValue),
        value(val)
    {
    };

private:
    int value;
};
%End\n
"""
    sip["code"] = result


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_make_local(filename, sip, entry, "QExplicitlySharedDataPointer<KSharedConfig>",
                                       "QList<QUrl>", "QList<QVariant>")
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<int>", "QList<T>", "QMap<QString, QString>")


def container_rules():
    return [
        ["kconfigbackend.h", "KConfigBackend", ".*", ".*", ".*", _mark_abstract_and_discard_QSharedData],
        ["kconfigbase.h", "KConfigBase", ".*", ".*", ".*", rule_helpers.container_mark_abstract],
        ["ksharedconfig.h", "KSharedConfig", ".*", ".*", ".*QSharedData.*", rule_helpers.container_discard_QSharedData_base],
        #
        # Emit templated containers.
        #
        ["kcoreconfigskeleton.h", "KConfigSkeletonGenericItem", ".*", ".*", ".*", rule_helpers.noop],
        #
        # SIP cannot handle inline templates like "class Foo: Bar<Baz>" without an intermediate typedef. For now,
        # delete the base class.
        #
        ["KCoreConfigSkeleton", "Item.*", ".*", ".*", ".*", _container_delete_base],
    ]


def function_rules():
    return [
        ["KCoreConfigSkeleton|KConfig.*|KDesktopFile|KSharedConfig", "groupImpl|group|config|actionGroup", ".*", ".*", ".*", ".*", "(?! const).*", _discard_non_const_suffixes],
        ["KConfigGroup", "KConfigGroup", ".*", ".*", "KConfigBase.*", ".*", "(?! const)", _discard_non_const_suffixes],
        ["KConfigSkeletonGenericItem", "value", ".*", ".*", ".*", "inline ", "", rule_helpers.function_discard],
        ["KConfigSkeletonGenericItem", "setValue|setDefaultValue", ".*", ".*", ".*", _function_fixup_template_params],
        #
        # What *is* KEntryMap?
        #
        ["KConfigBackend", ".*", ".*", ".*", ".*KEntryMap.*", rule_helpers.function_discard],
        ["KConfigBackend", "create", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Rewrite using declaration.
        #
        ["KConfigGroup", "deleteGroup", ".*", ".*", "", _function_rewrite_using_decl],
    ]


def typedef_rules():
    return [
        #
        # It is not clear how to represent "typedef QHash < QString, KConfigSkeletonItem * >::Iterator DictIterator;"
        # in SIP. Discard it.
        #
        ["KConfigSkeletonItem", "DictIterator", ".*", ".*", rule_helpers.typedef_discard],
    ]


def modulecode():
    return {
        "KConfigCoremod.sip": {
            "code": module_fix_mapped_types,
        },
        "kconfig.h": {
            "code":
                """
                %ModuleHeaderCode
                #include <KConfigCore/KDesktopFile>
                %End
                """
        },
        "kcoreconfigskeleton.h": {
            "code": _kcoreconfigskeleton_item_add_py_subclass
        },
    }


def methodcode():
    return {
        "KCoreConfigSkeleton":
        {
            "addItemBool":
            {
                "code": _kcoreconfigskeleton_add_item_xxx,
                "ctx": "Bool",
            },
            "addItemInt":
            {
                "code": _kcoreconfigskeleton_add_item_xxx,
                "ctx": "Int",
            },
            "addItemUInt":
            {
                "code": _kcoreconfigskeleton_add_item_xxx,
                "ctx": "UInt",
            },
            "addItemLongLong":
            {
                "code": _kcoreconfigskeleton_add_item_xxx,
                "ctx": "LongLong",
            },
            "addItemInt64":
            {
                "code": _kcoreconfigskeleton_add_item_xxx,
                "ctx": "LongLong",
            },
            "addItemULongLong":
            {
                "code": _kcoreconfigskeleton_add_item_xxx,
                "ctx": "ULongLong",
            },
            "addItemUInt64":
            {
                "code": _kcoreconfigskeleton_add_item_xxx,
                "ctx": "ULongLong",
            },
            "addItemDouble":
            {
                "code": _kcoreconfigskeleton_add_item_xxx,
                "ctx": "Double",
            },
        },
        "KCoreConfigSkeleton::ItemBool":
        {
            "ItemBool":
            {
                "code": _kcoreconfigskeleton_item_xxx,
                "ctx": "Bool",
            },
        },
        "KCoreConfigSkeleton::ItemInt":
        {
            "ItemInt":
            {
                "code": _kcoreconfigskeleton_item_xxx,
                "ctx": "Int",
            },
        },
        "KCoreConfigSkeleton::ItemLongLong":
        {
            "ItemLongLong":
            {
                "code": _kcoreconfigskeleton_item_xxx,
                "ctx": "LongLong",
            },
        },
        "KCoreConfigSkeleton::ItemEnum":
        {
            "ItemEnum":
            {
                "code": _kcoreconfigskeleton_item_enum,
                "ctx": "Enum",
            },
        },
        "KCoreConfigSkeleton::ItemUInt":
        {
            "ItemUInt":
            {
                "code": _kcoreconfigskeleton_item_xxx,
                "ctx": "UInt",
            },
        },
        "KCoreConfigSkeleton::ItemULongLong":
        {
            "ItemULongLong":
            {
                "code": _kcoreconfigskeleton_item_xxx,
                "ctx": "ULongLong",
            },
        },
        "KCoreConfigSkeleton::ItemDouble":
        {
            "ItemDouble":
            {
                "code": _kcoreconfigskeleton_item_xxx,
                "ctx": "Double",
            },
        },
    }


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kcoreconfigskeleton.h::KCoreConfigSkeleton": {
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'KConfigSkeletonItem'
                    sipType = NULL;

                    if (dynamic_cast<KCoreConfigSkeleton::ItemBool*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemBool;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemDateTime*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemDateTime;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemDouble*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemDouble;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemInt*>(sipCpp))
                        {
                        sipType = sipType_KCoreConfigSkeleton_ItemInt;
                        if (dynamic_cast<KCoreConfigSkeleton::ItemEnum*>(sipCpp))
                            sipType = sipType_KCoreConfigSkeleton_ItemEnum;
                        }
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemIntList*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemIntList;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemLongLong*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemLongLong;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemPoint*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemPoint;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemProperty*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemProperty;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemRect*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemRect;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemSize*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemSize;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemString*>(sipCpp))
                        {
                        sipType = sipType_KCoreConfigSkeleton_ItemString;
                        if (dynamic_cast<KCoreConfigSkeleton::ItemPassword*>(sipCpp))
                            sipType = sipType_KCoreConfigSkeleton_ItemPassword;
                        else if (dynamic_cast<KCoreConfigSkeleton::ItemPath*>(sipCpp))
                            sipType = sipType_KCoreConfigSkeleton_ItemPath;
                        }
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemStringList*>(sipCpp))
                        {
                        sipType = sipType_KCoreConfigSkeleton_ItemStringList;
                        if (dynamic_cast<KCoreConfigSkeleton::ItemPathList*>(sipCpp))
                            sipType = sipType_KCoreConfigSkeleton_ItemPathList;
                        }
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemUInt*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemUInt;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemULongLong*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemULongLong;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemUrl*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemUrl;
                    else if (dynamic_cast<KCoreConfigSkeleton::ItemUrlList*>(sipCpp))
                        sipType = sipType_KCoreConfigSkeleton_ItemUrlList;
                %End
                """
            },
        }
