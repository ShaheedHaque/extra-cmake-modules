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
SIP binding customisation for PyKF5.Plasma. This modules describes:

    * Supplementary SIP file generator rules.
"""


_plasma_qobject_ctscc = """
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QObject'
    sipType = NULL;

    if (dynamic_cast<Plasma::ConfigLoader*>(sipCpp))
        sipType = sipType_Plasma_ConfigLoader;
    else if (dynamic_cast<Plasma::AccessAppletJob*>(sipCpp))
        sipType = sipType_Plasma_AccessAppletJob;
    else if (dynamic_cast<Plasma::ServiceAccessJob*>(sipCpp))
        sipType = sipType_Plasma_ServiceAccessJob;
    else if (dynamic_cast<Plasma::ServiceJob*>(sipCpp))
        sipType = sipType_Plasma_ServiceJob;
    else if (dynamic_cast<Plasma::AbstractDialogManager*>(sipCpp))
        sipType = sipType_Plasma_AbstractDialogManager;
    else if (dynamic_cast<Plasma::AbstractRunner*>(sipCpp))
        sipType = sipType_Plasma_AbstractRunner;
    else if (dynamic_cast<Plasma::AccessManager*>(sipCpp))
        sipType = sipType_Plasma_AccessManager;
    else if (dynamic_cast<Plasma::AnimationDriver*>(sipCpp))
        sipType = sipType_Plasma_AnimationDriver;
    else if (dynamic_cast<Plasma::Animator*>(sipCpp))
        sipType = sipType_Plasma_Animator;
    else if (dynamic_cast<Plasma::AuthorizationManager*>(sipCpp))
        sipType = sipType_Plasma_AuthorizationManager;
    else if (dynamic_cast<Plasma::AuthorizationRule*>(sipCpp))
        sipType = sipType_Plasma_AuthorizationRule;
    else if (dynamic_cast<Plasma::ClientPinRequest*>(sipCpp))
        sipType = sipType_Plasma_ClientPinRequest;
    else if (dynamic_cast<Plasma::ContainmentActions*>(sipCpp))
        sipType = sipType_Plasma_ContainmentActions;
    else if (dynamic_cast<Plasma::Context*>(sipCpp))
        sipType = sipType_Plasma_Context;
    else if (dynamic_cast<Plasma::DataContainer*>(sipCpp))
        sipType = sipType_Plasma_DataContainer;
    else if (dynamic_cast<Plasma::DataEngine*>(sipCpp))
        sipType = sipType_Plasma_DataEngine;
    else if (dynamic_cast<Plasma::DataEngineManager*>(sipCpp))
        sipType = sipType_Plasma_DataEngineManager;
    else if (dynamic_cast<Plasma::PackageStructure*>(sipCpp))
        sipType = sipType_Plasma_PackageStructure;
    else if (dynamic_cast<Plasma::RunnerContext*>(sipCpp))
        sipType = sipType_Plasma_RunnerContext;
    else if (dynamic_cast<Plasma::RunnerManager*>(sipCpp))
        sipType = sipType_Plasma_RunnerManager;
    else if (dynamic_cast<Plasma::ScriptEngine*>(sipCpp))
        {
        sipType = sipType_Plasma_ScriptEngine;
        if (dynamic_cast<Plasma::AppletScript*>(sipCpp))
            sipType = sipType_Plasma_AppletScript;
        else if (dynamic_cast<Plasma::DataEngineScript*>(sipCpp))
            sipType = sipType_Plasma_DataEngineScript;
        else if (dynamic_cast<Plasma::RunnerScript*>(sipCpp))
            sipType = sipType_Plasma_RunnerScript;
        else if (dynamic_cast<Plasma::WallpaperScript*>(sipCpp))
            sipType = sipType_Plasma_WallpaperScript;
        }
    else if (dynamic_cast<Plasma::Service*>(sipCpp))
        sipType = sipType_Plasma_Service;
    else if (dynamic_cast<Plasma::Svg*>(sipCpp))
        {
        sipType = sipType_Plasma_Svg;
        if (dynamic_cast<Plasma::FrameSvg*>(sipCpp))
            sipType = sipType_Plasma_FrameSvg;
        }
    else if (dynamic_cast<Plasma::Theme*>(sipCpp))
        sipType = sipType_Plasma_Theme;
    else if (dynamic_cast<Plasma::ToolTipManager*>(sipCpp))
        sipType = sipType_Plasma_ToolTipManager;
    else if (dynamic_cast<Plasma::Wallpaper*>(sipCpp))
        sipType = sipType_Plasma_Wallpaper;
    else if (dynamic_cast<Plasma::Animation*>(sipCpp))
        sipType = sipType_Plasma_Animation;
    else if (dynamic_cast<Plasma::Delegate*>(sipCpp))
        sipType = sipType_Plasma_Delegate;
    else if (dynamic_cast<Plasma::Corona*>(sipCpp))
        sipType = sipType_Plasma_Corona;
    else if (dynamic_cast<Plasma::AbstractToolBox*>(sipCpp))
        sipType = sipType_Plasma_AbstractToolBox;
    else if (dynamic_cast<Plasma::Applet*>(sipCpp))
        {
        sipType = sipType_Plasma_Applet;
        if (dynamic_cast<Plasma::AppletProtectedThunk*>(sipCpp))
            sipType = sipType_Plasma_AppletProtectedThunk;
        else if (dynamic_cast<Plasma::Containment*>(sipCpp))
            sipType = sipType_Plasma_Containment;
        else if (dynamic_cast<Plasma::GLApplet*>(sipCpp))
            sipType = sipType_Plasma_GLApplet;
        else if (dynamic_cast<Plasma::PopupApplet*>(sipCpp))
            sipType = sipType_Plasma_PopupApplet;
        }
    else if (dynamic_cast<Plasma::BusyWidget*>(sipCpp))
        sipType = sipType_Plasma_BusyWidget;
    else if (dynamic_cast<Plasma::DeclarativeWidget*>(sipCpp))
        sipType = sipType_Plasma_DeclarativeWidget;
    else if (dynamic_cast<Plasma::Extender*>(sipCpp))
        sipType = sipType_Plasma_Extender;
    else if (dynamic_cast<Plasma::ExtenderItem*>(sipCpp))
        {
        sipType = sipType_Plasma_ExtenderItem;
        if (dynamic_cast<Plasma::ExtenderGroup*>(sipCpp))
            sipType = sipType_Plasma_ExtenderGroup;
        }
    else if (dynamic_cast<Plasma::FlashingLabel*>(sipCpp))
        sipType = sipType_Plasma_FlashingLabel;
    else if (dynamic_cast<Plasma::Frame*>(sipCpp))
        sipType = sipType_Plasma_Frame;
    else if (dynamic_cast<Plasma::IconWidget*>(sipCpp))
        sipType = sipType_Plasma_IconWidget;
    else if (dynamic_cast<Plasma::ItemBackground*>(sipCpp))
        sipType = sipType_Plasma_ItemBackground;
    else if (dynamic_cast<Plasma::Meter*>(sipCpp))
        sipType = sipType_Plasma_Meter;
    else if (dynamic_cast<Plasma::ScrollWidget*>(sipCpp))
        sipType = sipType_Plasma_ScrollWidget;
    else if (dynamic_cast<Plasma::Separator*>(sipCpp))
        sipType = sipType_Plasma_Separator;
    else if (dynamic_cast<Plasma::SignalPlotter*>(sipCpp))
        sipType = sipType_Plasma_SignalPlotter;
    else if (dynamic_cast<Plasma::SvgWidget*>(sipCpp))
        sipType = sipType_Plasma_SvgWidget;
    else if (dynamic_cast<Plasma::TabBar*>(sipCpp))
        sipType = sipType_Plasma_TabBar;
    else if (dynamic_cast<Plasma::WebView*>(sipCpp))
        sipType = sipType_Plasma_WebView;
    else if (dynamic_cast<Plasma::CheckBox*>(sipCpp))
        sipType = sipType_Plasma_CheckBox;
    else if (dynamic_cast<Plasma::ComboBox*>(sipCpp))
        sipType = sipType_Plasma_ComboBox;
    else if (dynamic_cast<Plasma::GroupBox*>(sipCpp))
        sipType = sipType_Plasma_GroupBox;
    else if (dynamic_cast<Plasma::Label*>(sipCpp))
        sipType = sipType_Plasma_Label;
    else if (dynamic_cast<Plasma::LineEdit*>(sipCpp))
        sipType = sipType_Plasma_LineEdit;
    else if (dynamic_cast<Plasma::PushButton*>(sipCpp))
        sipType = sipType_Plasma_PushButton;
    else if (dynamic_cast<Plasma::RadioButton*>(sipCpp))
        sipType = sipType_Plasma_RadioButton;
    else if (dynamic_cast<Plasma::ScrollBar*>(sipCpp))
        sipType = sipType_Plasma_ScrollBar;
    else if (dynamic_cast<Plasma::Slider*>(sipCpp))
        sipType = sipType_Plasma_Slider;
    else if (dynamic_cast<Plasma::SpinBox*>(sipCpp))
        sipType = sipType_Plasma_SpinBox;
    else if (dynamic_cast<Plasma::TextBrowser*>(sipCpp))
        sipType = sipType_Plasma_TextBrowser;
    else if (dynamic_cast<Plasma::TextEdit*>(sipCpp))
        sipType = sipType_Plasma_TextEdit;
    else if (dynamic_cast<Plasma::ToolButton*>(sipCpp))
        sipType = sipType_Plasma_ToolButton;
    else if (dynamic_cast<Plasma::TreeView*>(sipCpp))
        sipType = sipType_Plasma_TreeView;
    else if (dynamic_cast<Plasma::VideoWidget*>(sipCpp))
        sipType = sipType_Plasma_VideoWidget;
    else if (dynamic_cast<Plasma::Dialog*>(sipCpp))
        sipType = sipType_Plasma_Dialog;
    else if (dynamic_cast<Plasma::View*>(sipCpp))
        sipType = sipType_Plasma_View;
