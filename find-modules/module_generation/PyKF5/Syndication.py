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


def _function_fixup_template_params(container, function, sip, matcher):
    sip["parameters"][-1] = sip["parameters"][-1].replace("type-parameter-0-0", "T", 1)


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
        PyQt_templates.qshareddatapointer_typecode(container, typedef, sip, matcher)


def function_rules():
    return [
        ["Syndication.*", "operator QString", ".*", ".*", ".*", rule_helpers.function_discard],
        ["Syndication::ParserCollection", "registerParser|changeMapper", ".*", ".*", ".*", _function_fixup_template_params],
        #
        # Provide %MethodCode and a C++ signature.
        #
        ["Syndication", "parserCollection", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Broken C++, missing ">"!!!
        #
        #["Syndication::RSS2::Item", "Item", ".*", ".*", ".*doc.*", rule_helpers.function_discard],
    ]


def typedef_rules():
    return [
        ["Syndication.*", ".*Ptr", ".*", "QSharedPointer<Syndication::.*>", typedef_duplicate_discard],
    ]


def modulecode():
    return {
        "Syndicationmod.sip": {
            "code":
                """
                class KIO::Job /External/;
                class KJob /External/;
                %Import(name=QtXml/QtXmlmod.sip)
                class Syndication::Atom::EntryDocument /External/;
                class Syndication::Atom::FeedDocument /External/;
                class Syndication::Atom::Entry /External/;
                class Syndication::RDF::Document /External/;
                class Syndication::RDF::Item /External/;
                class Syndication::RSS2::Document /External/;
                class Syndication::RSS2::Item /External/;
                """
        },
    }
