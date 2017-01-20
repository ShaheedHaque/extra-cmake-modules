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
SIP binding customisation for PyKF5.KIOCore. This modules describes:

    * Supplementary SIP file generator rules.
"""

from clang.cindex import TokenKind

import rules_engine


def _container_delete_base(container, sip, matcher):
    sip["base_specifiers"] = []


def fn_remove_inlined(container, function, sip, matcher):
    for token in function.get_tokens():
        if token.kind != TokenKind.KEYWORD:
            return
        if token.spelling == "inline":
            rules_engine.function_discard(container, function, sip, matcher)
            return


def module_fix_imports(filename, sip, matcher):
    lines = []
    for l in sip["decl"].split("\n"):
        if "name=KIOCore/KIOCoremod.sip" in l:
            #
            # These modules refer to each other.
            #
            lines.append("%If (!KIOCore_KIO_KIOmod)")
            lines.append(l)
            lines.append("%End")
            continue
        lines.append(l)
    sip["decl"] = "\n".join(lines)


def container_rules():
    return [
        #
        # SIP cannot handle inline templates like "class Foo: Bar<Baz>" without an intermediate typedef. For now,
        # delete the base class.
        #
        ["kfileitem.h", "KFileItemList", ".*", ".*", ".*", _container_delete_base],
        ["KMountPoint", "List", ".*", ".*", ".*", _container_delete_base],
        ["KIO", "MetaData", ".*", ".*", ".*", _container_delete_base],
    ]


def function_rules():
    return [
        #
        # Remove some inlined stuff.
        #
        ["KIO::MetaData", "MetaData|operator\\+=|toVariant", ".*", ".*", ".*", fn_remove_inlined],
    ]


def typedef_rules():
    return [
        #
        # Remove some useless stuff.
        #
        ["kacl.h", "ACL.*PermissionsIterator|ACL.*PermissionsConstIterator", ".*", ".*", rules_engine.typedef_discard],
    ]


def modulecode():
    return {
        "KIOCoremod.sip": {
            "code": module_fix_imports,
        },
        "KIOmod.sip": {
            "code": module_fix_imports,
        }
    }


def typecode():
    return {
        # ./kio/kacl.sip
        "kacl.h::ACLUserPermissionsList": {  # ACLUserPermissionsList
            "code":
                """
                %ConvertFromTypeCode
                    if (!sipCpp)
                        return PyList_New(0);

                    // Create the list
                    PyObject *pylist;
                    if ((pylist = PyList_New(0)) == NULL)
                        return NULL;

                    QList<QPair<QString, unsigned short> > *cpplist = (QList<QPair<QString, unsigned short> > *)sipCpp;
                    PyObject *inst = NULL;

                    // Get it.
                    QList<QPair<QString, unsigned short> >::Iterator it;
                    for( it = cpplist->begin(); it != cpplist->end(); ++it )
                    {
                        QString s = (*it).first;
                        ushort  u = (*it).second;
                        PyObject *pys = sipBuildResult (NULL, "N", new QString (s), sipType_QString);
                        if ((pys == NULL) || ((inst = Py_BuildValue ("Ni", pys, u)) == NULL)
                            || PyList_Append (pylist, inst) < 0)
                        {
                            Py_XDECREF (inst);
                            Py_XDECREF (pys);
                            Py_DECREF (pylist);
                            return NULL;
                        }
                    }

                    return pylist;
                %End
                %ConvertToTypeCode
                    if (sipIsErr == NULL)
                        return PyList_Check(sipPy);

                    QList<QPair<QString, unsigned short> > *cpplist = new QList<QPair<QString, unsigned short> >;

                    QString p1;
                    int iserr = 0;

                    for (int i = 0; i < PyList_Size (sipPy); i++)
                    {
                        PyObject *elem = PyList_GET_ITEM (sipPy, i);
                        PyObject *pyp1 = PyTuple_GET_ITEM (elem, 0);
                        p1 = *(QString *)sipForceConvertToType(pyp1, sipType_QString, NULL, 0, NULL, &iserr);
                        if (iserr)
                        {
                            *sipIsErr = 1;
                            delete cpplist;
                            return 0;
                        }
                #if PY_MAJOR_VERSION >= 3
                        ushort p2 = (ushort)(PyLong_AsLong (PyTuple_GET_ITEM (elem, 1)));
                #else
                        ushort p2 = (ushort)(PyInt_AS_LONG (PyTuple_GET_ITEM (elem, 1)));
                #endif
                        cpplist->append (QPair<QString, unsigned short> (p1, p2));
                    }

                    *sipCppPtr = cpplist;

                    return 1;
                %End
                """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED KIO::TCPSlaveBase": {  # TCPSlaveBase : KIO::SlaveBase
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'SlaveBase'
                    sipType = NULL;

                    if (dynamic_cast<KIO::ForwardingSlaveBase*>(sipCpp))
                        sipType = sipType_KIO_ForwardingSlaveBase;
                    else if (dynamic_cast<KIO::TCPSlaveBase*>(sipCpp))
                        sipType = sipType_KIO_TCPSlaveBase;
                %End
                """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED karchivedirectory.h::KArchiveDirectory": {  # KArchiveDirectory : KArchiveEntry
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'KArchiveEntry'
                    sipType = NULL;

                    if (dynamic_cast<KArchiveDirectory*>(sipCpp))
                        sipType = sipType_KArchiveDirectory;
                    else if (dynamic_cast<KArchiveFile*>(sipCpp))
                        {
                        sipType = sipType_KArchiveFile;
                        if (dynamic_cast<KZipFileEntry*>(sipCpp))
                            sipType = sipType_KZipFileEntry;
                        }
                %End
                """
        },
        # ./kio/kimagefilepreview.sip
        "kimagefilepreview.h::KImageFilePreview": {  # KImageFilePreview : KPreviewWidgetBase
            "code":
                """
                %TypeHeaderCode
                #include <kimagefilepreview.h>
                #include <jobclasses.h>
                %End
                """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED KIO::AccessManager": {  # AccessManager : QNetworkAccessManager
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'AccessManager'
                    sipType = NULL;

                    if (dynamic_cast<KIO::AccessManager*>(sipCpp))
                        sipType = sipType_KIO_AccessManager;
                %End
                """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED KIO::Integration::CookieJar": {  # CookieJar : QNetworkCookieJar
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'CookieJar'
                    sipType = NULL;

                    if (dynamic_cast<KIO::Integration::CookieJar*>(sipCpp))
                        sipType = sipType_KIO_Integration_CookieJar;
                %End
                """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kar.h::KAr": {  # KAr : KArchive
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'KArchive'
                    sipType = NULL;

                    if (dynamic_cast<KAr*>(sipCpp))
                        sipType = sipType_KAr;
                    else if (dynamic_cast<KTar*>(sipCpp))
                        sipType = sipType_KTar;
                    else if (dynamic_cast<KZip*>(sipCpp))
                        sipType = sipType_KZip;
                %End
                """
        },
        # ./kio/metainfojob.sip
        "MetaInfoJob": {  # MetaInfoJob : KIO::Job
            "code":
                """
                %TypeHeaderCode
                #include <metainfojob.h>
                #include <kfileitem.h>
                #include <jobclasses.h>
                %End
                """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED thumbcreator.h::ThumbCreator": {  # ThumbCreator
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'ThumbCreator'
                    sipType = NULL;

                    if (dynamic_cast<ThumbCreatorV2*>(sipCpp))
                        sipType = sipType_ThumbCreatorV2;
                    else if (dynamic_cast<ThumbSequenceCreator*>(sipCpp))
                        sipType = sipType_ThumbSequenceCreator;
                %End
                """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kurlpixmapprovider.h::KUrlPixmapProvider": {  # KUrlPixmapProvider : KPixmapProvider
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'KPixmapProvider'
                    sipType = NULL;

                    if (dynamic_cast<KUrlPixmapProvider*>(sipCpp))
                        sipType = sipType_KUrlPixmapProvider;
                %End
                """
        },
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED KAbstractFileModule": {  # KAbstractFileModule : QObject
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'QObject'
                    sipType = NULL;

                    if (dynamic_cast<KAbstractFileItemActionPlugin*>(sipCpp))
                        sipType = sipType_KAbstractFileItemActionPlugin;
                    else if (dynamic_cast<KAbstractFileModule*>(sipCpp))
                        sipType = sipType_KAbstractFileModule;
                    else if (dynamic_cast<KAutoMount*>(sipCpp))
                        sipType = sipType_KAutoMount;
                    else if (dynamic_cast<KAutoUnmount*>(sipCpp))
                        sipType = sipType_KAutoUnmount;
                    else if (dynamic_cast<KBookmarkDomBuilder*>(sipCpp))
                        sipType = sipType_KBookmarkDomBuilder;
                    else if (dynamic_cast<KBookmarkImporterBase*>(sipCpp))
                        {
                        sipType = sipType_KBookmarkImporterBase;
                        if (dynamic_cast<KCrashBookmarkImporterImpl*>(sipCpp))
                            sipType = sipType_KCrashBookmarkImporterImpl;
                        else if (dynamic_cast<KIEBookmarkImporterImpl*>(sipCpp))
                            sipType = sipType_KIEBookmarkImporterImpl;
                        else if (dynamic_cast<KNSBookmarkImporterImpl*>(sipCpp))
                            {
                            sipType = sipType_KNSBookmarkImporterImpl;
                            if (dynamic_cast<KMozillaBookmarkImporterImpl*>(sipCpp))
                                sipType = sipType_KMozillaBookmarkImporterImpl;
                            }
                        else if (dynamic_cast<KOperaBookmarkImporterImpl*>(sipCpp))
                            sipType = sipType_KOperaBookmarkImporterImpl;
                        else if (dynamic_cast<KXBELBookmarkImporterImpl*>(sipCpp))
                            sipType = sipType_KXBELBookmarkImporterImpl;
                        }
                    else if (dynamic_cast<KBookmarkManager*>(sipCpp))
                        sipType = sipType_KBookmarkManager;
                    else if (dynamic_cast<KBookmarkMenu*>(sipCpp))
                        {
                        sipType = sipType_KBookmarkMenu;
                        if (dynamic_cast<KonqBookmarkMenu*>(sipCpp))
                            sipType = sipType_KonqBookmarkMenu;
                        }
                    else if (dynamic_cast<KUrlCompletion*>(sipCpp))
                        {
                        sipType = sipType_KUrlCompletion;
                        if (dynamic_cast<KShellCompletion*>(sipCpp))
                            sipType = sipType_KShellCompletion;
                        }
                    else if (dynamic_cast<KCrashBookmarkImporter*>(sipCpp))
                        sipType = sipType_KCrashBookmarkImporter;
                    else if (dynamic_cast<KDataTool*>(sipCpp))
                        sipType = sipType_KDataTool;
                    else if (dynamic_cast<KDirLister*>(sipCpp))
                        sipType = sipType_KDirLister;
                    else if (dynamic_cast<KDirWatch*>(sipCpp))
                        sipType = sipType_KDirWatch;
                    else if (dynamic_cast<KDiskFreeSpace*>(sipCpp))
                        sipType = sipType_KDiskFreeSpace;
                    else if (dynamic_cast<KFileItemActionPlugin*>(sipCpp))
                        sipType = sipType_KFileItemActionPlugin;
                    else if (dynamic_cast<KFileItemActions*>(sipCpp))
                        sipType = sipType_KFileItemActions;
                    else if (dynamic_cast<KFilePreviewGenerator*>(sipCpp))
                        sipType = sipType_KFilePreviewGenerator;
                    else if (dynamic_cast<KFileWritePlugin*>(sipCpp))
                        sipType = sipType_KFileWritePlugin;
                    else if (dynamic_cast<KIO::Connection*>(sipCpp))
                        sipType = sipType_KIO_Connection;
                    else if (dynamic_cast<KIO::ConnectionServer*>(sipCpp))
                        sipType = sipType_KIO_ConnectionServer;
                    else if (dynamic_cast<KIO::FileUndoManager*>(sipCpp))
                        sipType = sipType_KIO_FileUndoManager;
                    else if (dynamic_cast<KIO::ForwardingSlaveBase*>(sipCpp))
                        sipType = sipType_KIO_ForwardingSlaveBase;
                    else if (dynamic_cast<KIO::NetAccess*>(sipCpp))
                        sipType = sipType_KIO_NetAccess;
                    else if (dynamic_cast<KIO::Scheduler*>(sipCpp))
                        sipType = sipType_KIO_Scheduler;
                    else if (dynamic_cast<KIO::SessionData*>(sipCpp))
                        sipType = sipType_KIO_SessionData;
                    else if (dynamic_cast<KIO::SlaveConfig*>(sipCpp))
                        sipType = sipType_KIO_SlaveConfig;
                    else if (dynamic_cast<KIO::SlaveInterface*>(sipCpp))
                        {
                        sipType = sipType_KIO_SlaveInterface;
                        if (dynamic_cast<KIO::Slave*>(sipCpp))
                            sipType = sipType_KIO_Slave;
                        }
                    else if (dynamic_cast<KIO::Job*>(sipCpp))
                        {
                        sipType = sipType_KIO_Job;
                        if (dynamic_cast<KIO::ChmodJob*>(sipCpp))
                            sipType = sipType_KIO_ChmodJob;
                        else if (dynamic_cast<KIO::CopyJob*>(sipCpp))
                            sipType = sipType_KIO_CopyJob;
                        else if (dynamic_cast<KIO::DeleteJob*>(sipCpp))
                            sipType = sipType_KIO_DeleteJob;
                        else if (dynamic_cast<KIO::DirectorySizeJob*>(sipCpp))
                            sipType = sipType_KIO_DirectorySizeJob;
                        else if (dynamic_cast<KIO::FileCopyJob*>(sipCpp))
                            sipType = sipType_KIO_FileCopyJob;
                        else if (dynamic_cast<KIO::MetaInfoJob*>(sipCpp))
                            sipType = sipType_KIO_MetaInfoJob;
                        else if (dynamic_cast<KIO::PreviewJob*>(sipCpp))
                            sipType = sipType_KIO_PreviewJob;
                        else if (dynamic_cast<KIO::SimpleJob*>(sipCpp))
                            {
                            sipType = sipType_KIO_SimpleJob;
                            if (dynamic_cast<KIO::FileJob*>(sipCpp))
                                sipType = sipType_KIO_FileJob;
                            else if (dynamic_cast<KIO::ListJob*>(sipCpp))
                                sipType = sipType_KIO_ListJob;
                            else if (dynamic_cast<KIO::StatJob*>(sipCpp))
                                sipType = sipType_KIO_StatJob;
                            else if (dynamic_cast<KIO::TransferJob*>(sipCpp))
                                {
                                sipType = sipType_KIO_TransferJob;
                                if (dynamic_cast<KIO::DavJob*>(sipCpp))
                                    sipType = sipType_KIO_DavJob;
                                else if (dynamic_cast<KIO::MimetypeJob*>(sipCpp))
                                    sipType = sipType_KIO_MimetypeJob;
                                else if (dynamic_cast<KIO::MultiGetJob*>(sipCpp))
                                    sipType = sipType_KIO_MultiGetJob;
                                else if (dynamic_cast<KIO::SpecialJob*>(sipCpp))
                                    sipType = sipType_KIO_SpecialJob;
                                else if (dynamic_cast<KIO::StoredTransferJob*>(sipCpp))
                                    sipType = sipType_KIO_StoredTransferJob;
                                }
                            }
                        }
                    else if (dynamic_cast<KIO::JobUiDelegate*>(sipCpp))
                        sipType = sipType_KIO_JobUiDelegate;
                    else if (dynamic_cast<KNFSShare*>(sipCpp))
                        sipType = sipType_KNFSShare;
                    else if (dynamic_cast<KPropertiesDialogPlugin*>(sipCpp))
                        {
                        sipType = sipType_KPropertiesDialogPlugin;
                        if (dynamic_cast<KFileSharePropsPlugin*>(sipCpp))
                            sipType = sipType_KFileSharePropsPlugin;
                        }
                    else if (dynamic_cast<KRun*>(sipCpp))
                        sipType = sipType_KRun;
                    else if (dynamic_cast<KSambaShare*>(sipCpp))
                        sipType = sipType_KSambaShare;
                    else if (dynamic_cast<KUriFilterPlugin*>(sipCpp))
                        sipType = sipType_KUriFilterPlugin;
                    else if (dynamic_cast<KFileItemDelegate*>(sipCpp))
                        sipType = sipType_KFileItemDelegate;
                    else if (dynamic_cast<KDeviceListModel*>(sipCpp))
                        sipType = sipType_KDeviceListModel;
                    else if (dynamic_cast<KDirModel*>(sipCpp))
                        sipType = sipType_KDirModel;
                    else if (dynamic_cast<KFilePlacesModel*>(sipCpp))
                        sipType = sipType_KFilePlacesModel;
                    else if (dynamic_cast<KDirSortFilterProxyModel*>(sipCpp))
                        sipType = sipType_KDirSortFilterProxyModel;
                    else if (dynamic_cast<KBookmarkActionMenu*>(sipCpp))
                        sipType = sipType_KBookmarkActionMenu;
                    else if (dynamic_cast<KNewFileMenu*>(sipCpp))
                        sipType = sipType_KNewFileMenu;
                    else if (dynamic_cast<KBookmarkAction*>(sipCpp))
                        sipType = sipType_KBookmarkAction;
                    else if (dynamic_cast<KDataToolAction*>(sipCpp))
                        sipType = sipType_KDataToolAction;
                    else if (dynamic_cast<KDirOperator*>(sipCpp))
                        sipType = sipType_KDirOperator;
                    else if (dynamic_cast<KFileMetaDataConfigurationWidget*>(sipCpp))
                        sipType = sipType_KFileMetaDataConfigurationWidget;
                    else if (dynamic_cast<KFileMetaDataWidget*>(sipCpp))
                        sipType = sipType_KFileMetaDataWidget;
                    else if (dynamic_cast<KFileWidget*>(sipCpp))
                        sipType = sipType_KFileWidget;
                    else if (dynamic_cast<KIO::RenameDialogPlugin*>(sipCpp))
                        sipType = sipType_KIO_RenameDialogPlugin;
                    else if (dynamic_cast<KPreviewWidgetBase*>(sipCpp))
                        {
                        sipType = sipType_KPreviewWidgetBase;
                        if (dynamic_cast<KImageFilePreview*>(sipCpp))
                            sipType = sipType_KImageFilePreview;
                        }
                    else if (dynamic_cast<KStatusBarOfflineIndicator*>(sipCpp))
                        sipType = sipType_KStatusBarOfflineIndicator;
                    else if (dynamic_cast<KUrlNavigator*>(sipCpp))
                        sipType = sipType_KUrlNavigator;
                    else if (dynamic_cast<KIconButton*>(sipCpp))
                        sipType = sipType_KIconButton;
                    else if (dynamic_cast<KFileFilterCombo*>(sipCpp))
                        sipType = sipType_KFileFilterCombo;
                    else if (dynamic_cast<KUrlComboBox*>(sipCpp))
                        sipType = sipType_KUrlComboBox;
                    else if (dynamic_cast<KBookmarkDialog*>(sipCpp))
                        sipType = sipType_KBookmarkDialog;
                    else if (dynamic_cast<KDirSelectDialog*>(sipCpp))
                        sipType = sipType_KDirSelectDialog;
                    else if (dynamic_cast<KFileDialog*>(sipCpp))
                        {
                        sipType = sipType_KFileDialog;
                        if (dynamic_cast<KEncodingFileDialog*>(sipCpp))
                            sipType = sipType_KEncodingFileDialog;
                        }
                    else if (dynamic_cast<KIO::SkipDialog*>(sipCpp))
                        sipType = sipType_KIO_SkipDialog;
                    else if (dynamic_cast<KIconDialog*>(sipCpp))
                        sipType = sipType_KIconDialog;
                    else if (dynamic_cast<KMimeTypeChooserDialog*>(sipCpp))
                        sipType = sipType_KMimeTypeChooserDialog;
                    else if (dynamic_cast<KNameAndUrlInputDialog*>(sipCpp))
                        sipType = sipType_KNameAndUrlInputDialog;
                    else if (dynamic_cast<KOpenWithDialog*>(sipCpp))
                        sipType = sipType_KOpenWithDialog;
                    else if (dynamic_cast<KOCRDialog*>(sipCpp))
                        sipType = sipType_KOCRDialog;
                    else if (dynamic_cast<KPropertiesDialog*>(sipCpp))
                        sipType = sipType_KPropertiesDialog;
                    else if (dynamic_cast<KScanDialog*>(sipCpp))
                        sipType = sipType_KScanDialog;
                    else if (dynamic_cast<KIO::PasswordDialog*>(sipCpp))
                        sipType = sipType_KIO_PasswordDialog;
                    else if (dynamic_cast<KUrlRequesterDialog*>(sipCpp))
                        sipType = sipType_KUrlRequesterDialog;
                    else if (dynamic_cast<KIO::RenameDialog*>(sipCpp))
                        sipType = sipType_KIO_RenameDialog;
                    else if (dynamic_cast<KBuildSycocaProgressDialog*>(sipCpp))
                        sipType = sipType_KBuildSycocaProgressDialog;
                    else if (dynamic_cast<KUrlRequester*>(sipCpp))
                        {
                        sipType = sipType_KUrlRequester;
                        if (dynamic_cast<KUrlComboRequester*>(sipCpp))
                            sipType = sipType_KUrlComboRequester;
                        }
                    else if (dynamic_cast<KMimeTypeChooser*>(sipCpp))
                        sipType = sipType_KMimeTypeChooser;
                    else if (dynamic_cast<KFilePlacesView*>(sipCpp))
                        sipType = sipType_KFilePlacesView;
                    else if (dynamic_cast<KIconCanvas*>(sipCpp))
                        sipType = sipType_KIconCanvas;
                    else if (dynamic_cast<KBookmarkContextMenu*>(sipCpp))
                        sipType = sipType_KBookmarkContextMenu;
                %End
                """
        },
    }
