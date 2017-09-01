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
SIP binding customisation for PyKF5.KArchive. This modules describes:

    * Supplementary SIP file generator rules.
"""

def container_add_includes(container, sip, rule):
    sip["code"] += """%TypeHeaderCode
#include <KArchive/KArchive>
#include <QtCore/QDateTime>
#include <QtCore/QIODevice>
%End
"""


def function_rewrite_dir(container, fn, sip, rule):
    sip["parameters"][0] = "KArchive *archive"


def function_rewrite_entry(container, fn, sip, rule):
    sip["parameters"] = ["KArchive *archive", "const QString &name", "int access", "const QDateTime &date",
                         "const QString &user", "const QString &group", "const QString &symlink"]


def function_rewrite_file(container, fn, sip, rule):
    sip["parameters"] = ["KArchive *archive", "const QString &name", "int access", "const QDateTime &date",
                         "const QString &user", "const QString &group", "const QString &symlink", "qint64 pos",
                         "qint64 size"]


def function_rewrite_setsize(container, fn, sip, rule):
    sip["parameters"] = ["qint64 s"]


def function_rewrite_copyto(container, fn, sip, rule):
    sip["parameters"] = ["const QString &dest"]


def function_return_karchive(container, fn, sip, rule):
    sip["fn_result"] = "KArchive *"


def function_return_qdatetime(container, fn, sip, rule):
    sip["fn_result"] = "QDateTime"


def function_return_qstring(container, fn, sip, rule):
    sip["fn_result"] = "QString"


def function_return_mode_t(container, fn, sip, rule):
    sip["fn_result"] = "int"


def function_return_qint64(container, fn, sip, rule):
    sip["fn_result"] = "qint64"


def function_return_qbytearray(container, fn, sip, rule):
    sip["fn_result"] = "virtual QByteArray"


def function_return_qiodevice(container, fn, sip, rule):
    sip["fn_result"] = "virtual QIODevice *"


def container_rules():
    return [
        #
        # Completely rewrite args because ofmissing fwd decls/#includes.
        #
        [".*", "KArchiveEntry|KArchiveDirectory|KArchiveFile", ".*", ".*", ".*", container_add_includes],
    ]


def function_rules():
    return [
        #
        # Completely rewrite args because ofmissing fwd decls/#includes.
        #
        ["KArchiveEntry", "name|user|group|symLinkTarget", ".*", ".*", ".*", function_return_qstring],
        ["KArchiveEntry", "date", ".*", ".*", ".*", function_return_qdatetime],
        ["KArchiveEntry", "archive", ".*", ".*", ".*", function_return_karchive],
        ["KArchiveEntry", "permissions", ".*", ".*", ".*", function_return_mode_t],
        ["KArchiveEntry", "KArchiveEntry", ".*", ".*", ".*", function_rewrite_entry],
        ["KArchiveDirectory", "KArchiveDirectory", ".*", ".*", ".*", function_rewrite_dir],
        ["KArchiveFile", "KArchiveFile", ".*", ".*", ".*", function_rewrite_file],
        ["KArchiveFile", "position|size", ".*", ".*", ".*", function_return_qint64],
        ["KArchiveFile", "setSize", ".*", ".*", ".*", function_rewrite_setsize],
        ["KArchiveFile", "copyTo", ".*", ".*", ".*", function_rewrite_copyto],
        ["KArchiveFile", "data", ".*", ".*", ".*", function_return_qbytearray],
        ["KArchiveFile", "createDevice", ".*", ".*", ".*", function_return_qiodevice],
    ]
