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
SIP binding customisation for PyKF5.KIOCore, PyKF5.KIOFileWidgets,
PyKF5.KIOGui PyKF5.KIOWidgets PyKF5.kio. This modules describes:

    * Supplementary SIP file generator rules.
"""

from clang.cindex import TokenKind, TypeKind

import rule_helpers


def _container_discard_templated_bases_and_fake(container, sip, matcher):
    rule_helpers.container_discard_templated_bases(container, sip, matcher)
    rule_helpers.container_fake_derived_class(container, sip, matcher)


def _function_rewrite_using_decl1(container, function, sip, matcher):
    sip["parameters"] = ["const QByteArray &data"]
    sip["fn_result"] = "virtual void"


def _function_rewrite_using_decl2(container, function, sip, matcher):
    sip["parameters"] = ["KIO::filesize_t size"]
    sip["fn_result"] = "virtual void"


def variable_rewrite_array(container, variable, sip, matcher):
    base_type, indices = sip["decl"].split("[", 1)
    indices = "[" + indices
    #
    # If all the indices are empty, as in [][][], then just convert to ***.
    #
    if indices == "[]":
        sip["decl"] = base_type + "*"
        return
    #
    # We only handle simple 1D arrays of byte values.
    #
    if variable.type.kind != TypeKind.CONSTANTARRAY:
        return
    element_type = variable.type.element_type.get_canonical()
    if element_type.kind in [TypeKind.CHAR_S, TypeKind.CHAR_U, TypeKind.SCHAR, TypeKind.UCHAR]:
        sip["decl"] = "SIP_PYBUFFER"
        code = """
{
%GetCode
    char *cxxvalue = (char *)&sipCpp->{name}[0];

    // Create the Python buffer.
    Py_ssize_t element_count = {element_count};
    sipPy = PyByteArray_FromStringAndSize(cxxvalue, element_count);
%End

%SetCode
    char *cxxvalue = (char *)&sipCpp->{name}[0];
    Py_ssize_t element_count = {element_count};
    const char *name = "{name}";

    if (!PyByteArray_Check(sipPy)) {
        PyErr_Format(PyExc_TypeError, "expected buffer");
        sipErr = 1;
    }

    // Convert the buffer to C++.
    if (!sipErr) {
        if (PyByteArray_GET_SIZE(sipPy) != element_count) {
            PyErr_Format(PyExc_ValueError, "'%s' must have length %ld", name, element_count);
            sipErr = 1;
        } else {
            memcpy(cxxvalue, PyByteArray_AsString(sipPy), element_count);
        }
    }
%End
}"""
    elif element_type.kind in [TypeKind.USHORT, TypeKind.UINT, TypeKind.ULONG, TypeKind.ULONGLONG, TypeKind.UINT128,
                               TypeKind.SHORT, TypeKind.INT, TypeKind.LONG, TypeKind.LONGLONG, TypeKind.INT128,
                               TypeKind.ENUM]:
        sip["decl"] = base_type + "*"
        sip["decl"] = "SIP_PYTUPLE"
        code = """
{
%GetCode
    typedef {cxx_t} CxxvalueT;
    CxxvalueT *cxxvalue = (CxxvalueT *)&sipCpp->{name}[0];
    Py_ssize_t element_count = {element_count};
    int sipErr = 0;

    // Create the Python tuple.
    PyObject *tuple = PyTuple_New(element_count);
    if (!tuple) {
        PyErr_Format(PyExc_TypeError, "unable to create a tuple");
        sipErr = 1;
    }

    // Populate the tuple elements.
    if (!sipErr) {
        Py_ssize_t i = 0;
        for (i = 0; i < element_count; ++i) {
#if PY_MAJOR_VERSION >= 3
            PyObject *value = PyLong_FromLong((long)cxxvalue[i]);
#else
            PyObject *value = PyInt_FromLong((long)cxxvalue[i]);
#endif
            if (value == NULL) {
                PyErr_Format(PyExc_TypeError, "cannot insert value into tuple");
                Py_XDECREF(value);
                Py_DECREF(tuple);
                sipErr = 1;
            } else {
                PyTuple_SET_ITEM(tuple, i, value);
            }
        }
    }
    sipPy = sipErr ? tuple : NULL;
%End

%SetCode
    typedef {cxx_t} CxxvalueT;
    CxxvalueT *cxxvalue = (CxxvalueT *)&sipCpp->{name}[0];
    Py_ssize_t element_count = {element_count};
    const char *name = "{name}";

    if (!PyTuple_Check(sipPy)) {
        PyErr_Format(PyExc_TypeError, "expected tuple");
        sipErr = 1;
    }

    // Convert the tuple to C++.
    if (!sipErr) {
        if (PyTuple_GET_SIZE(sipPy) != element_count) {
            PyErr_Format(PyExc_ValueError, "'%s' must have length %ld", name, element_count);
            sipErr = 1;
        } else {
            Py_ssize_t i = 0;
            for (i = 0; i < element_count; ++i) {
                PyObject *value = PyTuple_GetItem(sipPy, i);
#if PY_MAJOR_VERSION >= 3
                cxxvalue[i] = (CxxvalueT)PyLong_AsLong(value);
#else
                cxxvalue[i] = (CxxvalueT)PyInt_AsLong(value);
#endif
            }
        }
    }
%End
}"""
    else:
        return
    code = code.replace("{cxx_t}", element_type.spelling)
    code = code.replace("{element_count}", str(variable.type.element_count))
    code = code.replace("{name}", sip["name"])
    sip["code"] = code


def variable_fully_qualify(container, variable, sip, matcher):
    sip["decl"] = "KNTLM::" + sip["decl"]


def module_fix_kiomod(filename, sip, matcher):
    """
    Note: there are multiple KIOmod.sip and one kiomod.sip files, and this has to deal with all of them. Yuck.
    """
    #
    # Fixup the recursion.
    #
    lines = []
    for l in sip["decl"].split("\n"):
        if "KIOCore/KIOCoremod.sip" in l or "KIOCore/KIO/KIOmod.sip" in l:
            #
            # These modules refer to each other.
            #
            lines.append("// " + l)
            continue
        lines.append(l)
    sip["decl"] = "\n".join(lines)
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    if sip["name"] == "KIOCore.kio":
        rule_helpers.modulecode_delete(filename, sip, matcher, "QMap<QString, QString>")
        sip["code"] = """
