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

from copy import deepcopy
import os

import rules_engine


def duplicate_typedef_discard(container, typedef, sip, matcher):
    """
    There are multiple definitions like this:

        typedef QSharedPointer<Syndication::Category> CategoryPtr;

    We need to get rid of each copy not in the canonical file.
    """
    pointer = os.path.basename(container.translation_unit.spelling)
    pointer = os.path.splitext(pointer)[0]
    pointer = pointer.capitalize() + "Ptr"
    if pointer != typedef.spelling:
        sip["name"] = ""


def function_rules():
    return [
        ["Syndication.*", "operator QString", ".*", ".*", ".*", rules_engine.function_discard],
    ]


def typedef_rules():
    return [
        ["Syndication.*", ".*Ptr", ".*", "QSharedPointer<Syndication::.*>", duplicate_typedef_discard],
    ]
