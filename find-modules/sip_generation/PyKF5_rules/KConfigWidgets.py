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
SIP binding customisation for PyKF5.KConfigWidgets. This modules describes:

    * Supplementary SIP file generator rules.
"""


def noop(*args):
    pass


def _delete_duplicate_content(filename, sip, entry):
    if "is_duplicate" not in entry:
        entry["is_duplicate"] = True
    else:
        sip["decl"] = ""


def parameter_rules():
    return [
        #
        # Override the default "parent" rule.
        #
        ["KStandardAction", ".*", "parent", ".*", ".*", noop]
    ]


def modulecode():
    return {
        "ktipdialog.h": {
            "code": _delete_duplicate_content
        },
    }
