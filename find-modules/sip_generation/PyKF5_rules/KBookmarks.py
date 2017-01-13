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
SIP binding customisation for PyKF5.KBookmarks. This modules describes:

    * Supplementary SIP file generator rules.
"""


def _container_discard(container, sip, matcher):
    sip["name"] = ""


def _variable_void(container, variable, sip, matcher):
    sip["decl"] = "void *"


def container_rules():
    return [
        #
        # No multiple inheritance.
        #
        ["kbookmarkimporter.h", "KXBELBookmarkImporterImpl", ".*", ".*", ".*", _container_discard],
    ]


def variable_rules():
    return [
        ["KonqBookmarkMenu::DynMenuInfo", "d", ".*DynMenuInfoPrivate.*", _variable_void],
    ]


def modulecode():
    return {
        "KBookmarksmod.sip": {
            "code":
                """
                %Import(name=QtDBus/QtDBusmod.sip)
                %Import(name=KXmlGui/KXmlGuimod.sip)
                """
            },
    }


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kbookmarkowner.h::KBookmarkOwner": {
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'KBookmarkOwner'
                    sipType = NULL;

                    if (dynamic_cast<KonqBookmarkOwner*>(sipCpp))
                        sipType = sipType_KonqBookmarkOwner;
                %End
                """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kbookmarkexporter.h::KBookmarkExporterBase": {
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'KBookmarkExporterBase'
                    sipType = NULL;

                    if (dynamic_cast<KIEBookmarkExporterImpl*>(sipCpp))
                        sipType = sipType_KIEBookmarkExporterImpl;
                    else if (dynamic_cast<KNSBookmarkExporterImpl*>(sipCpp))
                        sipType = sipType_KNSBookmarkExporterImpl;
                    else if (dynamic_cast<KOperaBookmarkExporterImpl*>(sipCpp))
                        sipType = sipType_KOperaBookmarkExporterImpl;
                %End
                """
        },
    }