%End
"""


import rule_helpers


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<QVariant>", "QList<KPluginInfo>",
                                   "QList<KPluginMetaData>", "QList<QAction *>", "QList<QUrl>",
                                   "QMap<QString, QVariant>")
    rule_helpers.module_add_classes(filename, sip, entry, "KConfigLoader", "KActionCollection", "QWidget")

def modulecode():
    return {
        "Plasmamod.sip": {
            "code": module_fix_mapped_types,
        },
    }


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED Plasma::AbstractRunner": {
            "code": _plasma_qobject_ctscc
        },
        # ./plasma/animation.sip
        "Animation": {  # Animation : QAbstractAnimation
            "code": _plasma_qobject_ctscc
        },
        # ./plasma/packagestructure.sip
        "QList<const char*>": {  # QList<const char*>
            "code":
                """
                %ConvertToTypeCode
                    return NULL;
                %End
                %ConvertFromTypeCode
                    // Create the list.
                    PyObject *l;
            
                    if ((l = PyList_New(sipCpp->size())) == NULL)
                        return NULL;
            
                    // Set the list elements.
                    for (int i = 0; i < sipCpp->size(); ++i)
                    {
                        PyObject *pobj;
                        int iserr;
            
                        if ((pobj = sipBuildResult(&iserr,"s",sipCpp->value(i))) == NULL)
                        {
                            Py_DECREF(l);
            
                            return NULL;
                        }
            
                        PyList_SET_ITEM(l, i, pobj);
                    }
            
                    return l;
                %End
                """
        },
    }