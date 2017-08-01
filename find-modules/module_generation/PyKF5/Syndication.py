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
SIP binding customisation for PyKF5.Syndication. This modules describes:

    * Supplementary SIP file generator rules.
"""

import os

import rule_helpers
import PyQt_templates


def param_fully_qualify_default(container, function, parameter, sip, matcher):
    sip["init"] = sip["init"].replace("Document", "Syndication::RSS2::Document", 1)


def typedef_duplicate_discard(container, typedef, sip, matcher):
    """
    There are multiple definitions like this:

        typedef QSharedPointer<Syndication::Category> CategoryPtr;

    We need to get rid of each copy not in the canonical file.
    """
    pointer = os.path.basename(container.translation_unit.spelling)
    pointer = os.path.splitext(pointer)[0]
    pointer = pointer.capitalize() + "Ptr"
    if pointer != typedef.spelling:
        rule_helpers.typedef_discard(container, typedef, sip, matcher)
    else:
        #
        # This is the one we want. Keep it, and generate its %MappedType.
        #
        PyQt_templates.pointer_typecode(container, typedef, sip, matcher)



def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QSharedPointer<T>")
    rule_helpers.module_add_imports(filename, sip, entry, "QtXml/QtXmlmod.sip", "Rss2/Rss2mod.sip", "Rdf/Rdfmod.sip",
                                    "Atom/Atommod.sip")


def module_fix_mapped_types_atom(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<QDomElement>",
                                   "QSharedPointer<Syndication::SpecificDocument>")
    rule_helpers.module_add_imports(filename, sip, entry, "QtXml/QtXmlmod.sip", "../Rss2/Rss2mod.sip",
                                    "../Rdf/Rdfmod.sip")


def module_fix_mapped_types_rdf(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QSharedPointer<Syndication::SpecificDocument>")
    rule_helpers.module_add_imports(filename, sip, entry, "QtXml/QtXmlmod.sip", "../Rss2/Rss2mod.sip",
                                    "../Atom/Atommod.sip")


def module_fix_mapped_types_rss2(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<QDomElement>",
                                   "QSharedPointer<Syndication::SpecificDocument>")
    rule_helpers.module_add_imports(filename, sip, entry, "QtXml/QtXmlmod.sip", "../Rdf/Rdfmod.sip",
                                    "../Atom/Atommod.sip")


def function_rules():
    return [
        ["Syndication.*", "operator QString", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Provide %MethodCode and a C++ signature.
        #
        ["Syndication", "parserCollection", ".*", ".*", ".*", rule_helpers.function_discard],
    ]


def parameter_rules():
    return [
        ["Syndication::RSS2::Item", "Item", "doc", ".*", ".*", param_fully_qualify_default],
    ]


def typedef_rules():
    return [
        ["Syndication.*", ".*Ptr", ".*", "QSharedPointer<Syndication::.*>", typedef_duplicate_discard],
    ]


def modulecode():
    return {
        "Atommod.sip": {
            "code": module_fix_mapped_types_atom,
        },
        "Rdfmod.sip": {
            "code": module_fix_mapped_types_rdf,
        },
        "Rss2mod.sip": {
            "code": module_fix_mapped_types_rss2,
        },
        "Syndicationmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
