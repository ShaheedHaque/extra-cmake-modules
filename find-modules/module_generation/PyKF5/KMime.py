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
SIP binding customisation for PyKF5.KMime. This modules describes:

    * Supplementary SIP file generator rules.
"""

import PyQt_templates
import rules_engine


def _delete_duplicate_content(filename, sip, entry):
    if sip["name"] == "KMimeMessage":
        sip["decl"] = ""


def parameter_in_out(container, function, parameter, sip, matcher):
    rules_engine.parameter_out(container, function, parameter, sip, matcher)
    rules_engine.parameter_in(container, function, parameter, sip, matcher)


def parameter_out(container, function, parameter, sip, matcher):
    rules_engine.parameter_out(container, function, parameter, sip, matcher)
    if sip["decl"].startswith("QPair"):
        PyQt_templates.qpair_parameter(container, function, parameter, sip, matcher)
    elif sip["decl"].startswith("QVector"):
        PyQt_templates.list_parameter(container, function, parameter, sip, matcher)
    elif sip["decl"].startswith("QMap"):
        PyQt_templates.dict_parameter(container, function, parameter, sip, matcher)


def parameter_rewrite_quotes(container, function, parameter, sip, matcher):
    sip["init"] = "'.'"


def parameter_fully_qualify(container, function, parameter, sip, matcher):
    sip["init"] = sip["init"].replace("<", "<KMime::MDN::")


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    if sip["name"] == "KMime.KMime":
        rules_engine.modulecode_delete(filename, sip, entry, "QMap<QString, QString>", "QVector<QByteArray>")
        sip["code"] = """
%If (!KMime_KMime_KMimemod)
class KConfigGroup /*External */;
class KCoreConfigSkeleton /*External */;
%End
"""
    elif sip["name"] == "Akonadi.KMime":
        rules_engine.modulecode_delete(filename, sip, entry, "QVector<Akonadi::Collection>", "QVector<Akonadi::Item>",
                                       "QSet<QByteArray>")
        sip["code"] = """
%If (!Akonadi_KMime_KMimemod)
class KMime::Message /*External */;
%End
"""


def container_rules():
    return [
        #
        # Duplicate Akonadi::SuperClass.
        #
        ["kmime_newsarticle.h", "Akonadi", ".*", ".*", ".*", rules_engine.container_discard],
    ]


def parameter_rules():
    return [
        #
        # Temporarily rewrite quote to workaround SIP 4.18.1 bug.
        # https://www.riverbankcomputing.com/pipermail/pyqt/2017-March/038989.html
        #
        ["KMime::HeaderParsing", "parseGenericQuotedString", "(open|close)Char", ".*", ".*", parameter_rewrite_quotes],
        ["KMime::HeaderParsing", "parse.*", "scursor", ".*", ".*", parameter_in_out],
        ["KMime::HeaderParsing", "parse.*", "result", ".*", ".*", parameter_out],
        #
        # Fully-qualify default values.
        #
        ["KMime::MDN", ".*", ".*", ".*", ".*<DispositionModifier>.*", parameter_fully_qualify],
    ]


def modulecode():
    return {
        "kmime_message.h": {
            "code": _delete_duplicate_content
        },
        "KMimemod.sip": {
            "code": module_fix_mapped_types
        },
    }