%If (!KIOCore_kio_kiomod)
class KIO::JobUiDelegateExtension /External/;
class KIO::MetaData /External/;
%End
"""
    elif sip["name"] == "KIOCore.KIO":
        rule_helpers.modulecode_delete(filename, sip, matcher, "QList<QUrl>", "QMap<QString, QString>",
                                       "QVector<unsigned int>")
        rule_helpers.modulecode_make_local(filename, sip, matcher, "QMap<QString, QVariant>")
        sip["code"] = """
%Import(name=KIOCore/kio/kiomod.sip)
class KIO::Connection;
class KIO::ClipboardUpdater;
%If (!KIOCore_KIO_KIOmod)
class KConfigGroup /External/;
class KFileItemList /External/;
class KService /External/;
class KRemoteEncoding /External/;
class QDBusArgument /External/;
%End
"""
    elif sip["name"] == "KIOGui.KIO":
        sip["code"] = """
%Import(name=KIOCore/kio/kiomod.sip)
%Import(name=KIOCore/KIO/KIOmod.sip)
%Import(name=KIOCore/KIOCoremod.sip)
%If (!KIOGui_KIO_KIOmod)
class KService;
%End
"""
    elif sip["name"] == "KIOWidgets.KIO":
        rule_helpers.modulecode_delete(filename, sip, matcher, "QList<QAction *>")
        sip["code"] = """
%Import(name=KIOCore/kio/kiomod.sip)
%Import(name=KIOCore/KIO/KIOmod.sip)
%Import(name=KIOCore/KIOCoremod.sip)
%If (!KIOWidgets_KIO_KIOmod)
class KService;
class KPixmapSequence;
%End
"""


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_make_local(filename, sip, entry, "QList<QPair<QString, unsigned short> >")
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<QUrl>")
    #
    # Random stuff.
    #
    sip["code"] = """
%If (!KIOCore_KIOCoremod)
class KService;
class KSslCertificateBoxPrivate;
%End
"""


def module_fix_mapped_types_filewidgets(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<QModelIndex>", "QList<QUrl>", "QVector<int>")


def module_fix_mapped_types_widgets(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QList<QSslCertificate>", "QList<KServiceAction>",
                                   "QList<QAction *>", "QExplicitlySharedDataPointer<KService>",
                                   "QList<QExplicitlySharedDataPointer<KService> >")
    rule_helpers.modulecode_make_local(filename, sip, entry, "QList<QModelIndex>")
    sip["code"] = """
