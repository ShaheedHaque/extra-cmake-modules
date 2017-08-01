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
SIP binding customisation for PyKF5.Solid. This modules describes:

    * Supplementary SIP file generator rules.
"""
import rule_helpers


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<int>")


def function_rules():
    return [
        #
        # Discard non-const.
        #
        ["Solid::Device", "asDeviceInterface", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
    ]


def modulecode():
    return {
        "Solidmod.sip": {
            "code": module_fix_mapped_types,
        },
    }


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED Solid::DeviceInterface": {  # DeviceInterface : QObject
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'QObject'
                    sipType = NULL;
            
                    if (dynamic_cast<Solid::DeviceInterface*>(sipCpp))
                        {
                        sipType = sipType_Solid_DeviceInterface;
                        if (dynamic_cast<Solid::AcAdapter*>(sipCpp))
                            sipType = sipType_Solid_AcAdapter;
                        else if (dynamic_cast<Solid::AudioInterface*>(sipCpp))
                            sipType = sipType_Solid_AudioInterface;
                        else if (dynamic_cast<Solid::Battery*>(sipCpp))
                            sipType = sipType_Solid_Battery;
                        else if (dynamic_cast<Solid::Block*>(sipCpp))
                            sipType = sipType_Solid_Block;
                        else if (dynamic_cast<Solid::Button*>(sipCpp))
                            sipType = sipType_Solid_Button;
                        else if (dynamic_cast<Solid::Camera*>(sipCpp))
                            sipType = sipType_Solid_Camera;
                        else if (dynamic_cast<Solid::DvbInterface*>(sipCpp))
                            sipType = sipType_Solid_DvbInterface;
                        else if (dynamic_cast<Solid::GenericInterface*>(sipCpp))
                            sipType = sipType_Solid_GenericInterface;
                        else if (dynamic_cast<Solid::InternetGateway*>(sipCpp))
                            sipType = sipType_Solid_InternetGateway;
                        else if (dynamic_cast<Solid::NetworkInterface*>(sipCpp))
                            sipType = sipType_Solid_NetworkInterface;
                        else if (dynamic_cast<Solid::NetworkShare*>(sipCpp))
                            sipType = sipType_Solid_NetworkShare;
                        else if (dynamic_cast<Solid::PortableMediaPlayer*>(sipCpp))
                            sipType = sipType_Solid_PortableMediaPlayer;
                        else if (dynamic_cast<Solid::Processor*>(sipCpp))
                            sipType = sipType_Solid_Processor;
                        else if (dynamic_cast<Solid::SerialInterface*>(sipCpp))
                            sipType = sipType_Solid_SerialInterface;
                        else if (dynamic_cast<Solid::SmartCardReader*>(sipCpp))
                            sipType = sipType_Solid_SmartCardReader;
                        else if (dynamic_cast<Solid::StorageAccess*>(sipCpp))
                            sipType = sipType_Solid_StorageAccess;
                        else if (dynamic_cast<Solid::StorageDrive*>(sipCpp))
                            {
                            sipType = sipType_Solid_StorageDrive;
                            if (dynamic_cast<Solid::OpticalDrive*>(sipCpp))
                                sipType = sipType_Solid_OpticalDrive;
                            }
                        else if (dynamic_cast<Solid::StorageVolume*>(sipCpp))
                            {
                            sipType = sipType_Solid_StorageVolume;
                            if (dynamic_cast<Solid::OpticalDisc*>(sipCpp))
                                sipType = sipType_Solid_OpticalDisc;
                            }
                        else if (dynamic_cast<Solid::Video*>(sipCpp))
                            sipType = sipType_Solid_Video;
                        }
                    else if (dynamic_cast<Solid::DeviceNotifier*>(sipCpp))
                        sipType = sipType_Solid_DeviceNotifier;
                    else if (dynamic_cast<Solid::Networking::Notifier*>(sipCpp))
                        sipType = sipType_Solid_Networking_Notifier;
                %End
                """
        },
        # ./solid/powermanagement.sip
        "QSet<Solid::PowerManagement::SleepState>": {  # QSet<Solid::PowerManagement::SleepState>
            "code":
                """
                %TypeHeaderCode
                #include <qset.h>
                #include <powermanagement.h>
                %End
                %ConvertFromTypeCode
                    // Create the list.
                    PyObject *l;
            
                    if ((l = PyList_New(sipCpp->size())) == NULL)
                        return NULL;
            
                    // Set the list elements.
                    QSet<Solid::PowerManagement::SleepState> set = *sipCpp;
                    int i = 0;
                    foreach (Solid::PowerManagement::SleepState value, set)
                    {
                #if PY_MAJOR_VERSION >= 3
                        PyObject *obj = PyLong_FromLong ((long) value);
                #else
                        PyObject *obj = PyInt_FromLong ((long) value);
                #endif
                        if (obj == NULL || PyList_SET_ITEM (l, i, obj) < 0)
                        {
                            Py_DECREF(l);
            
                            if (obj)
                                Py_DECREF(obj);
            
                            return NULL;
                        }
            
                        Py_DECREF(obj);
                        i++;
                    }
            
                    return l;
                %End
                %ConvertToTypeCode
                    // Check the type if that is all that is required.
                    if (sipIsErr == NULL)
                    {
                        if (!PyList_Check(sipPy))
                            return 0;
                    }
            
                    // Check the type if that is all that is required.
                    if (sipIsErr == NULL)
                    {
                        if (!PyList_Check(sipPy))
                            return 0;
                    }
            
                    QSet<Solid::PowerManagement::SleepState> *qs = new QSet<Solid::PowerManagement::SleepState>;
            
                    for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i)
                    {
                #if PY_MAJOR_VERSION >= 3
                        Solid::PowerManagement::SleepState t = (Solid::PowerManagement::SleepState)PyLong_AsLong (PyList_GET_ITEM (sipPy, i));
                #else
                        Solid::PowerManagement::SleepState t = (Solid::PowerManagement::SleepState)PyInt_AS_LONG (PyList_GET_ITEM (sipPy, i));
                #endif
                        *qs << t;
            
                    }
            
                    *sipCppPtr = qs;
            
                    return sipGetState(sipTransferObj);
                %End
                """
        },
        # ./solid/predicate.sip
        "QSet<Solid::DeviceInterface::Type>": {  # QSet<Solid::DeviceInterface::Type>
            "code":
                """
                %TypeHeaderCode
                #include <qset.h>
                #include <powermanagement.h>
                %End
                %ConvertFromTypeCode
                    // Create the list.
                    PyObject *l;
            
                    if ((l = PyList_New(sipCpp->size())) == NULL)
                        return NULL;
            
                    // Set the list elements.
                    QSet<Solid::DeviceInterface::Type> set = *sipCpp;
                    int i = 0;
                    foreach (Solid::DeviceInterface::Type value, set)
                    {
                #if PY_MAJOR_VERSION >= 3
                        PyObject *obj = PyLong_FromLong ((long) value);
                #else
                        PyObject *obj = PyInt_FromLong ((long) value);
                #endif
                        if (obj == NULL || PyList_SET_ITEM (l, i, obj) < 0)
                        {
                            Py_DECREF(l);
            
                            if (obj)
                                Py_DECREF(obj);
            
                            return NULL;
                        }
            
                        Py_DECREF(obj);
                        i++;
                    }
            
                    return l;
                %End
                %ConvertToTypeCode
                    // Check the type if that is all that is required.
                    if (sipIsErr == NULL)
                    {
                        if (!PyList_Check(sipPy))
                            return 0;
                    }
            
                    // Check the type if that is all that is required.
                    if (sipIsErr == NULL)
                    {
                        if (!PyList_Check(sipPy))
                            return 0;
                    }
            
                    QSet<Solid::DeviceInterface::Type> *qs = new QSet<Solid::DeviceInterface::Type>;
            
                    for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i)
                    {
                #if PY_MAJOR_VERSION >= 3
                        Solid::DeviceInterface::Type t = (Solid::DeviceInterface::Type)PyLong_AsLong (PyList_GET_ITEM (sipPy, i));
                #else
                        Solid::DeviceInterface::Type t = (Solid::DeviceInterface::Type)PyInt_AS_LONG (PyList_GET_ITEM (sipPy, i));
                #endif
                *qs << t;
            
                    }
            
                    *sipCppPtr = qs;
            
                    return sipGetState(sipTransferObj);
                %End
                """
        },
    }
