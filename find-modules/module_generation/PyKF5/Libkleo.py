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
SIP binding customisation for PyKF5.Libkleo. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def module_fix_mapped_types(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, rule, "QList<QUrl>", "QMap<QString, QVariant>",
                                   "std::vector<GpgME::Key, std::allocator<GpgME::Key> >",
                                   "std::vector<const char *, std::allocator<const char *> >",
                                   "std::vector<int, std::allocator<int> >",
                                   "std::vector<unsigned int, std::allocator<unsigned int> >",
                                   "std::vector<GpgME::Key, std::allocator<GpgME::Key> >")
    rule_helpers.module_add_classes(filename, sip, rule, "KConfig", "_IO_FILE", "Kleo::DownloadJob",
                                    "Kleo::RefreshKeysJob")


def container_rules():
    return [
        #
        # We cannot handle templated containers which are this complicated.
        #
        ["Kleo::_detail", "ByFingerprint|ByKeyID|ByShortKeyID|ByChainID", ".*", ".*", ".*", rule_helpers.container_discard],
        ["kdtools", "select1st|select2nd", ".*", ".*", ".*", rule_helpers.container_discard],
        ["Kleo::KeyApprovalDialog", "Item", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]


def modulecode():
    return {
        "Libkleo/CryptoBackend": {
            "code": rule_helpers.module_yank_scoped_class,
            "ctx": {"child": "Protocol", "parent": "CryptoBackend"},
        },
        "Libkleo/Dn": {
            "code": rule_helpers.module_yank_scoped_class,
            "ctx": {"child": "Attribute", "parent": "DN"},
        },
        "Libkleo/Libkleomod.sip": {
            "code": module_fix_mapped_types,
        },
    }
