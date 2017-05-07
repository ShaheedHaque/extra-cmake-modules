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
SIP binding customisation for PyKF5.KItemViews. This modules describes:

    * Supplementary SIP file generator rules.
"""

import builtin_rules
import PyQt_templates


class FunctionWithTemplatesExpander(builtin_rules.FunctionWithTemplatesExpander):
    """
    Override the use of the protected enum 'QAbstractItemView::CursorAction'.
    """
    def analyse_function(self, fn, cursor, sip):
        entries = super(FunctionWithTemplatesExpander, self).analyse_function(fn, cursor, sip)
        assert entries["parameters"][0].cxx_t == "QAbstractItemView::CursorAction"
        entries["parameters"][0] = PyQt_templates.FunctionParameterHelper("int", None)
        entries["p_types"][0] = "int"
        return entries


def function_uses_templates(container, function, sip, matcher):
    sip.setdefault("template", FunctionWithTemplatesExpander)
    PyQt_templates.function_uses_templates(container, function, sip, matcher)


def function_rules():
    return [
        #
        # Rewrite using declaration.
        #
        ["KCategorizedView", "moveCursor", ".*", ".*", ".*", function_uses_templates],
    ]

