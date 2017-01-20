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
SIP binding customisation for PyKF5.KService. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rules_engine


def _discard_QSharedData(container, sip, matcher):
    sip["base_specifiers"].remove("QSharedData")


def container_rules():
    return [
        ["ksycocaentry.h", "KSycocaEntry", ".*", ".*", ".*QSharedData.*", _discard_QSharedData],
    ]


def function_rules():
    return [
        #
        # Provide %MethodCode and a C++ signature.
        #
        ["KMimeTypeTrader|KServiceTypeTrader", "preferredService", ".*", ".*", ".*", rules_engine.function_discard],
        ["KPluginInfo", "KPluginInfo", ".*", ".*", ".*SharedData.*", rules_engine.function_discard],
        ["KPluginInfo", "service", ".*", ".*", ".*", rules_engine.function_discard],
        ["KService", "service.*", ".*", ".*", ".*", rules_engine.function_discard],
        ["KServiceGroup", "root|group|childGroup|addEntry", ".*", ".*", ".*", rules_engine.function_discard],
        ["KServiceType", "parentType|serviceType", ".*", ".*", ".*", rules_engine.function_discard],
        ["KSycoca", "stream", ".*", ".*", ".*", rules_engine.function_discard],
        #
        # No KSycocaFactory or KSycocaFactoryList.
        #
        ["KSycoca", "addFactory|factories", ".*", ".*", ".*", rules_engine.function_discard],
    ]


def typedef_rules():
    return [
        #
        # Duplicate.
        #
        ["kmimetypetrader.h", "KServiceOfferList", ".*", ".*", rules_engine.typedef_discard],
    ]


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kservicegroup.h::KServiceGroup": {  # KServiceGroup : KSycocaEntry
            "code":
                """
                %ConvertToSubClassCode

                    if (dynamic_cast<KServiceGroup*>(sipCpp))
                        sipClass = sipClass_KServiceGroup;
                    else if (dynamic_cast<KServiceSeparator*>(sipCpp))
                        sipClass = sipClass_KServiceSeparator;
                    else
                        sipClass = NULL;
                %End
                """
        },
        "KServiceGroup::List": {  # KServiceGroup::List
            "code":
                """
                %ConvertFromTypeCode
                    // Create the list.
                    PyObject *l;

                    if ((l = PyList_New(sipCpp->size())) == NULL)
                        return NULL;

                    // Set the list elements.
                    for (int i = 0; i < sipCpp->size(); ++i)
                    {
                        KServiceGroup::SPtr *t = new KServiceGroup::SPtr (sipCpp->at(i));
                        PyObject *tobj;

                        if ((tobj = sipConvertFromNewInstance(t->data(), sipClass_KServiceGroup, sipTransferObj)) == NULL)
                        {
                            Py_DECREF(l);
                            delete t;

                            return NULL;
                        }

                        PyList_SET_ITEM(l, i, tobj);
                    }

                    return l;
                %End
                %ConvertToTypeCode
                    // Check the type if that is all that is required.
                    if (sipIsErr == NULL)
                    {
                        if (!PyList_Check(sipPy))
                            return 0;

                        for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i)
                            if (!sipCanConvertToInstance(PyList_GET_ITEM(sipPy, i), sipClass_KServiceGroup, SIP_NOT_NONE))
                                return 0;

                        return 1;
                    }

                    QList<KServiceGroup::SPtr> *ql = new QList<KServiceGroup::SPtr>;

                    for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i)
                    {
                        int state;
                        KServiceGroup *t = reinterpret_cast<KServiceGroup *>(sipConvertToInstance(PyList_GET_ITEM(sipPy, i), sipClass_KServiceGroup, sipTransferObj, SIP_NOT_NONE, &state, sipIsErr));

                        if (*sipIsErr)
                        {
                            sipReleaseInstance(t, sipClass_KServiceGroup, state);

                            delete ql;
                            return 0;
                        }

                        KServiceGroup::SPtr *tptr = new KServiceGroup::SPtr (t);

                        ql->append(*tptr);

                        sipReleaseInstance(t, sipClass_KServiceGroup, state);
                    }

                    *sipCppPtr = ql;

                    return sipGetState(sipTransferObj);
                %End
                """
        },
    }