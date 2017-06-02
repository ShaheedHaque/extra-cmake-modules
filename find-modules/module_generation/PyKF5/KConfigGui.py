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
SIP binding customisation for PyKF5.KConfigGui. This modules describes:

    * Supplementary SIP file generator rules.
"""


def _container_delete_base(container, sip, matcher):
    sip["base_specifiers"] = []


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    # Putting knowledge here of any %Import'ers who happen not to have
    # duplicates is horrid, but much less painful than the alternative.
    #
    duplicated = "QExplicitlySharedDataPointer<KSharedConfig>"
    tmp = sip["modulecode"][duplicated]
    tmp = "%If (!KConfigGui_KConfigGuimod)\n" + tmp + "%End\n"
    sip["modulecode"][duplicated] = tmp


def container_rules():
    return [
        #
        # SIP cannot handle inline templates like "class Foo: Bar<Baz>" without an intermediate typedef. For now,
        # delete the base class.
        #
        ["KConfigSkeleton", "ItemColor|ItemFont", ".*", ".*", ".*", _container_delete_base],
    ]


def modulecode():
    return {
        "KConfigGuimod.sip": {
            "code": module_fix_mapped_types,
        },
        "kconfigskeleton.h": {
            "code":
                """
                %ModuleHeaderCode
                #include <KConfigGui/KConfigSkeleton>
                %End
                """
        },
    }
