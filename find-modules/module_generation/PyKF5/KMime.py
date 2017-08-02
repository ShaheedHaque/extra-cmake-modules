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
import rule_helpers


def _delete_duplicate_content(filename, sip, entry):
    if sip["name"] == "KMimeMessage":
        sip["decl"] = ""


def parameter_in_out(container, function, parameter, sip, matcher):
    rule_helpers.parameter_out(container, function, parameter, sip, matcher)
    rule_helpers.parameter_in(container, function, parameter, sip, matcher)


def parameter_out(container, function, parameter, sip, matcher):
    rule_helpers.parameter_out(container, function, parameter, sip, matcher)
    if sip["decl"].startswith("QPair"):
        PyQt_templates.pair_parameter(container, function, parameter, sip, matcher)
    elif sip["decl"].startswith("QVector"):
        PyQt_templates.list_parameter(container, function, parameter, sip, matcher)
    elif sip["decl"].startswith("QMap"):
        PyQt_templates.dict_parameter(container, function, parameter, sip, matcher)


def parameter_fully_qualify(container, function, parameter, sip, matcher):
    sip["init"] = sip["init"].replace("<", "<KMime::MDN::")


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    if sip["name"] == "KMime.KMime":
        rule_helpers.modulecode_delete(filename, sip, rule, "QMap<QString, QString>", "QVector<QByteArray>")
        rule_helpers.module_add_classes(filename, sip, rule, "KConfigGroup", "KCoreConfigSkeleton",
                                        "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate")
    elif sip["name"] == "Akonadi.KMime":
        rule_helpers.modulecode_delete(filename, sip, rule, "QVector<Akonadi::Collection>", "QVector<Akonadi::Item>",
                                       "QSet<QByteArray>")
        rule_helpers.module_add_classes(filename, sip, rule, "Akonadi::SpecialMailCollectionsPrivate",
                                        "KLocalizedString", "Akonadi::Protocol::Command",
                                        "Akonadi::ServerManagerPrivate")
        rule_helpers.module_add_imports(filename, sip, rule, "KMime/KMime/KMimemod.sip")
        rule_helpers.module_add_includes(filename, sip, rule, "<akonadi/private/protocol_p.h>")


def container_rules():
    return [
        #
        # Duplicate Akonadi::SuperClass.
        #
        ["kmime_newsarticle.h", "Akonadi", ".*", ".*", ".*", rule_helpers.container_discard],
        ["Akonadi", "MessageFolderAttribute", ".*", ".*", ".*", rule_helpers.container_make_unassignable],
    ]


def parameter_rules():
    return [
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
