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


def _delete_duplicate_content(filename, sip, entry):
    if sip["name"] == "KMimeMessage":
        sip["decl"] = ""


def parameter_rewrite_quotes(container, function, parameter, sip, matcher):
    sip["init"] = "'.'"


def parameter_fully_qualify(container, function, parameter, sip, matcher):
    sip["init"] = sip["init"].replace("<", "<KMime::MDN::")


def parameter_rules():
    return [
        #
        # Temporarily rewrite quote to workaround SIP 4.18.1 bug.
        # https://www.riverbankcomputing.com/pipermail/pyqt/2017-March/038989.html
        #
        ["KMime::HeaderParsing", "parseGenericQuotedString", "(open|close)Char", ".*", ".*", parameter_rewrite_quotes],
        #
        # Fully-qualify default values.
        #
        ["KMime::MDN", ".*", ".*", ".*", ".*<DispositionModifier>.*", parameter_fully_qualify],
    ]


def modulecode():
    return {
        "kmime_message.h": {
            "code": _delete_duplicate_content
        },
    }
