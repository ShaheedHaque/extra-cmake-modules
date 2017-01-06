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

import os
import sys

import rules_engine

from copy import deepcopy


def _discard_QSharedData(container, sip, matcher):
    sip["base_specifiers"] = sip["base_specifiers"].replace(", QSharedData", "")


def _mark_abstract(container, sip, matcher):
    sip["annotations"].add("Abstract")


def _mark_abstract_and_discard_QSharedData(container, sip, matcher):
    _mark_abstract(container, sip, matcher)
    _discard_QSharedData(container, sip, matcher)


def set_skeleton_item_base(container, sip, matcher):
    if not sip["base_specifiers"] or sip["base_specifiers"].endswith(">"):
        sip["base_specifiers"] = "KConfigSkeletonItem"


def _discard_non_const_suffixes(container, function, sip, matcher):
    if "const" not in sip["suffix"]:
        rules_engine.function_discard(container, function, sip, matcher)


def _kcoreconfigskeleton_add_item_xxx(function, sip, entry):
    sip["code"] = """
%MethodCode
        Py_BEGIN_ALLOW_THREADS
        sipRes = new PyItem{}(sipCpp->currentGroup(), a3->isNull() ? *a0 : *a3, a1, a2);
        sipCpp->addItem(sipRes, *a0);
        Py_END_ALLOW_THREADS
%End
""".format(entry["ctx"])


def _kcoreconfigskeleton_item_xxx(function, sip, entry):
    sip["decl2"] = deepcopy(sip["parameters"])
    sip["fn_result2"] = ""
    sip["code"] = """
%MethodCode
        Py_BEGIN_ALLOW_THREADS
        sipCpp = new KCoreConfigSkeleton::Item{}(*a0, *a1, a2, a3);
        Py_END_ALLOW_THREADS
%End
""".replace("{}", entry["ctx"])
    sip["parameters"][2] = sip["parameters"][2].replace("&", "")


def _kcoreconfigskeleton_item_enum(function, sip, entry):
    sip["decl2"] = deepcopy(sip["parameters"])
    sip["fn_result2"] = ""
    sip["code"] = """
%MethodCode
        Py_BEGIN_ALLOW_THREADS
        sipCpp = new KCoreConfigSkeleton::ItemEnum(*a0, *a1, a2, *a3, a4);
        Py_END_ALLOW_THREADS
%End
""".replace("{}", entry["ctx"])
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


def container_rules():
    return [
        ["kconfigbackend.h", "KConfigBackend", ".*", ".*", ".*", _mark_abstract_and_discard_QSharedData],
        ["kconfigbase.h", "KConfigBase", ".*", ".*", ".*", _mark_abstract],

        [".*KCoreConfigSkeleton.*", ".*Item.*", ".*", ".*", ".*", set_skeleton_item_base],
        ["ksharedconfig.h", "KSharedConfig", ".*", ".*", ".*QSharedData.*", _discard_QSharedData],
    ]


def function_rules():
    return [
        ["KCoreConfigSkeleton|KConfig.*|KDesktopFile", "groupImpl|group|config|actionGroup", ".*", ".*", ".*", _discard_non_const_suffixes],
        ["KConfigGroup", "KConfigGroup", ".*", ".*", "KConfigBase.*", _discard_non_const_suffixes],
        #
        # What *is* KEntryMap?
        #
        ["KConfigBackend", ".*", ".*", ".*", ".*KEntryMap.*", rules_engine.function_discard],
        ["KConfigBackend", "create", ".*", ".*", ".*", rules_engine.function_discard],
    ]


def modulecode():
    return {
        "kconfig.h": {
            "code":
                """
                %ModuleHeaderCode
                #include <KConfigCore/KDesktopFile>
                %End
                """
        },
        "kconfiggroup.h": {
            "code":
                """
                %MappedType QExplicitlySharedDataPointer<KSharedConfig>
                {
                %ConvertFromTypeCode
                    // Put something here
                    int foo = 1;
                %End
                %ConvertToTypeCode
                    int foo = 1;
                %End
                };
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
        "kcoreconfigskeleton.h::KCoreConfigSkeleton":
        {
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
