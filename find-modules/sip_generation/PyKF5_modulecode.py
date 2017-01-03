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
SIP binding custom module-related code for PyKF5.
"""

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


#
# Main dictionary.
#
# When using sip_bulk_generator.py, it is important to use the name of any forwardee header in
# the key, since that is the file we actually use.
#
code = {
    "kcoreconfigskeleton.h": {
        "code": _kcoreconfigskeleton_item_add_py_subclass
    },
}