%If (!KIOWidgets_KIOWidgetsmod)
class KCModule;
class KSslCertificateBoxPrivate;
%End
"""


def container_rules():
    return [
        ["kfileitem.h", "KFileItemList", ".*", ".*", ".*", _container_discard_templated_bases_and_fake],
        ["kmountpoint.h", "KMountPoint", ".*", ".*", ".*QSharedData.*", rule_helpers.container_discard_QSharedData_base],
        ["KIO", "MetaData", ".*", ".*", ".*", _container_discard_templated_bases_and_fake],
        ["KIO", "DesktopExecParser", ".*", ".*", ".*", rule_helpers.container_fake_derived_class],
    ]


def function_rules():
    return [
        #
        # Remove some inlined stuff.
        #
        ["udsentry.h", "debugUDSEntry", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Privates...
        #
        ["KIO::EmptyTrashJob", "EmptyTrashJob", ".*", ".*", ".*Private.*", rule_helpers.function_discard],
        ["KIO::FileSystemFreeSpaceJob", "FileSystemFreeSpaceJob", ".*", ".*", ".*Private.*", rule_helpers.function_discard],
        ["KIO::MkdirJob", "MkdirJob", ".*", ".*", ".*Private.*", rule_helpers.function_discard],
        #
        # Duplicate signatures.
        #
        ["KIO::StatJob", "setSide", ".*", ".*", ".*bool.*", rule_helpers.function_discard],
        ["KFileItem", "mostLocalUrl", ".*", ".*", ".*local", rule_helpers.function_discard],
        #
        # Missing stat64.
        #
        ["KIO::UDSEntry", "UDSEntry", ".*", ".*", ".*stat64.*", rule_helpers.function_discard],
        #
        # Rewrite using declaration.
        #
        ["KIO::TCPSlaveBase", "write", ".*", ".*", "", _function_rewrite_using_decl1],
        ["KIO::TCPSlaveBase", "read", ".*", ".*", "", _function_rewrite_using_decl2],
        #
        # Deleted functions.
        #
        ["KIO", "file_(copy|move)", ".*", ".*", ".*flags", rule_helpers.function_discard],
    ]


def typedef_rules():
    return [
        #
        # Remove some useless stuff.
        #
        ["kacl.h", "ACL.*PermissionsIterator|ACL.*PermissionsConstIterator", ".*", ".*", rule_helpers.typedef_discard],
        ["kprotocolmanager.h", "KSharedConfigPtr", ".*", ".*", rule_helpers.typedef_discard],
        ["thumb.*creator.h", "newCreator", ".*", ".*", rule_helpers.typedef_discard],
    ]


def variable_rules():
    return [
        #
        # Emit code for fixed arrays.
        #
        ["KNTLM::.*", ".*", ".*\[.+\]", variable_rewrite_array],
        #
        # Fully-qualify.
        #
        ["KNTLM::.*", ".*", "SecBuf.*", variable_fully_qualify],
    ]


def modulecode():
    return {
        "KIOCoremod.sip": {
            "code": module_fix_mapped_types,
        },
        "KIOmod.sip": {
            "code": module_fix_kiomod,
        },
        "kiomod.sip": {
            "code": module_fix_kiomod,
        },
        "KIOWidgetsmod.sip": {
            "code": module_fix_mapped_types_widgets,
        },
        "KIOFileWidgetsmod.sip": {
            "code": module_fix_mapped_types_filewidgets,
        },
    }


def typecode():
    return {
        # DISABLED until I figure out an approach for CTSCC.
        "DISABLED kprotocolinfo.h::KProtocolInfo": {  # KProtocolInfo : KSycocaEntry
            "code":
                """
                %ConvertToSubClassCode
                    // CTSCC for subclasses of 'KSycocaEntry'
                    sipType = NULL;
        
                    if (dynamic_cast<KProtocolInfo*>(sipCpp))
                        sipType = sipType_KProtocolInfo;
                    else if (dynamic_cast<KService*>(sipCpp))
                        sipType = sipType_KService;
                    else if (dynamic_cast<KServiceGroup*>(sipCpp))
                        sipType = sipType_KServiceGroup;
                    else if (dynamic_cast<KServiceType*>(sipCpp))
                        {
                        sipType = sipType_KServiceType;
                        if (dynamic_cast<KMimeType*>(sipCpp))
                            sipType = sipType_KMimeType;
                        }
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
