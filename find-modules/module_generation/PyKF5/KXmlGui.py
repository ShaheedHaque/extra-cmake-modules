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
SIP binding customisation for PyKF5.KXmlGui. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rules_engine


def _parameter_remove_qualifier(container, function, parameter, sip, matcher):
    sip["init"] = sip["init"].split(":")[-1]


def function_rules():
    return [
        ["KMainWindow", "k_func", ".*", ".*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KMainWindow", "KMainWindow", ".*", ".*", "KMainWindowPrivate.*", rules_engine.function_discard],
    ]


def parameter_rules():
    return [
        ["KMainWindow", "KMainWindow", "f", ".*", ".*::.*", _parameter_remove_qualifier],
    ]


def modulecode():
    return {
        "kgesturemap_p.h": {
            "code": "",
            "decl": ""
        },
        "ktoggletoolbaraction.h": {
            "code": "",
            "decl": ""
        },
        #
        # No multiple inheritance.
        #
        "kxmlguiwindow.h": {
            "code": "",
            "decl": ""
        },
        "KXmlGuimod.sip": {
            "code":
                """
                %Import(name=QtXml/QtXmlmod.sip)
                """
        },
    }


def methodcode():
    return {
        "KXMLGUIBuilder": {
            "createContainer": {
                "parameters": ["QWidget* parent /Transfer/", "int index", "const QDomElement& element"],
                "fn_result": "SIP_PYTUPLE",
                "cxx_parameters": ["QWidget* parent", "int index", "const QDomElement& element", "QAction*& containerAction"],
                "cxx_fn_result": "QWidget*",
                "code":
                    """
                    %MethodCode
                        QAction *containerAction;
                        QWidget* res;
                        Py_BEGIN_ALLOW_THREADS
                        res = sipSelfWasArg ? sipCpp->KXMLGUIBuilder::createContainer (a0, a1, *a2, containerAction) : sipCpp->createContainer (a0, a1, *a2, containerAction);
                        Py_END_ALLOW_THREADS

                        PyObject *pyWidget;
                        PyObject *pyContainerAction;

                        if ((pyWidget = sipConvertFromNewInstance(res, sipClass_QWidget, NULL)) == NULL)
                            return NULL;

                        if ((pyContainerAction = sipConvertFromNewInstance(containerAction, sipClass_QAction, NULL)) == NULL)
                            return NULL;

                        sipRes = Py_BuildValue ("NN", pyWidget, pyContainerAction);
                    %End
                    """
            },
        },
    }
