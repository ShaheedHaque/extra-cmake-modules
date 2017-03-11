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
SIP binding customisation for PyKF5.KCompletion. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rules_engine


def _container_delete_base(container, sip, matcher):
    sip["base_specifiers"] = []


def _function_rewrite_using_decl(container, function, sip, matcher):
    sip["parameters"] = ["int index", "const QStringList &texts"]


def parameter_rewrite_template(container, function, parameter, sip, matcher):
    if sip["name"] == "i":
        sip["decl"] = "Key i"
    elif sip["name"] == "t":
        sip["decl"] = "const T &t"
    else:
        assert False, "Unexpected parameter {}".format(sip["name"])


def container_rules():
    return [
        #
        # SIP cannot handle inline templates like "class Foo: Bar<Baz>" without an intermediate typedef. For now,
        # delete the base class.
        #
        ["kcompletionmatches.h", "KCompletionMatches", ".*", ".*", ".*", _container_delete_base],
        ["ksortablelist.h", "KSortableItem|KSortableList", ".*", ".*", ".*", _container_delete_base],
    ]


def function_rules():
    return [
        ["KCompletionBase", "keyBindingMap|getKeyBindings|setKeyBindingMap", ".*", ".*", ".*", rules_engine.function_discard],
        ["KCompletionMatches", "KCompletionMatches", ".*", ".*", ".*KCompletionMatchesWrapper.*", rules_engine.function_discard],
        #
        # Rewrite using declaration.
        #
        ["KHistoryComboBox", "insertItems", ".*", ".*", "", _function_rewrite_using_decl],
    ]


def parameter_rules():
    return [
        ["KSortableList", ".*", "i|t", ".*", ".*", parameter_rewrite_template],
    ]
