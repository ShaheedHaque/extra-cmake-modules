#
# Copyright 2016 by Shaheed Haque (srhaque@theiet.org)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# Text snippets in this file are derived from PyKDE4, and are in turn derived
# from kde library code. The licence for the snippets is below.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Library General Public License as
# published by the Free Software Foundation; either version 2, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details
#
# You should have received a copy of the GNU Library General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
SIP binding custom method-related code for PyKF5.
"""


#
# Main dictionary.
#
# For a top level object, when using sip_bulk_generator.py, it is important to use the name of any forwardee header in
# the key, since that is the file we actually use.
#
def code():
    return {
# ./kdecore/kurl.sip
"kdecore/kurl.h":
{
    "__len__":
    {
        "code":
        """
        %MethodCode
            //returns (int)
            Py_BEGIN_ALLOW_THREADS
            sipRes = sipCpp -> count();
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "__setitem__":
    {
        "code":
        """
        %MethodCode
            //takes index | (int) | value | (KUrl)
            int len;
    
            len = sipCpp -> count();
    
            if ((a0 = sipConvertFromSequenceIndex(a0,len)) < 0)
                sipIsErr = 1;
            else
                (*sipCpp)[a0] = *a1;
        %End
        """
    },
    "__setitem__":
    {
        "code":
        """
        %MethodCode
            //takes range | (a Python slice) | urlList | (KUrl.List)
            SIP_SSIZE_T len, start, stop, step, slicelength, i;
    
            len = sipCpp -> count();
    
            if (sipConvertFromSliceObject(a0,len,&start,&stop,&step,&slicelength) < 0)
                sipIsErr = 1;
            else
            {
                int vlen = a1 -> count();
                if (vlen != slicelength)
                {
                    sipBadLengthForSlice(vlen,slicelength);
                    sipIsErr = 1;
                }
                else
                {
                    KUrl::List::ConstIterator it = a1 -> begin();
                    for (i = 0; i < slicelength; ++i)
                    {
                        (*sipCpp)[start] = *it;
                        start += step;
                        ++it;
                    }
                }
            }
        %End
        """
    },
    "__delitem__":
    {
        "code":
        """
        %MethodCode
            //takes index | (int)
            int len;
    
            len = sipCpp -> count();
    
            if ((a0 = sipConvertFromSequenceIndex(a0,len)) < 0)
                sipIsErr = 1;
            else
                sipCpp -> removeAt(a0);
        %End
        """
    },
    "__delitem__":
    {
        "code":
        """
        %MethodCode
            //takes range | (a Python slice)
            SIP_SSIZE_T len, start, stop, step, slicelength, i;
    
            len = sipCpp -> count();
            if (sipConvertFromSliceObject(a0,len,&start,&stop,&step,&slicelength) < 0)
                sipIsErr = 1;
            else
                for (i = 0; i < slicelength; ++i)
                {
                    sipCpp -> removeAt(start);
                    start += step - 1;
                }
        %End
        """
    },
    "operator[]":
    {
        "parameters": "KUrl operator",
        "cxx_parameters": "[] (int)",
        "code":
        """
        %MethodCode
            //returns (KUrl)
            //takes index | (int)
            int len;
    
            len = sipCpp -> count();
    
            if ((a0 = sipConvertFromSequenceIndex(a0,len)) < 0)
                sipIsErr = 1;
            else
                sipRes = new KUrl((*sipCpp)[a0]);
        %End
        """
    },
    "operator[]":
    {
        "parameters": "KUrl::List operator",
        "cxx_parameters": "[] (SIP_PYSLICE)",
        "code":
        """
        %MethodCode
            //returns (KUrl.List)
            //takes range | (a Python slice)
            SIP_SSIZE_T len, start, stop, step, slicelength, i;
    
            len = sipCpp -> count();
    
            if (sipConvertFromSliceObject(a0,len,&start,&stop,&step,&slicelength) < 0)
                sipIsErr = 1;
            else
            {
                sipRes = new KUrl::List();
    
                for (i = 0; i < slicelength; ++i)
                {
                    (*sipRes) += (*sipCpp)[start];
                    start += step;
                }
            }
        %End
        """
    },
    "operator+":
    {
        "code":
        """
        %MethodCode
            //returns (KUrl.List)
            //takes listToAdd | (KUrl.List)
            Py_BEGIN_ALLOW_THREADS
            //    sipRes = new KUrl::List((const KUrl::List&)((*sipCpp) + *a0));
            sipRes = new KUrl::List (*sipCpp);
            (*sipRes) += (*a0);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "operator*":
    {
        "code":
        """
        %MethodCode
            sipRes = new KUrl::List();
    
            for (int i = 0; i < a0; ++i)
                (*sipRes) += (*sipCpp);
        %End
        """
    },
    "operator*=":
    {
        "code":
        """
        %MethodCode
            //returns (KUrl.List)
            //takes val | (int)
            KUrl::List orig(*sipCpp);
    
            sipCpp -> clear();
    
            for (int i = 0; i < a0; ++i)
                (*sipCpp) += orig;
        %End
        """
    },
    "__contains__":
    {
        "code":
        """
        %MethodCode
            //returns (bool)
            //takes a0 | (KUrl)
            // It looks like you can't assign QBool to int.
            sipRes = bool(sipCpp->contains(*a0));
        %End
        """
    },
},
# ./kdecore/kcmdlineargs.sip
"KCmdLineArgs::StdCmdLineArgs":
{
    "init":
    {
        "parameters": ["SIP_PYLIST argv", "const QByteArray& appname", "const QByteArray& catalog", "const KLocalizedString& programName", "const QByteArray& version", "const KLocalizedString& description = KLocalizedString()", "int stdargs = 3"],
        "cxx_parameters": ["int", "char**", "const QByteArray&", "const QByteArray&", "const KLocalizedString&", "const QByteArray&", "const KLocalizedString& = KLocalizedString()", "KCmdLineArgs::StdCmdLineArgs = 3"],
        "code":
        """
        %MethodCode
            KCmdLineArgs::StdCmdLineArgs cmdLineArgs = (KCmdLineArgs::StdCmdLineArgs) a6;
            int argc, nargc;
            char **argv;
    
            // Convert the list.
    
            if ((argv = pyArgvToC(a0, &argc)) == NULL)
                return NULL;
    
            // Create it now the arguments are right.
            nargc = argc;
    
            Py_BEGIN_ALLOW_THREADS
            KCmdLineArgs::init (nargc, argv, *a1, *a2, *a3, *a4, *a5, cmdLineArgs);
            Py_END_ALLOW_THREADS
    
            // Now modify the original list.
    
            updatePyArgv (a0, argc, argv);
        %End
        """
    },
    "init":
    {
        "parameters": ["SIP_PYLIST argv", "const KAboutData* about", "int stdargs = 3"],
        "cxx_parameters": ["int", "char**", "const KAboutData*", "KCmdLineArgs::StdCmdLineArgs = 3"],
        "code":
        """
        %MethodCode
            KCmdLineArgs::StdCmdLineArgs cmdLineArgs = (KCmdLineArgs::StdCmdLineArgs) a2;
            int argc, nargc;
            char **argv;
    
            // Convert the list.
    
            if ((argv = pyArgvToC(a0, &argc)) == NULL)
                return NULL;
    
            // Create it now the arguments are right.
            nargc = argc;
    
            Py_BEGIN_ALLOW_THREADS
            KCmdLineArgs::init (nargc, argv, a1, cmdLineArgs);
            Py_END_ALLOW_THREADS
    
            // Now modify the original list.
    
            updatePyArgv (a0, argc, argv);
        %End
        """
    },
},
# ./kdecore/typedefs.sip
"kdecore/typedefs.h":
{
    "version":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = KDE::version ();
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "versionMajor":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = KDE::versionMajor ();
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "versionMinor":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
                sipRes = KDE::versionMinor ();
                Py_END_ALLOW_THREADS
        %End
        """
    },
    "versionRelease":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = KDE::versionRelease ();
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "versionString":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = KDE::versionString ();
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "pykde_version":
    {
        "code":
        """
        %MethodCode
            //version
            sipRes = 0x040002;
        %End
        """
    },
    "pykde_versionMajor":
    {
        "code":
        """
        %MethodCode
            //major
            sipRes = 0x04;
        %End
        """
    },
    "pykde_versionMinor":
    {
        "code":
        """
        %MethodCode
            //minor
            sipRes = 0x00;
        %End
        """
    },
    "pykde_versionRelease":
    {
        "code":
        """
        %MethodCode
            //release
            sipRes = 0x02;
        %End
        """
    },
    "pykde_versionString":
    {
        "code":
        """
        %MethodCode
            //string
            sipRes = "4.0.2 Rev 2";
        %End
        """
    },
},
# ./kio/kfileitem.sip
"KFileItem":
{
    "__len__":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = sipCpp -> count();
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "__setitem__":
    {
        "code":
        """
        %MethodCode
            int len;
    
            len = sipCpp -> count();
    
            if ((a0 = sipConvertFromSequenceIndex(a0,len)) < 0)
                sipIsErr = 1;
            else
                (*sipCpp)[a0] = *(KFileItem *)a1;
        %End
        """
    },
    "__setitem__":
    {
        "code":
        """
        %MethodCode
            SIP_SSIZE_T len, start, stop, step, slicelength, i;
    
            len = sipCpp -> count();
    
            if (sipConvertFromSliceObject(a0,len,&start,&stop,&step,&slicelength) < 0)
                sipIsErr = 1;
            else
            {
                int vlen = a1 -> count();
                if (vlen != slicelength)
                {
                    sipBadLengthForSlice(vlen,slicelength);
                    sipIsErr = 1;
                }
                else
                {
                    KFileItemList::ConstIterator it = a1 -> begin();
                    for (i = 0; i < slicelength; ++i)
                    {
                        (*sipCpp)[start] = *it;
                        start += step;
                        ++it;
                    }
                }
            }
        %End
        """
    },
    "__delitem__":
    {
        "code":
        """
        %MethodCode
            int len;
    
            len = sipCpp -> count();
    
            if ((a0 = sipConvertFromSequenceIndex(a0,len)) < 0)
                sipIsErr = 1;
            else
                sipCpp -> removeAt ( a0);
        %End
        """
    },
    "__delitem__":
    {
        "code":
        """
        %MethodCode
            SIP_SSIZE_T len, start, stop, step, slicelength, i;
    
            len = sipCpp -> count();
            if (sipConvertFromSliceObject(a0,len,&start,&stop,&step,&slicelength) < 0)
                sipIsErr = 1;
            else
                for (i = 0; i < slicelength; ++i)
                {
                    sipCpp -> removeAt (start);
                    start += step - 1;
                }
        %End
        """
    },
    "[]":
    {
        "parameters": "KFileItem operator",
        "cxx_parameters": "[] (int)",
        "code":
        """
        %MethodCode
            int len;
    
            len = sipCpp->count();
    
            if ((a0 = (int)sipConvertFromSequenceIndex(a0, len)) < 0)
                sipIsErr = 1;
            else
                sipRes = new KFileItem((*sipCpp)[a0]);
        %End
        """
    },
    "[]":
    {
        "parameters": "KFileItemList operator",
        "cxx_parameters": "[] (SIP_PYSLICE)",
        "code":
        """
        %MethodCode
            SIP_SSIZE_T len, start, stop, step, slicelength, i;
    
            len = sipCpp->count();
    
            #if PY_VERSION_HEX >= 0x03020000
            if (PySlice_GetIndicesEx(a0, len, &start, &stop, &step, &slicelength) < 0)
            #else
            if (PySlice_GetIndicesEx((PySliceObject *)a0, len, &start, &stop, &step, &slicelength) < 0)
            #endif
                sipIsErr = 1;
            else
            {
                sipRes = new KFileItemList();
    
                for (i = 0; i < slicelength; ++i)
                {
                    (*sipRes) += (*sipCpp)[start];
                    start += step;
                }
            }
        %End
        """
    },
},
# ./solid/predicate.sip
"Predicate":
{
    "Predicate":
    {
        "parameters": "const Solid::DeviceInterface::Type ifaceType",
        "cxx_parameters": "const Solid::DeviceInterface::Type&",
        "cxx_fn_result": "void",
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipCpp = new Solid::Predicate (a0);
            Py_END_ALLOW_THREADS
        %End
        """
    },
},
# ./ktexteditor/movingrange.sip
"KTextEditor::MovingRange":
{
    "start":
    {
        "code":
        """
        %MethodCode
            // Returning a ref of this class is problematic.
            const KTextEditor::MovingCursor& cursor = sipCpp->start();
            sipRes = const_cast<KTextEditor::MovingCursor *>(&cursor);
        %End
        """
    },
    "end":
    {
        "code":
        """
        %MethodCode
            // Returning a ref of this class is problematic.
            const KTextEditor::MovingCursor& cursor = sipCpp->end();
            sipRes = const_cast<KTextEditor::MovingCursor *>(&cursor);
        %End
        """
    },
},
# ./ktexteditor/view.sip
"./ktexteditor/view.h":
{
    "codeCompletionInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::CodeCompletionInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "sessionConfigInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::SessionConfigInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "textHintInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::TextHintInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "annotationViewInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::AnnotationViewInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "configInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::ConfigInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "coordinatesToCursorInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::CoordinatesToCursorInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "templateInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::TemplateInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "templateInterface2":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::TemplateInterface2*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
},
# ./ktexteditor/editor.sip
"KTextEditor/ktexteditor/editor.h":
{
    "commandInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::CommandInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "containerInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::ContainerInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
},
# ./ktexteditor/document.sip
"KTextEditor::Document":
{
    "annotationInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::AnnotationInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "markInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::MarkInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "modificationInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::ModificationInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "searchInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::SearchInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "variableInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::VariableInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "movingInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::MovingInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "highlightInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::HighlightInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "configInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::ConfigInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "parameterizedSessionConfigInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::ParameterizedSessionConfigInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "sessionConfigInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::SessionConfigInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "recoveryInterface":
    {
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipRes = dynamic_cast<KTextEditor::RecoveryInterface*>(sipCpp);
            Py_END_ALLOW_THREADS
        %End
        """
    },
},
# ./kdeui/kapplication.sip
"/kdeui/kapplication.h":
{
    "KApplication":
    {
        "parameters": ["Display* display", "SIP_PYLIST list", "const QByteArray& rAppName", "bool GUIenabled = 1"],
        "cxx_parameters": ["Display*", "int&", "char**", "const QByteArray&", "bool = 1"],
        "cxx_fn_result": "void",
        "code":
        """
        %MethodCode
            // The Python interface is a list of argument strings that is modified.
    
            int argc;
            char **argv;
    
            // Convert the list.
            if ((argv = kdeui_ArgvToC(a1, argc)) == NULL)
                sipIsErr = 1;
            else
            {
                // Create it now the arguments are right.
                static int nargc;
                nargc = argc;
    
                Py_BEGIN_ALLOW_THREADS
                sipCpp = new sipKApplication(a0, nargc, argv, *a2, a3);
                Py_END_ALLOW_THREADS
    
                // Now modify the original list.
                kdeui_UpdatePyArgv(a1, argc, argv);
            }
        %End
        """
    },
},
# ./kdeui/kfontchooser.sip
# ./kdeui/kfontdialog.sip
"KFontChooser":
{
    "KFontChooser":
    {
        "parameters": ["QWidget* parent /TransferThis/ = 0", "const KFontChooser::DisplayFlags& flags = KFontChooser::DisplayFrame", "const QStringList& fontList = QStringList()", "int visibleListSize = 8", "Qt::CheckState* sizeIsRelativeState = 0"],
        "cxx_parameters": ["QWidget* = 0", "const KFontChooser::DisplayFlags& = KFontChooser::DisplayFrame", "const QStringList& = QStringList()", "int = 8", "Qt::CheckState* = 0"],
        "cxx_fn_result": "void",
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipCpp = new sipKFontChooser (a0, *a1, *a2, a3, &a4);
            Py_END_ALLOW_THREADS
        %End
        """
    },
},
# ./kdeui/kfontdialog.sip
"KFontDialog":
{
    "KFontDialog":
    {
        "parameters": ["QWidget* parent /TransferThis/ = 0", "const KFontChooser::DisplayFlags& flags = KFontChooser::NoDisplayFlags", "const QStringList& fontlist = QStringList()", "Qt::CheckState* sizeIsRelativeState = 0"],
        "cxx_parameters": ["QWidget* = 0", "const KFontChooser::DisplayFlags& = KFontChooser::NoDisplayFlags", "const QStringList& = QStringList()", "Qt::CheckState* = 0"],
        "cxx_fn_result": "void",
        "code":
        """
        %MethodCode
            Py_BEGIN_ALLOW_THREADS
            sipCpp= new sipKFontDialog (a0, *a1, *a2, &a3);
            Py_END_ALLOW_THREADS
        %End
        """
    },
    "getFont":
    {
        "parameters": ["QFont& theFont", "const KFontChooser::DisplayFlags& flags = KFontChooser::NoDisplayFlags", "QWidget* parent /Transfer/ = 0", "Qt::CheckState* sizeIsRelativeState = Qt::Unchecked"],
        "fn_result": "SIP_PYTUPLE",
        "cxx_parameters": ["QFont&", "const KFontChooser::DisplayFlags& = KFontChooser::NoDisplayFlags", "QWidget* = 0", "Qt::CheckState* = 0"],
        "cxx_fn_result": "int",
        "code":
        """
        %MethodCode
            int result;
            Py_BEGIN_ALLOW_THREADS
            result = KFontDialog::getFont (*a0, *a1, a2, &a3);
            Py_END_ALLOW_THREADS
            #if PY_MAJOR_VERSION >= 3
            sipRes = PyLong_FromLong (result);
            #else
            sipRes = PyInt_FromLong (result);
            #endif
        %End
        """
    },
    "getFontDiff":
    {
        "parameters": ["QFont& theFont", "KFontChooser::FontDiffFlags& diffFlags", "const KFontChooser::DisplayFlags& flags = KFontChooser::NoDisplayFlags", "QWidget* parent /Transfer/ = 0", "Qt::CheckState sizeIsRelativeState = Qt::Unchecked"],
        "fn_result": "SIP_PYTUPLE",
        "cxx_parameters": ["QFont&", "KFontChooser::FontDiffFlags&", "const KFontChooser::DisplayFlags& = KFontChooser::NoDisplayFlags", "QWidget* = 0", "Qt::CheckState* = 0"],
        "cxx_fn_result": "int",
        "code":
        """
        %MethodCode
            int result;
            Py_BEGIN_ALLOW_THREADS
            result = KFontDialog::getFontDiff (*a0, *a1, *a2, a3, &a4);
            Py_END_ALLOW_THREADS
    
            #if PY_MAJOR_VERSION >= 3
            sipRes = PyLong_FromLong (result);
            #else
            sipRes = PyInt_FromLong (result);
            #endif
        %End
        """
    },
    "getFontAndText":
    {
        "parameters": ["QFont& theFont", "QString& theString", "const KFontChooser::DisplayFlags& flags = KFontChooser::NoDisplayFlags", "QWidget* parent /Transfer/ = 0", "Qt::CheckState sizeIsRelativeState = Qt::Unchecked"],
        "fn_result": "SIP_PYTUPLE",
        "cxx_parameters": ["QFont&", "QString&", "const KFontChooser::DisplayFlags& = KFontChooser::NoDisplayFlags", "QWidget* = 0", "Qt::CheckState* = 0"],
        "cxx_fn_result": "int",
        "code":
        """
        %MethodCode
            int result;
            Py_BEGIN_ALLOW_THREADS
            result = KFontDialog::getFontAndText (*a0, *a1, *a2, a3, &a4);
            Py_END_ALLOW_THREADS
    
            #if PY_MAJOR_VERSION >= 3
            sipRes = PyLong_FromLong (result);
            #else
            sipRes = PyInt_FromLong (result);
            #endif
        %End
        """
    },
},
}
