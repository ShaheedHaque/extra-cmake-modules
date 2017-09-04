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
SIP binding customisation for PyKF5.Kross. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def container_fixup(container, sip, rule):
    rule_helpers.container_discard_QSharedData_base(container, sip, rule)
    rule_helpers.container_make_unassignable(container, sip, rule)


def module_fix_mapped_types_core(filename, sip, rule):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_make_local(filename, sip, rule, "QList<QVariant>", "QMap<QString, QVariant>")
    rule_helpers.module_add_imports(filename, sip, rule, "SonnetCore/Sonnet/Sonnetmod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "QScriptable")


def module_fix_mapped_types_ui(filename, sip, rule):
    rule_helpers.module_add_imports(filename, sip, rule, "KIOCore/kio/kiomod.sip")
    rule_helpers.module_add_classes(filename, sip, rule, "KXmlGuiWindow", "QScriptable", "KIO::Connection",
                                    "KIO::ClipboardUpdater", "KIconLoader")


def container_rules():
    return [
        #
        # SIP does not seem to be able to handle these type specialization, but we can live without them?
        #
        ["Kross", "MetaTypeVariant", "", ".*", ".*", rule_helpers.container_discard],
        ["Kross", "Object", ".*", ".*", ".*", container_fixup],
        ["Kross", "InterpreterInfo", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]


def function_rules():
    return [
        ["Kross::Manager", "registerMetaTypeHandler", ".*", ".*", ".*", rule_helpers.function_discard],
        ["Kross::MetaTypeHandler", "MetaTypeHandler", ".*", ".*", ".*func", rule_helpers.function_discard],
    ]


def modulecode():
    return {
        "KrossCore/Kross/Core/Coremod.sip": {
            "code": module_fix_mapped_types_core,
        },
        "KrossUi/Kross/Ui/Uimod.sip": {
            "code": module_fix_mapped_types_ui,
        },
    }
