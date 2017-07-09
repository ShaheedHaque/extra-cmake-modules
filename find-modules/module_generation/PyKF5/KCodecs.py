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
SIP binding customisation for PyKF5.KCodecs. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers

def _mark_abstract(container, sip, matcher):
    sip["annotations"].add("Abstract")


def container_rules():
    return [
        ["KCodecs", ".*", ".*", ".*", ".*", _mark_abstract],
    ]


def function_rules():
    return [
        ["KCodecs::Codec", "encode", ".*", ".*", ".*char.*&.*", rule_helpers.function_discard],
        ["KCodecs::Codec", "decode", ".*", ".*", ".*char.*&.*", rule_helpers.function_discard],

        ["KCodecs::Encoder", "encode", ".*", ".*", ".*char.*&.*", rule_helpers.function_discard],
        ["KCodecs::Encoder", "finish", ".*", ".*", ".*char.*&.*", rule_helpers.function_discard],
        ["KCodecs::Encoder", "write", ".*", ".*", ".*char.*&.*", rule_helpers.function_discard],
        ["KCodecs::Encoder", "writeCRLF", ".*", ".*", ".*char.*&.*", rule_helpers.function_discard],
        ["KCodecs::Encoder", "flushOutputBuffer", ".*", ".*", ".*char.*&.*", rule_helpers.function_discard],

        ["KCodecs::Decoder", "decode", ".*", ".*", ".*char.*&.*", rule_helpers.function_discard],
        ["KCodecs::Decoder", "finish", ".*", ".*", ".*char.*&.*", rule_helpers.function_discard],

        ["KCharsets", "codecForName", ".*", ".*", ".*name", rule_helpers.function_discard],
        ["KCharsets", "fromEntity", ".*", ".*", ".*str", rule_helpers.function_discard],
    ]
