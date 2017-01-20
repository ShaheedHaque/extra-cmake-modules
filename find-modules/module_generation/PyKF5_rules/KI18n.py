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
SIP binding customisation for PyKF5.KI18n. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rules_engine


def container_rules():
    return [
        #
        # Remove some useless stuff.
        #
        ["klocalizedstring.h", "I18nTypeCheck", ".*", ".*", ".*", rules_engine.container_discard],
    ]


def function_rules():
    return [
        ["Kuit", "setupForDomain", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # Needs %MethodCode?
        #
        ["KuitSetup", "setTagPattern", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # SIP thinks there are duplicate signatures.
        #
        ["KLocalizedString", "subs", ".*", ".*", "(?!long long).*", rules_engine.function_discard],
    ]
