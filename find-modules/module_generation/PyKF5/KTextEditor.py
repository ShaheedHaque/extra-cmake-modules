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
SIP binding customisation for PyKF5.KTextEditor. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers


def _function_make_public(container, function, sip, matcher):
    sip["prefix"] = "public: "


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<QAction *>", "QSet<QString>")
    rule_helpers.module_add_classes(filename, sip, entry, "KXmlGuiWindow /External/", "KIconLoader",
                                    "KSslCertificateBoxPrivate")


_ktexteditor_qobject_ctscc = """
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QObject'
    sipType = NULL;

    if (dynamic_cast<KTextEditor::Document*>(sipCpp))
        sipType = sipType_KTextEditor_Document;
    else if (dynamic_cast<KTextEditor::AnnotationModel*>(sipCpp))
        sipType = sipType_KTextEditor_AnnotationModel;
    else if (dynamic_cast<KTextEditor::Editor*>(sipCpp))
        sipType = sipType_KTextEditor_Editor;
    else if (dynamic_cast<KTextEditor::LoadSaveFilterCheckPlugin*>(sipCpp))
        sipType = sipType_KTextEditor_LoadSaveFilterCheckPlugin;
    else if (dynamic_cast<KTextEditor::Plugin*>(sipCpp))
        sipType = sipType_KTextEditor_Plugin;
    else if (dynamic_cast<KTextEditor::CodeCompletionModel*>(sipCpp))
        {
        sipType = sipType_KTextEditor_CodeCompletionModel;
        if (dynamic_cast<KTextEditor::CodeCompletionModel2*>(sipCpp))
            sipType = sipType_KTextEditor_CodeCompletionModel2;
        }
    else if (dynamic_cast<KTextEditor::ConfigPage*>(sipCpp))
        sipType = sipType_KTextEditor_ConfigPage;
    else if (dynamic_cast<KTextEditor::EditorChooser*>(sipCpp))
        sipType = sipType_KTextEditor_EditorChooser;
    else if (dynamic_cast<KTextEditor::View*>(sipCpp))
        sipType = sipType_KTextEditor_View;
%End
"""


