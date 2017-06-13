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
SIP binding customisation for PyKF5.KParts. This modules describes:

    * Supplementary SIP file generator rules.
"""

from clang.cindex import CursorKind

import rules_engine


def _function_rewrite_using_decl(container, function, sip, matcher):
    if function.kind == CursorKind.USING_DECLARATION:
        sip["parameters"] = ["QObject *parent /TransferThis/",
                             "KXMLGUIClient *parentGUIClient",
                             "const KAboutData &aboutData"]


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    if sip["name"] == "KParts.KParts":
        rules_engine.modulecode_delete(filename, sip, entry, "QExplicitlySharedDataPointer<KService>")
        rules_engine.modulecode_make_local(filename, sip, entry, "QList<QUrl>", "QMap<QString, QString>")
        sip["code"] = """
%If (!KParts_KParts_KPartsmod)
class KIconLoader /External/;
class KXmlGuiWindow /External/;
class KSslCertificateBoxPrivate;
%End
%Import(name=SonnetCore/Sonnet/Sonnetmod.sip)
"""

def function_rules():
    return [
        #
        # SIP unsupported signal argument type.
        #
        ["KParts::BrowserExtension", "createNewWindow", ".*", ".*", ".*", rules_engine.function_discard],
        ["KParts::ReadWritePart", "sigQueryClose", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # SIP overloaded functions with the same Python signature.
        #
        ["KParts::OpenUrlArguments", "metaData", ".*", ".*", ".*", ".*", "(?! const)", rules_engine.function_discard],
        #
        # Rewrite using declaration.
        #
        ["KParts::Part", "loadPlugins", ".*", ".*", "", _function_rewrite_using_decl],
    ]


def modulecode():
    return {
        #
        # NOTE: there are two files with the same name!
        #
        "KPartsmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
