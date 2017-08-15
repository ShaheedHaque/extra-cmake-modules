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
import rule_helpers
from templates import PyQt


def _delete_duplicate_content(filename, sip, entry):
    sip["decl"] = ""


def parameter_in_out(container, function, parameter, sip, matcher):
    rule_helpers.parameter_out(container, function, parameter, sip, matcher)
    rule_helpers.parameter_in(container, function, parameter, sip, matcher)


def parameter_out(container, function, parameter, sip, matcher):
    rule_helpers.parameter_out(container, function, parameter, sip, matcher)
    if sip["decl"].startswith("QPair"):
        PyQt.pair_parameter(container, function, parameter, sip, matcher)
    elif sip["decl"].startswith("QVector"):
        PyQt.list_parameter(container, function, parameter, sip, matcher)
    elif sip["decl"].startswith("QMap"):
        PyQt.dict_parameter(container, function, parameter, sip, matcher)


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QMap<QString, QString>", "QVector<QByteArray>")
    rule_helpers.module_add_classes(filename, sip, rule, "KConfigGroup", "KCoreConfigSkeleton",
                                    "Akonadi::Protocol::Command", "Akonadi::ServerManagerPrivate")


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
     ]


def modulecode():
    return {
        "KMime/KMime/KMimeMessage": {
            "code": _delete_duplicate_content
        },
        "KMime/KMime/KMimemod.sip": {
            "code": module_fix_mapped_types
        },
    }
