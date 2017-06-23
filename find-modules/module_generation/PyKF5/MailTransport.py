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
SIP binding customisation for PyKF5.MailTransport. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rules_engine


def _parameter_remove_prefix(container, function, parameter, sip, matcher):
    sip["init"] = sip["init"].replace("Akonadi::-1", "-1")


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rules_engine.modulecode_delete(filename, sip, entry, "QList<int>", "QSharedPointer<KMime::Message>")
    rules_engine.code_add_classes(filename, sip, entry, "Akonadi::SpecialMailCollectionsPrivate",
                                  "MailTransport::SentActionAttribute", "Akonadi::Protocol::Command",
                                  "Akonadi::ServerManagerPrivate", "KWallet::Wallet")
    rules_engine.code_add_imports(filename, sip, entry, "MailTransport/mailtransport/mailtransportmod.sip")


def parameter_rules():
    return [
        ["MailTransport::SentBehaviourAttribute", "SentBehaviourAttribute", "moveToCollection", ".*", ".*", _parameter_remove_prefix],
    ]


def modulecode():
    return {
        "MailTransportmod.sip": {
            "code": module_fix_mapped_types,
        },
    }
