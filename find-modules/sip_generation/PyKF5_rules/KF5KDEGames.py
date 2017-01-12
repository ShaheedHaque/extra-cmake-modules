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
SIP binding customisation for PyKF5.KF5KDEGames. This modules describes:

    * Supplementary SIP file generator rules.
"""


def strip_redundant_import(filename, sip, matcher):
    lines = []
    for l in sip["decl"].split("\n"):
        if "KF5KDEGames/KF5KDEGamesmod.sip" in l:
            l = "// " + l
        lines.append(l)
    sip["decl"] = "\n".join(lines)


def discard_union(container, sip, matcher):
    sip["name"] = ""


def _function_discard_class(container, function, sip, matcher):
    sip["fn_result"] = sip["fn_result"].replace("class ", "")


def container_rules():
    return [
        ["KGamePropertyBase", "Flags", ".*", ".*", ".*", discard_union],
    ]


def function_rules():
    return [
        ["KGameCanvasAbstract|KGameCanvasAdapter", "topLevelCanvas", ".*", ".*", ".*", _function_discard_class],
    ]


def modulecode():
    return {
        "KDEmod.sip": {
            "code": strip_redundant_import
        }
    }