def container_rules():
    return [
        ["KTextEditor", "Attribute", ".*", ".*", ".*QSharedData.*", rule_helpers.container_discard_QSharedData_base],
        ["KTextEditor", "AttributeBlock", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]


def function_rules():
    return [
        ["KTextEditor::.*Cursor", "operator Cursor", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KTextEditor::MovingRange", "operator Range", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KTextEditor::MovingCursor", "MovingCursor", ".*", "", ".*", _function_make_public],
        #
        # SIP unsupported signal argument type.
        #
        ["KTextEditor::MarkInterface", "markToolTipRequested", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KTextEditor::MarkInterface", "markContextMenuRequested", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KTextEditor::MarkInterface", "markClicked", ".*", ".*", ".*", rule_helpers.function_discard],
    ]


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED KTextEditor::AnnotationInterface": { #AnnotationInterface
            "code":
            """
            %ConvertToSubClassCode
                // CTSCC for subclasses of 'AnnotationInterface'
                sipType = NULL;
            
                if (dynamic_cast<KTextEditor::AnnotationViewInterface*>(sipCpp))
                    sipType = sipType_KTextEditor_AnnotationViewInterface;
            %End
            """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED KTextEditor::TemplateInterface": { #TemplateInterface
            "code":
            """
            %ConvertToSubClassCode
                // CTSCC for subclasses of 'TemplateInterface'
                sipType = NULL;
            
                if (dynamic_cast<KTextEditor::TemplateInterface2*>(sipCpp))
                    sipType = sipType_KTextEditor_TemplateInterface2;
            %End
            """
        },
        "KTextEditor::QHash<int,KTextEditor::Mark*>": { #QHash<int,KTextEditor::Mark*>
            "code":
            """
            %ConvertFromTypeCode
                // Create the dictionary.
                PyObject *d = PyDict_New();
            
                if (!d)
                    return NULL;
            
                // Set the dictionary elements.
                QHash<int, KTextEditor::Mark*>::const_iterator i = sipCpp->constBegin();
            
                while (i != sipCpp->constEnd())
                {
                    int t1 = i.key();
                    KTextEditor::Mark *t2 = i.value();
            
            #if PY_MAJOR_VERSION >= 3
                    PyObject *t1obj = PyLong_FromLong ((long)t1);
            #else
                    PyObject *t1obj = PyInt_FromLong ((long)t1);
            #endif
                    PyObject *t2obj = sipConvertFromNewInstance(t2, sipClass_KTextEditor_Mark, sipTransferObj);
            
                    if (t2obj == NULL || PyDict_SetItem(d, t1obj, t2obj) < 0)
                    {
                        Py_DECREF(d);
            
                        if (t1obj)
                            Py_DECREF(t1obj);
            
                        if (t2obj)
                            Py_DECREF(t2obj);
                        else
                            delete t2;
            
                        return NULL;
                    }
            
                    Py_DECREF(t1obj);
                    Py_DECREF(t2obj);
            
                    ++i;
                }
            
                return d;
            %End
            %ConvertToTypeCode
                PyObject *t1obj, *t2obj;
                SIP_SSIZE_T i = 0;
            
                // Check the type if that is all that is required.
                if (sipIsErr == NULL)
                {
                    if (!PyDict_Check(sipPy))
                        return 0;
            
                    while (PyDict_Next(sipPy, &i, &t1obj, &t2obj))
                    {
            #if PY_MAJOR_VERSION >= 3
                        if (!PyNumber_Check (t1obj))
            #else
                        if (!PyInt_Check (t1obj))
            #endif
                            return 0;
            
                        if (!sipCanConvertToInstance(t2obj, sipClass_KTextEditor_Mark, SIP_NOT_NONE))
                            return 0;
                    }
            
                    return 1;
                }
            
                QHash<int, KTextEditor::Mark*> *qm = new QHash<int, KTextEditor::Mark*>;
            
                while (PyDict_Next(sipPy, &i, &t1obj, &t2obj))
                {
                    int state2;
            
            #if PY_MAJOR_VERSION >= 3
                    int t1 = PyLong_AsLong (t1obj);
            #else
                    int t1 = PyInt_AS_LONG (t1obj);
            #endif
                    KTextEditor::Mark *t2 = reinterpret_cast<KTextEditor::Mark *>(sipConvertToInstance(t2obj, sipClass_KTextEditor_Mark, sipTransferObj, SIP_NOT_NONE, &state2, sipIsErr));
            
                    if (*sipIsErr)
                    {
                        sipReleaseInstance(t2, sipClass_KTextEditor_Mark, state2);
            
                        delete qm;
                        return 0;
                    }
            
                    qm->insert(t1, t2);
            
                    sipReleaseInstance(t2, sipClass_KTextEditor_Mark, state2);
                }
            
                *sipCppPtr = qm;
            
                return sipGetState(sipTransferObj);
            %End
            """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED KTextEditor::Document": { #Document : KParts::ReadWritePart
            "code": _ktexteditor_qobject_ctscc
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED KTextEditor::CodeCompletionModel": { #CodeCompletionModel : QAbstractItemModel
            "code": _ktexteditor_qobject_ctscc
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED KTextEditor::Attribute": { #Attribute : QTextCharFormat
            "code":
            """
            %ConvertToSubClassCode
                // CTSCC for subclasses of 'QTextFormat'
                sipType = NULL;
            
                if (dynamic_cast<KTextEditor::Attribute*>(sipCpp))
                    sipType = sipType_KTextEditor_Attribute;
            %End
            """
        },
    }


def modulecode():
    return {
        "KTextEditor/KTextEditor/KTextEditormod.sip": {
            "code": module_fix_mapped_types,
        },
    }
