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
SIP binding custom type-related code for PyKF5.
"""

from builtin_rules import HeldAs
from templates.PyQt import list_typecode


_kdeui_qobject_ctscc = """
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QObject'
    sipType = NULL;

    if (dynamic_cast<KActionCategory*>(sipCpp))
        sipType = sipType_KActionCategory;
    else if (dynamic_cast<KActionCollection*>(sipCpp))
        sipType = sipType_KActionCollection;
    else if (dynamic_cast<KCategoryDrawerV2*>(sipCpp))
        {
        sipType = sipType_KCategoryDrawerV2;
        if (dynamic_cast<KCategoryDrawerV3*>(sipCpp))
            sipType = sipType_KCategoryDrawerV3;
        }
    else if (dynamic_cast<KCompletion*>(sipCpp))
        sipType = sipType_KCompletion;
    else if (dynamic_cast<KConfigDialogManager*>(sipCpp))
        sipType = sipType_KConfigDialogManager;
    else if (dynamic_cast<KConfigSkeleton*>(sipCpp))
        sipType = sipType_KConfigSkeleton;
    else if (dynamic_cast<KFind*>(sipCpp))
        {
        sipType = sipType_KFind;
        if (dynamic_cast<KReplace*>(sipCpp))
            sipType = sipType_KReplace;
        }
    else if (dynamic_cast<KGlobalAccel*>(sipCpp))
        sipType = sipType_KGlobalAccel;
    else if (dynamic_cast<KGlobalSettings*>(sipCpp))
        sipType = sipType_KGlobalSettings;
    else if (dynamic_cast<KGlobalShortcutInfo*>(sipCpp))
        sipType = sipType_KGlobalShortcutInfo;
    else if (dynamic_cast<KHelpMenu*>(sipCpp))
        sipType = sipType_KHelpMenu;
    else if (dynamic_cast<KIconLoader*>(sipCpp))
        sipType = sipType_KIconLoader;
    else if (dynamic_cast<KAbstractWidgetJobTracker*>(sipCpp))
        {
        sipType = sipType_KAbstractWidgetJobTracker;
        if (dynamic_cast<KStatusBarJobTracker*>(sipCpp))
            sipType = sipType_KStatusBarJobTracker;
        else if (dynamic_cast<KWidgetJobTracker*>(sipCpp))
            sipType = sipType_KWidgetJobTracker;
        }
    else if (dynamic_cast<KUiServerJobTracker*>(sipCpp))
        sipType = sipType_KUiServerJobTracker;
    else if (dynamic_cast<KDialogJobUiDelegate*>(sipCpp))
        sipType = sipType_KDialogJobUiDelegate;
    else if (dynamic_cast<KMessageBoxMessageHandler*>(sipCpp))
        sipType = sipType_KMessageBoxMessageHandler;
    else if (dynamic_cast<KModelIndexProxyMapper*>(sipCpp))
        sipType = sipType_KModelIndexProxyMapper;
    else if (dynamic_cast<KModifierKeyInfo*>(sipCpp))
        sipType = sipType_KModifierKeyInfo;
    else if (dynamic_cast<KNotification*>(sipCpp))
        sipType = sipType_KNotification;
    else if (dynamic_cast<KNotificationRestrictions*>(sipCpp))
        sipType = sipType_KNotificationRestrictions;
    else if (dynamic_cast<KPageWidgetItem*>(sipCpp))
        sipType = sipType_KPageWidgetItem;
    else if (dynamic_cast<KPassivePopupMessageHandler*>(sipCpp))
        sipType = sipType_KPassivePopupMessageHandler;
    else if (dynamic_cast<KPixmapSequenceOverlayPainter*>(sipCpp))
        sipType = sipType_KPixmapSequenceOverlayPainter;
    else if (dynamic_cast<KSelectionOwner*>(sipCpp))
        sipType = sipType_KSelectionOwner;
    else if (dynamic_cast<KSelectionWatcher*>(sipCpp))
        sipType = sipType_KSelectionWatcher;
    else if (dynamic_cast<KStartupInfo*>(sipCpp))
        sipType = sipType_KStartupInfo;
    else if (dynamic_cast<KStatusNotifierItem*>(sipCpp))
        sipType = sipType_KStatusNotifierItem;
    else if (dynamic_cast<KViewStateMaintainerBase*>(sipCpp))
        sipType = sipType_KViewStateMaintainerBase;
    else if (dynamic_cast<KViewStateSaver*>(sipCpp))
        sipType = sipType_KViewStateSaver;
    else if (dynamic_cast<KWallet::Wallet*>(sipCpp))
        sipType = sipType_KWallet_Wallet;
    else if (dynamic_cast<KXMLGUIFactory*>(sipCpp))
        sipType = sipType_KXMLGUIFactory;
    else if (dynamic_cast<KWidgetItemDelegate*>(sipCpp))
        sipType = sipType_KWidgetItemDelegate;
    else if (dynamic_cast<KExtendableItemDelegate*>(sipCpp))
        sipType = sipType_KExtendableItemDelegate;
    else if (dynamic_cast<KPageModel*>(sipCpp))
        {
        sipType = sipType_KPageModel;
        if (dynamic_cast<KPageWidgetModel*>(sipCpp))
            sipType = sipType_KPageWidgetModel;
        }
    else if (dynamic_cast<KDescendantsProxyModel*>(sipCpp))
        sipType = sipType_KDescendantsProxyModel;
    else if (dynamic_cast<KIdentityProxyModel*>(sipCpp))
        {
        sipType = sipType_KIdentityProxyModel;
        if (dynamic_cast<KCheckableProxyModel*>(sipCpp))
            sipType = sipType_KCheckableProxyModel;
        }
    else if (dynamic_cast<KSelectionProxyModel*>(sipCpp))
        sipType = sipType_KSelectionProxyModel;
    else if (dynamic_cast<KCategorizedSortFilterProxyModel*>(sipCpp))
        sipType = sipType_KCategorizedSortFilterProxyModel;
    else if (dynamic_cast<KRecursiveFilterProxyModel*>(sipCpp))
        sipType = sipType_KRecursiveFilterProxyModel;
    else if (dynamic_cast<KAction*>(sipCpp))
        {
        sipType = sipType_KAction;
        if (dynamic_cast<KActionMenu*>(sipCpp))
            sipType = sipType_KActionMenu;
        else if (dynamic_cast<KDualAction*>(sipCpp))
            sipType = sipType_KDualAction;
        else if (dynamic_cast<KPasteTextAction*>(sipCpp))
            sipType = sipType_KPasteTextAction;
        else if (dynamic_cast<KSelectAction*>(sipCpp))
            {
            sipType = sipType_KSelectAction;
            if (dynamic_cast<KCodecAction*>(sipCpp))
                sipType = sipType_KCodecAction;
            else if (dynamic_cast<KFontAction*>(sipCpp))
                sipType = sipType_KFontAction;
            else if (dynamic_cast<KFontSizeAction*>(sipCpp))
                sipType = sipType_KFontSizeAction;
            else if (dynamic_cast<KRecentFilesAction*>(sipCpp))
                sipType = sipType_KRecentFilesAction;
            }
        else if (dynamic_cast<KToggleAction*>(sipCpp))
            {
            sipType = sipType_KToggleAction;
            if (dynamic_cast<KToggleFullScreenAction*>(sipCpp))
                sipType = sipType_KToggleFullScreenAction;
            else if (dynamic_cast<KToggleToolBarAction*>(sipCpp))
                sipType = sipType_KToggleToolBarAction;
            }
        else if (dynamic_cast<KToolBarLabelAction*>(sipCpp))
            sipType = sipType_KToolBarLabelAction;
        else if (dynamic_cast<KToolBarPopupAction*>(sipCpp))
            sipType = sipType_KToolBarPopupAction;
        else if (dynamic_cast<KToolBarSpacerAction*>(sipCpp))
            sipType = sipType_KToolBarSpacerAction;
        }
    else if (dynamic_cast<KApplication*>(sipCpp))
        {
        sipType = sipType_KApplication;
        if (dynamic_cast<KUniqueApplication*>(sipCpp))
            sipType = sipType_KUniqueApplication;
        }
    else if (dynamic_cast<KBreadcrumbSelectionModel*>(sipCpp))
        sipType = sipType_KBreadcrumbSelectionModel;
    else if (dynamic_cast<KLinkItemSelectionModel*>(sipCpp))
        sipType = sipType_KLinkItemSelectionModel;
    else if (dynamic_cast<KStyle*>(sipCpp))
        sipType = sipType_KStyle;
    else if (dynamic_cast<KSvgRenderer*>(sipCpp))
        sipType = sipType_KSvgRenderer;
    else if (dynamic_cast<Sonnet::Highlighter*>(sipCpp))
        sipType = sipType_Sonnet_Highlighter;
    else if (dynamic_cast<KSystemTrayIcon*>(sipCpp))
        sipType = sipType_KSystemTrayIcon;
    else if (dynamic_cast<KUndoStack*>(sipCpp))
        sipType = sipType_KUndoStack;
    else if (dynamic_cast<KDateValidator*>(sipCpp))
        sipType = sipType_KDateValidator;
    else if (dynamic_cast<KFloatValidator*>(sipCpp))
        sipType = sipType_KFloatValidator;
    else if (dynamic_cast<KIntValidator*>(sipCpp))
        sipType = sipType_KIntValidator;
    else if (dynamic_cast<KMimeTypeValidator*>(sipCpp))
        sipType = sipType_KMimeTypeValidator;
    else if (dynamic_cast<KStringListValidator*>(sipCpp))
        sipType = sipType_KStringListValidator;
    else if (dynamic_cast<KDoubleValidator*>(sipCpp))
        sipType = sipType_KDoubleValidator;
    else if (dynamic_cast<KActionSelector*>(sipCpp))
        sipType = sipType_KActionSelector;
    else if (dynamic_cast<KCModule*>(sipCpp))
        sipType = sipType_KCModule;
    else if (dynamic_cast<KCapacityBar*>(sipCpp))
        sipType = sipType_KCapacityBar;
    else if (dynamic_cast<KCharSelect*>(sipCpp))
        sipType = sipType_KCharSelect;
    else if (dynamic_cast<KDateTable*>(sipCpp))
        sipType = sipType_KDateTable;
    else if (dynamic_cast<KDateTimeEdit*>(sipCpp))
        sipType = sipType_KDateTimeEdit;
    else if (dynamic_cast<KDateTimeWidget*>(sipCpp))
        sipType = sipType_KDateTimeWidget;
    else if (dynamic_cast<KDateWidget*>(sipCpp))
        sipType = sipType_KDateWidget;
    else if (dynamic_cast<KEditListWidget*>(sipCpp))
        sipType = sipType_KEditListWidget;
    else if (dynamic_cast<KFadeWidgetEffect*>(sipCpp))
        sipType = sipType_KFadeWidgetEffect;
    else if (dynamic_cast<KFilterProxySearchLine*>(sipCpp))
        sipType = sipType_KFilterProxySearchLine;
    else if (dynamic_cast<KFontChooser*>(sipCpp))
        sipType = sipType_KFontChooser;
    else if (dynamic_cast<KFontRequester*>(sipCpp))
        sipType = sipType_KFontRequester;
    else if (dynamic_cast<KKeySequenceWidget*>(sipCpp))
        sipType = sipType_KKeySequenceWidget;
    else if (dynamic_cast<KLanguageButton*>(sipCpp))
        sipType = sipType_KLanguageButton;
    else if (dynamic_cast<KLed*>(sipCpp))
        sipType = sipType_KLed;
    else if (dynamic_cast<KMultiTabBar*>(sipCpp))
        sipType = sipType_KMultiTabBar;
    else if (dynamic_cast<KNumInput*>(sipCpp))
        {
        sipType = sipType_KNumInput;
        if (dynamic_cast<KDoubleNumInput*>(sipCpp))
            sipType = sipType_KDoubleNumInput;
        else if (dynamic_cast<KIntNumInput*>(sipCpp))
            sipType = sipType_KIntNumInput;
        }
    else if (dynamic_cast<KPageView*>(sipCpp))
        {
        sipType = sipType_KPageView;
        if (dynamic_cast<KPageWidget*>(sipCpp))
            sipType = sipType_KPageWidget;
        }
    else if (dynamic_cast<KPixmapRegionSelectorWidget*>(sipCpp))
        sipType = sipType_KPixmapRegionSelectorWidget;
    else if (dynamic_cast<KPixmapSequenceWidget*>(sipCpp))
        sipType = sipType_KPixmapSequenceWidget;
    else if (dynamic_cast<KShortcutWidget*>(sipCpp))
        sipType = sipType_KShortcutWidget;
    else if (dynamic_cast<KShortcutsEditor*>(sipCpp))
        sipType = sipType_KShortcutsEditor;
    else if (dynamic_cast<KTitleWidget*>(sipCpp))
        sipType = sipType_KTitleWidget;
    else if (dynamic_cast<KTreeWidgetSearchLineWidget*>(sipCpp))
        sipType = sipType_KTreeWidgetSearchLineWidget;
    else if (dynamic_cast<KXMessages*>(sipCpp))
        sipType = sipType_KXMessages;
    else if (dynamic_cast<KXYSelector*>(sipCpp))
        {
        sipType = sipType_KXYSelector;
        if (dynamic_cast<KHueSaturationSelector*>(sipCpp))
            sipType = sipType_KHueSaturationSelector;
        }
    else if (dynamic_cast<KArrowButton*>(sipCpp))
        sipType = sipType_KArrowButton;
    else if (dynamic_cast<KColorButton*>(sipCpp))
        sipType = sipType_KColorButton;
    else if (dynamic_cast<KMultiTabBarButton*>(sipCpp))
        {
        sipType = sipType_KMultiTabBarButton;
        if (dynamic_cast<KMultiTabBarTab*>(sipCpp))
            sipType = sipType_KMultiTabBarTab;
        }
    else if (dynamic_cast<KPushButton*>(sipCpp))
        sipType = sipType_KPushButton;
    else if (dynamic_cast<KAnimatedButton*>(sipCpp))
        sipType = sipType_KAnimatedButton;
    else if (dynamic_cast<KRuler*>(sipCpp))
        sipType = sipType_KRuler;
    else if (dynamic_cast<KSelector*>(sipCpp))
        {
        sipType = sipType_KSelector;
        if (dynamic_cast<KColorValueSelector*>(sipCpp))
            sipType = sipType_KColorValueSelector;
        else if (dynamic_cast<KGradientSelector*>(sipCpp))
            sipType = sipType_KGradientSelector;
        }
    else if (dynamic_cast<KIntSpinBox*>(sipCpp))
        sipType = sipType_KIntSpinBox;
    else if (dynamic_cast<KColorCombo*>(sipCpp))
        sipType = sipType_KColorCombo;
    else if (dynamic_cast<KComboBox*>(sipCpp))
        {
        sipType = sipType_KComboBox;
        if (dynamic_cast<KDateComboBox*>(sipCpp))
            sipType = sipType_KDateComboBox;
        else if (dynamic_cast<KFontComboBox*>(sipCpp))
            sipType = sipType_KFontComboBox;
        else if (dynamic_cast<KHistoryComboBox*>(sipCpp))
            sipType = sipType_KHistoryComboBox;
        else if (dynamic_cast<KTimeComboBox*>(sipCpp))
            sipType = sipType_KTimeComboBox;
        else if (dynamic_cast<Sonnet::DictionaryComboBox*>(sipCpp))
            sipType = sipType_Sonnet_DictionaryComboBox;
        }
    else if (dynamic_cast<KDialog*>(sipCpp))
        {
        sipType = sipType_KDialog;
        if (dynamic_cast<KAboutApplicationDialog*>(sipCpp))
            sipType = sipType_KAboutApplicationDialog;
        else if (dynamic_cast<KBugReport*>(sipCpp))
            sipType = sipType_KBugReport;
        else if (dynamic_cast<KColorDialog*>(sipCpp))
            sipType = sipType_KColorDialog;
        else if (dynamic_cast<KEditToolBar*>(sipCpp))
            sipType = sipType_KEditToolBar;
        else if (dynamic_cast<KFindDialog*>(sipCpp))
            {
            sipType = sipType_KFindDialog;
            if (dynamic_cast<KReplaceDialog*>(sipCpp))
                sipType = sipType_KReplaceDialog;
            }
        else if (dynamic_cast<KFontDialog*>(sipCpp))
            sipType = sipType_KFontDialog;
        else if (dynamic_cast<KNewPasswordDialog*>(sipCpp))
            sipType = sipType_KNewPasswordDialog;
        else if (dynamic_cast<KPageDialog*>(sipCpp))
            {
            sipType = sipType_KPageDialog;
            if (dynamic_cast<KAssistantDialog*>(sipCpp))
                sipType = sipType_KAssistantDialog;
            else if (dynamic_cast<KConfigDialog*>(sipCpp))
                sipType = sipType_KConfigDialog;
            }
        else if (dynamic_cast<KPasswordDialog*>(sipCpp))
            sipType = sipType_KPasswordDialog;
        else if (dynamic_cast<KPixmapRegionSelectorDialog*>(sipCpp))
            sipType = sipType_KPixmapRegionSelectorDialog;
        else if (dynamic_cast<KProgressDialog*>(sipCpp))
            sipType = sipType_KProgressDialog;
        else if (dynamic_cast<KShortcutsDialog*>(sipCpp))
            sipType = sipType_KShortcutsDialog;
        else if (dynamic_cast<KTipDialog*>(sipCpp))
            sipType = sipType_KTipDialog;
        else if (dynamic_cast<Sonnet::ConfigDialog*>(sipCpp))
            sipType = sipType_Sonnet_ConfigDialog;
        else if (dynamic_cast<Sonnet::Dialog*>(sipCpp))
            sipType = sipType_Sonnet_Dialog;
        }
    else if (dynamic_cast<KDialogButtonBox*>(sipCpp))
        sipType = sipType_KDialogButtonBox;
    else if (dynamic_cast<KColorPatch*>(sipCpp))
        sipType = sipType_KColorPatch;
    else if (dynamic_cast<KDatePicker*>(sipCpp))
        sipType = sipType_KDatePicker;
    else if (dynamic_cast<KHBox*>(sipCpp))
        {
        sipType = sipType_KHBox;
        if (dynamic_cast<KVBox*>(sipCpp))
            sipType = sipType_KVBox;
        }
    else if (dynamic_cast<KMessageWidget*>(sipCpp))
        sipType = sipType_KMessageWidget;
    else if (dynamic_cast<KPassivePopup*>(sipCpp))
        sipType = sipType_KPassivePopup;
    else if (dynamic_cast<KPlotWidget*>(sipCpp))
        sipType = sipType_KPlotWidget;
    else if (dynamic_cast<KPopupFrame*>(sipCpp))
        sipType = sipType_KPopupFrame;
    else if (dynamic_cast<KRatingWidget*>(sipCpp))
        sipType = sipType_KRatingWidget;
    else if (dynamic_cast<KSeparator*>(sipCpp))
        sipType = sipType_KSeparator;
    else if (dynamic_cast<KCategorizedView*>(sipCpp))
        sipType = sipType_KCategorizedView;
    else if (dynamic_cast<KListWidget*>(sipCpp))
        {
        sipType = sipType_KListWidget;
        if (dynamic_cast<KCompletionBox*>(sipCpp))
            sipType = sipType_KCompletionBox;
        }
    else if (dynamic_cast<KColorCells*>(sipCpp))
        sipType = sipType_KColorCells;
    else if (dynamic_cast<KTimeZoneWidget*>(sipCpp))
        sipType = sipType_KTimeZoneWidget;
    else if (dynamic_cast<KTextEdit*>(sipCpp))
        {
        sipType = sipType_KTextEdit;
        if (dynamic_cast<KRichTextEdit*>(sipCpp))
            {
            sipType = sipType_KRichTextEdit;
            if (dynamic_cast<KRichTextWidget*>(sipCpp))
                sipType = sipType_KRichTextWidget;
            }
        }
    else if (dynamic_cast<KTextBrowser*>(sipCpp))
        sipType = sipType_KTextBrowser;
    else if (dynamic_cast<KSqueezedTextLabel*>(sipCpp))
        sipType = sipType_KSqueezedTextLabel;
    else if (dynamic_cast<KUrlLabel*>(sipCpp))
        sipType = sipType_KUrlLabel;
    else if (dynamic_cast<KButtonGroup*>(sipCpp))
        sipType = sipType_KButtonGroup;
    else if (dynamic_cast<KEditListBox*>(sipCpp))
        sipType = sipType_KEditListBox;
    else if (dynamic_cast<KLineEdit*>(sipCpp))
        {
        sipType = sipType_KLineEdit;
        if (dynamic_cast<KListWidgetSearchLine*>(sipCpp))
            sipType = sipType_KListWidgetSearchLine;
        else if (dynamic_cast<KRestrictedLine*>(sipCpp))
            sipType = sipType_KRestrictedLine;
        else if (dynamic_cast<KTreeWidgetSearchLine*>(sipCpp))
            sipType = sipType_KTreeWidgetSearchLine;
        }
    else if (dynamic_cast<KMainWindow*>(sipCpp))
        {
        sipType = sipType_KMainWindow;
        if (dynamic_cast<KXmlGuiWindow*>(sipCpp))
            sipType = sipType_KXmlGuiWindow;
        }
    else if (dynamic_cast<KMenu*>(sipCpp))
        sipType = sipType_KMenu;
    else if (dynamic_cast<KMenuBar*>(sipCpp))
        sipType = sipType_KMenuBar;
    else if (dynamic_cast<KSplashScreen*>(sipCpp))
        sipType = sipType_KSplashScreen;
    else if (dynamic_cast<KStatusBar*>(sipCpp))
        sipType = sipType_KStatusBar;
    else if (dynamic_cast<KTabBar*>(sipCpp))
        sipType = sipType_KTabBar;
    else if (dynamic_cast<KTabWidget*>(sipCpp))
        sipType = sipType_KTabWidget;
    else if (dynamic_cast<KToolBar*>(sipCpp))
        sipType = sipType_KToolBar;
    else if (dynamic_cast<Sonnet::ConfigWidget*>(sipCpp))
        sipType = sipType_Sonnet_ConfigWidget;
%End
"""


#
# Main dictionary.
#
# For a top level object, when using sip_bulk_generator.py, it is important to use the name of any forwardee header in
# the key, since that is the file we actually use.
#
def code():
    return {
# ./khtml/dom_misc.sip
"DOM::DomShared": { #DomShared
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'DomShared'
    sipType = NULL;

    if (dynamic_cast<DOM::CustomNodeFilter*>(sipCpp))
        sipType = sipType_DOM_CustomNodeFilter;
    else if (dynamic_cast<DOM::EventListener*>(sipCpp))
        sipType = sipType_DOM_EventListener;
%End
"""
},
# ./khtml/khtml_part.sip
"khtml_part.h::KHTMLPart": { #KHTMLPart : KParts::ReadOnlyPart
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QObject'
    sipType = NULL;

    if (dynamic_cast<KHTMLPart*>(sipCpp))
        sipType = sipType_KHTMLPart;
    else if (dynamic_cast<KHTMLView*>(sipCpp))
        sipType = sipType_KHTMLView;
%End
"""
},
# ./khtml/dom_element.sip
"DOM::Attr": { #Attr : DOM::Node
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'Node'
    sipType = NULL;

    if (dynamic_cast<DOM::Attr*>(sipCpp))
        sipType = sipType_DOM_Attr;
    else if (dynamic_cast<DOM::CharacterData*>(sipCpp))
        {
        sipType = sipType_DOM_CharacterData;
        if (dynamic_cast<DOM::Comment*>(sipCpp))
            sipType = sipType_DOM_Comment;
        else if (dynamic_cast<DOM::Text*>(sipCpp))
            {
            sipType = sipType_DOM_Text;
            if (dynamic_cast<DOM::CDATASection*>(sipCpp))
                sipType = sipType_DOM_CDATASection;
            }
        }
    else if (dynamic_cast<DOM::Document*>(sipCpp))
        {
        sipType = sipType_DOM_Document;
        if (dynamic_cast<DOM::HTMLDocument*>(sipCpp))
            sipType = sipType_DOM_HTMLDocument;
        }
    else if (dynamic_cast<DOM::DocumentFragment*>(sipCpp))
        sipType = sipType_DOM_DocumentFragment;
    else if (dynamic_cast<DOM::DocumentType*>(sipCpp))
        sipType = sipType_DOM_DocumentType;
    else if (dynamic_cast<DOM::Element*>(sipCpp))
        {
        sipType = sipType_DOM_Element;
        if (dynamic_cast<DOM::HTMLElement*>(sipCpp))
            {
            sipType = sipType_DOM_HTMLElement;
            if (dynamic_cast<DOM::HTMLAnchorElement*>(sipCpp))
                sipType = sipType_DOM_HTMLAnchorElement;
            else if (dynamic_cast<DOM::HTMLAppletElement*>(sipCpp))
                sipType = sipType_DOM_HTMLAppletElement;
            else if (dynamic_cast<DOM::HTMLAreaElement*>(sipCpp))
                sipType = sipType_DOM_HTMLAreaElement;
            else if (dynamic_cast<DOM::HTMLBRElement*>(sipCpp))
                sipType = sipType_DOM_HTMLBRElement;
            else if (dynamic_cast<DOM::HTMLBaseElement*>(sipCpp))
                sipType = sipType_DOM_HTMLBaseElement;
            else if (dynamic_cast<DOM::HTMLBaseFontElement*>(sipCpp))
                sipType = sipType_DOM_HTMLBaseFontElement;
            else if (dynamic_cast<DOM::HTMLBlockquoteElement*>(sipCpp))
                sipType = sipType_DOM_HTMLBlockquoteElement;
            else if (dynamic_cast<DOM::HTMLBodyElement*>(sipCpp))
                sipType = sipType_DOM_HTMLBodyElement;
            else if (dynamic_cast<DOM::HTMLButtonElement*>(sipCpp))
                sipType = sipType_DOM_HTMLButtonElement;
            else if (dynamic_cast<DOM::HTMLDListElement*>(sipCpp))
                sipType = sipType_DOM_HTMLDListElement;
            else if (dynamic_cast<DOM::HTMLDirectoryElement*>(sipCpp))
                sipType = sipType_DOM_HTMLDirectoryElement;
            else if (dynamic_cast<DOM::HTMLDivElement*>(sipCpp))
                sipType = sipType_DOM_HTMLDivElement;
            else if (dynamic_cast<DOM::HTMLFieldSetElement*>(sipCpp))
                sipType = sipType_DOM_HTMLFieldSetElement;
            else if (dynamic_cast<DOM::HTMLFontElement*>(sipCpp))
                sipType = sipType_DOM_HTMLFontElement;
            else if (dynamic_cast<DOM::HTMLFormElement*>(sipCpp))
                sipType = sipType_DOM_HTMLFormElement;
            else if (dynamic_cast<DOM::HTMLFrameElement*>(sipCpp))
                sipType = sipType_DOM_HTMLFrameElement;
            else if (dynamic_cast<DOM::HTMLFrameSetElement*>(sipCpp))
                sipType = sipType_DOM_HTMLFrameSetElement;
            else if (dynamic_cast<DOM::HTMLHRElement*>(sipCpp))
                sipType = sipType_DOM_HTMLHRElement;
            else if (dynamic_cast<DOM::HTMLHeadElement*>(sipCpp))
                sipType = sipType_DOM_HTMLHeadElement;
            else if (dynamic_cast<DOM::HTMLHeadingElement*>(sipCpp))
                sipType = sipType_DOM_HTMLHeadingElement;
            else if (dynamic_cast<DOM::HTMLHtmlElement*>(sipCpp))
                sipType = sipType_DOM_HTMLHtmlElement;
            else if (dynamic_cast<DOM::HTMLIFrameElement*>(sipCpp))
                sipType = sipType_DOM_HTMLIFrameElement;
            else if (dynamic_cast<DOM::HTMLImageElement*>(sipCpp))
                sipType = sipType_DOM_HTMLImageElement;
            else if (dynamic_cast<DOM::HTMLInputElement*>(sipCpp))
                sipType = sipType_DOM_HTMLInputElement;
            else if (dynamic_cast<DOM::HTMLIsIndexElement*>(sipCpp))
                sipType = sipType_DOM_HTMLIsIndexElement;
            else if (dynamic_cast<DOM::HTMLLIElement*>(sipCpp))
                sipType = sipType_DOM_HTMLLIElement;
            else if (dynamic_cast<DOM::HTMLLabelElement*>(sipCpp))
                sipType = sipType_DOM_HTMLLabelElement;
            else if (dynamic_cast<DOM::HTMLLayerElement*>(sipCpp))
                sipType = sipType_DOM_HTMLLayerElement;
            else if (dynamic_cast<DOM::HTMLLegendElement*>(sipCpp))
                sipType = sipType_DOM_HTMLLegendElement;
            else if (dynamic_cast<DOM::HTMLLinkElement*>(sipCpp))
                sipType = sipType_DOM_HTMLLinkElement;
            else if (dynamic_cast<DOM::HTMLMapElement*>(sipCpp))
                sipType = sipType_DOM_HTMLMapElement;
            else if (dynamic_cast<DOM::HTMLMenuElement*>(sipCpp))
                sipType = sipType_DOM_HTMLMenuElement;
            else if (dynamic_cast<DOM::HTMLMetaElement*>(sipCpp))
                sipType = sipType_DOM_HTMLMetaElement;
            else if (dynamic_cast<DOM::HTMLModElement*>(sipCpp))
                sipType = sipType_DOM_HTMLModElement;
            else if (dynamic_cast<DOM::HTMLOListElement*>(sipCpp))
                sipType = sipType_DOM_HTMLOListElement;
            else if (dynamic_cast<DOM::HTMLObjectElement*>(sipCpp))
                sipType = sipType_DOM_HTMLObjectElement;
            else if (dynamic_cast<DOM::HTMLOptGroupElement*>(sipCpp))
                sipType = sipType_DOM_HTMLOptGroupElement;
            else if (dynamic_cast<DOM::HTMLOptionElement*>(sipCpp))
                sipType = sipType_DOM_HTMLOptionElement;
            else if (dynamic_cast<DOM::HTMLParagraphElement*>(sipCpp))
                sipType = sipType_DOM_HTMLParagraphElement;
            else if (dynamic_cast<DOM::HTMLParamElement*>(sipCpp))
                sipType = sipType_DOM_HTMLParamElement;
            else if (dynamic_cast<DOM::HTMLPreElement*>(sipCpp))
                sipType = sipType_DOM_HTMLPreElement;
            else if (dynamic_cast<DOM::HTMLQuoteElement*>(sipCpp))
                sipType = sipType_DOM_HTMLQuoteElement;
            else if (dynamic_cast<DOM::HTMLScriptElement*>(sipCpp))
                sipType = sipType_DOM_HTMLScriptElement;
            else if (dynamic_cast<DOM::HTMLSelectElement*>(sipCpp))
                sipType = sipType_DOM_HTMLSelectElement;
            else if (dynamic_cast<DOM::HTMLStyleElement*>(sipCpp))
                sipType = sipType_DOM_HTMLStyleElement;
            else if (dynamic_cast<DOM::HTMLTableCaptionElement*>(sipCpp))
                sipType = sipType_DOM_HTMLTableCaptionElement;
            else if (dynamic_cast<DOM::HTMLTableCellElement*>(sipCpp))
                sipType = sipType_DOM_HTMLTableCellElement;
            else if (dynamic_cast<DOM::HTMLTableColElement*>(sipCpp))
                sipType = sipType_DOM_HTMLTableColElement;
            else if (dynamic_cast<DOM::HTMLTableElement*>(sipCpp))
                sipType = sipType_DOM_HTMLTableElement;
            else if (dynamic_cast<DOM::HTMLTableRowElement*>(sipCpp))
                sipType = sipType_DOM_HTMLTableRowElement;
            else if (dynamic_cast<DOM::HTMLTableSectionElement*>(sipCpp))
                sipType = sipType_DOM_HTMLTableSectionElement;
            else if (dynamic_cast<DOM::HTMLTextAreaElement*>(sipCpp))
                sipType = sipType_DOM_HTMLTextAreaElement;
            else if (dynamic_cast<DOM::HTMLTitleElement*>(sipCpp))
                sipType = sipType_DOM_HTMLTitleElement;
            else if (dynamic_cast<DOM::HTMLUListElement*>(sipCpp))
                sipType = sipType_DOM_HTMLUListElement;
            }
        }
    else if (dynamic_cast<DOM::Entity*>(sipCpp))
        sipType = sipType_DOM_Entity;
    else if (dynamic_cast<DOM::EntityReference*>(sipCpp))
        sipType = sipType_DOM_EntityReference;
    else if (dynamic_cast<DOM::Notation*>(sipCpp))
        sipType = sipType_DOM_Notation;
    else if (dynamic_cast<DOM::ProcessingInstruction*>(sipCpp))
        sipType = sipType_DOM_ProcessingInstruction;
%End
"""
},
# ./khtml/dom2_events.sip
"DOM::MutationEvent": { #MutationEvent : DOM::Event
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'Event'
    sipType = NULL;

    if (dynamic_cast<DOM::MutationEvent*>(sipCpp))
        sipType = sipType_DOM_MutationEvent;
    else if (dynamic_cast<DOM::UIEvent*>(sipCpp))
        {
        sipType = sipType_DOM_UIEvent;
        if (dynamic_cast<DOM::KeyboardEvent*>(sipCpp))
            sipType = sipType_DOM_KeyboardEvent;
        else if (dynamic_cast<DOM::MouseEvent*>(sipCpp))
            sipType = sipType_DOM_MouseEvent;
        else if (dynamic_cast<DOM::TextEvent*>(sipCpp))
            sipType = sipType_DOM_TextEvent;
        }
%End
"""
},
# ./kparts/event.sip
"KParts::Event": { #Event : QEvent
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QEvent'
    sipType = NULL;

    if (dynamic_cast<KParts::Event*>(sipCpp))
        {
        sipType = sipType_KParts_Event;
        if (dynamic_cast<KParts::GUIActivateEvent*>(sipCpp))
            sipType = sipType_KParts_GUIActivateEvent;
        else if (dynamic_cast<KParts::OpenUrlEvent*>(sipCpp))
            sipType = sipType_KParts_OpenUrlEvent;
        else if (dynamic_cast<KParts::PartActivateEvent*>(sipCpp))
            sipType = sipType_KParts_PartActivateEvent;
        else if (dynamic_cast<KParts::PartSelectEvent*>(sipCpp))
            sipType = sipType_KParts_PartSelectEvent;
        }
%End
"""
},
# ./kparts/browserextension.sip
"KParts::BrowserExtension": { #BrowserExtension : QObject
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QObject'
    sipType = NULL;

    if (dynamic_cast<KParts::BrowserExtension*>(sipCpp))
        sipType = sipType_KParts_BrowserExtension;
    else if (dynamic_cast<KParts::BrowserHostExtension*>(sipCpp))
        sipType = sipType_KParts_BrowserHostExtension;
    else if (dynamic_cast<KParts::BrowserInterface*>(sipCpp))
        sipType = sipType_KParts_BrowserInterface;
    else if (dynamic_cast<KParts::FileInfoExtension*>(sipCpp))
        sipType = sipType_KParts_FileInfoExtension;
    else if (dynamic_cast<KParts::HistoryProvider*>(sipCpp))
        sipType = sipType_KParts_HistoryProvider;
    else if (dynamic_cast<KParts::HtmlExtension*>(sipCpp))
        sipType = sipType_KParts_HtmlExtension;
    else if (dynamic_cast<KParts::LiveConnectExtension*>(sipCpp))
        sipType = sipType_KParts_LiveConnectExtension;
    else if (dynamic_cast<KParts::Part*>(sipCpp))
        {
        sipType = sipType_KParts_Part;
        if (dynamic_cast<KParts::ReadOnlyPart*>(sipCpp))
            {
            sipType = sipType_KParts_ReadOnlyPart;
            if (dynamic_cast<KParts::ReadWritePart*>(sipCpp))
                sipType = sipType_KParts_ReadWritePart;
            }
        }
    else if (dynamic_cast<KParts::PartManager*>(sipCpp))
        sipType = sipType_KParts_PartManager;
    else if (dynamic_cast<KParts::Plugin*>(sipCpp))
        sipType = sipType_KParts_Plugin;
    else if (dynamic_cast<KParts::ScriptableExtension*>(sipCpp))
        sipType = sipType_KParts_ScriptableExtension;
    else if (dynamic_cast<KParts::StatusBarExtension*>(sipCpp))
        sipType = sipType_KParts_StatusBarExtension;
    else if (dynamic_cast<KParts::TextExtension*>(sipCpp))
        sipType = sipType_KParts_TextExtension;
    else if (dynamic_cast<KParts::BrowserRun*>(sipCpp))
        sipType = sipType_KParts_BrowserRun;
    else if (dynamic_cast<KParts::MainWindow*>(sipCpp))
        sipType = sipType_KParts_MainWindow;
%End
"""
},
# ./kparts/factory.sip
"Factory": { #Factory : KLibFactory
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'Factory'
    sipType = NULL;

    if (dynamic_cast<KParts::Factory*>(sipCpp))
        sipType = sipType_KParts_Factory;
%End
"""
},
# ./phonon/medianode.sip
"MediaNode": { #MediaNode /NoDefaultCtors/
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'MediaNode'
    sipType = NULL;

    if (dynamic_cast<Phonon::AbstractAudioOutput*>(sipCpp))
        {
        sipType = sipType_Phonon_AbstractAudioOutput;
        if (dynamic_cast<Phonon::AudioDataOutput*>(sipCpp))
            sipType = sipType_Phonon_AudioDataOutput;
        }
    else if (dynamic_cast<Phonon::AbstractVideoOutput*>(sipCpp))
        {
        sipType = sipType_Phonon_AbstractVideoOutput;
        if (dynamic_cast<Phonon::VideoWidget*>(sipCpp))
            sipType = sipType_Phonon_VideoWidget;
        }
    else if (dynamic_cast<Phonon::AudioOutput*>(sipCpp))
        sipType = sipType_Phonon_AudioOutput;
    else if (dynamic_cast<Phonon::Effect*>(sipCpp))
        {
        sipType = sipType_Phonon_Effect;
        if (dynamic_cast<Phonon::VolumeFaderEffect*>(sipCpp))
            sipType = sipType_Phonon_VolumeFaderEffect;
        }
    else if (dynamic_cast<Phonon::MediaObject*>(sipCpp))
        sipType = sipType_Phonon_MediaObject;
%End
"""
},
# ./phonon/abstractvideodataoutput.sip
"QSet<Phonon::Experimental::VideoFrame2::Format>": { #QSet<Phonon::Experimental::VideoFrame2::Format>
"code":
"""
%TypeHeaderCode
#include <qset.h>
#include <phonon/experimental/abstractvideodataoutput.h>
%End
%ConvertFromTypeCode
    // Create the list.
    PyObject *l;

    if ((l = PyList_New(sipCpp->size())) == NULL)
        return NULL;

    // Set the list elements.
    QSet<Phonon::Experimental::VideoFrame2::Format> set = *sipCpp;
    int i = 0;
    foreach (Phonon::Experimental::VideoFrame2::Format value, set)
    {
        PyObject *obj = PyInt_FromLong ((long) value);
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

    QSet<Phonon::Experimental::VideoFrame2::Format> *qs = new QSet<Phonon::Experimental::VideoFrame2::Format>;

    for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i)
    {
        Phonon::Experimental::VideoFrame2::Format t = (Phonon::Experimental::VideoFrame2::Format)PyInt_AS_LONG (PyList_GET_ITEM (sipPy, i));
        *qs << t;

    }

    *sipCppPtr = qs;

    return sipGetState(sipTransferObj);
%End
"""
},
# ./phonon/pulsesupport.sip
"PulseSupport": { #PulseSupport : QObject
"code":
"""
%TypeHeaderCode
#include <phonon/pulsesupport.h>
#include <phonon/phononnamespace.h>
%End
"""
},
# ./phonon/mrl.sip
"Mrl": { #Mrl : QUrl
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QUrl'
    sipType = NULL;

    if (dynamic_cast<Phonon::Mrl*>(sipCpp))
        sipType = sipType_Phonon_Mrl;
%End
"""
},
# ./phonon/abstractaudiodataoutput.sip
"QSet<Phonon::Experimental::AudioFormat>": { #QSet<Phonon::Experimental::AudioFormat>
"code":
"""
%TypeHeaderCode
#include <qset.h>
#include <phonon/experimental/abstractaudiodataoutput.h>
%End
%ConvertFromTypeCode
    // Create the list.
    PyObject *l;

    if ((l = PyList_New(sipCpp->size())) == NULL)
        return NULL;

    // Set the list elements.
    QSet<Phonon::Experimental::AudioFormat> set = *sipCpp;
    int i = 0;
    foreach (Phonon::Experimental::AudioFormat value, set)
    {
        PyObject *obj = PyInt_FromLong ((long) value);
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

    QSet<Phonon::Experimental::AudioFormat> *qs = new QSet<Phonon::Experimental::AudioFormat>;

    for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i)
    {
        Phonon::Experimental::AudioFormat t = (Phonon::Experimental::AudioFormat)PyInt_AS_LONG (PyList_GET_ITEM (sipPy, i));
        *qs << t;

    }

    *sipCppPtr = qs;

    return sipGetState(sipTransferObj);
%End
"""
},
# ./phonon/videowidget.sip
"VideoWidget": { #VideoWidget : QWidget, Phonon::AbstractVideoOutput
"code":
"""
%TypeHeaderCode
#include <phonon/videowidget.h>
#include <phonon/abstractvideooutput.h>
%End
"""
},
# ./phonon/objectdescription.sip
"QList<Phonon::ObjectDescription>": { #QList<Phonon::ObjectDescription>
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
        DNSSD::RemoteService::Ptr *t = new Phonon::ObjectDescription (sipCpp->at(i));
        PyObject *tobj;

        if ((tobj = sipConvertFromNewInstance(t->data(), sipClass_DNSSD_RemoteService, sipTransferObj)) == NULL)
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
            if (!sipCanConvertToInstance(PyList_GET_ITEM(sipPy, i), sipClass_DNSSD_RemoteService, SIP_NOT_NONE))
                return 0;

        return 1;
    }

    QList<DNSSD::RemoteService::Ptr> *ql = new QList<DNSSD::RemoteService::Ptr>;

    for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i)
    {
        int state;
        DNSSD::RemoteService *t = reinterpret_cast<DNSSD::RemoteService *>(sipConvertToInstance(PyList_GET_ITEM(sipPy, i), sipClass_DNSSD_RemoteService, sipTransferObj, SIP_NOT_NONE, &state, sipIsErr));

        if (*sipIsErr)
        {
            sipReleaseInstance(t, sipClass_DNSSD_RemoteService, state);

            delete ql;
            return 0;
        }

        DNSSD::RemoteService::Ptr *tptr = new DNSSD::RemoteService::Ptr (t);

        ql->append(*tptr);

        sipReleaseInstance(t, sipClass_DNSSD_RemoteService, state);
    }

    *sipCppPtr = ql;

    return sipGetState(sipTransferObj);
%End
"""
},
# ./nepomuk/ktagcloudwidget.sip
"KTagCloudWidget": { #KTagCloudWidget : QWidget
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QWidget'
    sipType = NULL;

    if (dynamic_cast<KTagCloudWidget*>(sipCpp))
        {
        sipType = sipType_KTagCloudWidget;
        if (dynamic_cast<Nepomuk::TagCloud*>(sipCpp))
            sipType = sipType_Nepomuk_TagCloud;
        }
    else if (dynamic_cast<KTagDisplayWidget*>(sipCpp))
        sipType = sipType_KTagDisplayWidget;
    else if (dynamic_cast<Nepomuk::TagWidget*>(sipCpp))
        sipType = sipType_Nepomuk_TagWidget;
%End
"""
},
# ./nepomuk/entity.sip
"Entity": { #Entity
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'Entity'
    sipType = NULL;

    if (dynamic_cast<Nepomuk::Types::Class*>(sipCpp))
        sipType = sipType_Nepomuk_Types_Class;
    else if (dynamic_cast<Nepomuk::Types::Ontology*>(sipCpp))
        sipType = sipType_Nepomuk_Types_Ontology;
    else if (dynamic_cast<Nepomuk::Types::Property*>(sipCpp))
        sipType = sipType_Nepomuk_Types_Property;
%End
"""
},
# ./nepomuk/resource.sip
"Resource": { #Resource
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'Resource'
    sipType = NULL;

    if (dynamic_cast<Nepomuk::File*>(sipCpp))
        sipType = sipType_Nepomuk_File;
    else if (dynamic_cast<Nepomuk::Tag*>(sipCpp))
        sipType = sipType_Nepomuk_Tag;
    else if (dynamic_cast<Nepomuk::Thing*>(sipCpp))
        sipType = sipType_Nepomuk_Thing;
%End
"""
},
# ./soprano/queryresultiterator.sip
"QueryResultIterator": { #QueryResultIterator
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QueryResultIterator'
    sipType = NULL;

    if (dynamic_cast<Soprano::Client::DBusQueryResultIterator*>(sipCpp))
        sipType = sipType_Soprano_Client_DBusQueryResultIterator;
%End
"""
},
# ./soprano/statementiterator.sip
"StatementIterator": { #StatementIterator
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'StatementIterator'
    sipType = NULL;

    if (dynamic_cast<Soprano::Client::DBusStatementIterator*>(sipCpp))
        sipType = sipType_Soprano_Client_DBusStatementIterator;
    else if (dynamic_cast<Soprano::Util::SimpleStatementIterator*>(sipCpp))
        sipType = sipType_Soprano_Util_SimpleStatementIterator;
%End
"""
},
# ./soprano/plugin.sip
"Plugin": { #Plugin
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'Plugin'
    sipType = NULL;

    if (dynamic_cast<Soprano::Backend*>(sipCpp))
        sipType = sipType_Soprano_Backend;
    else if (dynamic_cast<Soprano::Parser*>(sipCpp))
        sipType = sipType_Soprano_Parser;
    else if (dynamic_cast<Soprano::Serializer*>(sipCpp))
        sipType = sipType_Soprano_Serializer;
%End
"""
},
# ./soprano/error.sip
"Error": { #Error
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'Error'
    sipType = NULL;

    if (dynamic_cast<Soprano::Error::ParserError*>(sipCpp))
        sipType = sipType_Soprano_Error_ParserError;
%End
"""
},
# ./soprano/pluginmanager.sip
"QList<const Soprano::Backend*>": { #QList<const Soprano::Backend*>
    "code": list_typecode,
    "value": {
        "type": "Soprano::Backend",
        "HeldAs": HeldAs.POINTER,
    },
},
"QList<const Soprano::Parser*>": { #QList<const Soprano::Parser*>
    "code": list_typecode,
    "value": {
        "type": "Soprano::Parser",
        "HeldAs": HeldAs.POINTER,
    },
},
"QList<const Soprano::Serializer*>": { #QList<const Soprano::Serializer*>
    "code": list_typecode,
    "value": {
        "type": "Soprano::Serializer",
        "HeldAs": HeldAs.POINTER,
    },
},
# ./soprano/model.sip
"Model": { #Model : QObject, Soprano::Error::ErrorCache
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QObject'
    sipType = NULL;

    if (dynamic_cast<Soprano::Client::DBusClient*>(sipCpp))
        sipType = sipType_Soprano_Client_DBusClient;
    else if (dynamic_cast<Soprano::Client::LocalSocketClient*>(sipCpp))
        sipType = sipType_Soprano_Client_LocalSocketClient;
    else if (dynamic_cast<Soprano::Client::TcpClient*>(sipCpp))
        sipType = sipType_Soprano_Client_TcpClient;
    else if (dynamic_cast<Soprano::Model*>(sipCpp))
        {
        sipType = sipType_Soprano_Model;
        if (dynamic_cast<Soprano::Client::SparqlModel*>(sipCpp))
            sipType = sipType_Soprano_Client_SparqlModel;
        else if (dynamic_cast<Soprano::FilterModel*>(sipCpp))
            {
            sipType = sipType_Soprano_FilterModel;
            if (dynamic_cast<Soprano::Inference::InferenceModel*>(sipCpp))
                sipType = sipType_Soprano_Inference_InferenceModel;
            else if (dynamic_cast<Soprano::NRLModel*>(sipCpp))
                sipType = sipType_Soprano_NRLModel;
            else if (dynamic_cast<Soprano::Server::DBusExportModel*>(sipCpp))
                sipType = sipType_Soprano_Server_DBusExportModel;
            else if (dynamic_cast<Soprano::Util::AsyncModel*>(sipCpp))
                sipType = sipType_Soprano_Util_AsyncModel;
            else if (dynamic_cast<Soprano::Util::MutexModel*>(sipCpp))
                sipType = sipType_Soprano_Util_MutexModel;
            else if (dynamic_cast<Soprano::Util::SignalCacheModel*>(sipCpp))
                sipType = sipType_Soprano_Util_SignalCacheModel;
            }
        else if (dynamic_cast<Soprano::StorageModel*>(sipCpp))
            {
            sipType = sipType_Soprano_StorageModel;
            if (dynamic_cast<Soprano::Client::DBusModel*>(sipCpp))
                sipType = sipType_Soprano_Client_DBusModel;
            }
        else if (dynamic_cast<Soprano::Util::DummyModel*>(sipCpp))
            sipType = sipType_Soprano_Util_DummyModel;
        }
    else if (dynamic_cast<Soprano::PluginManager*>(sipCpp))
        sipType = sipType_Soprano_PluginManager;
    else if (dynamic_cast<Soprano::Server::DBusExportIterator*>(sipCpp))
        sipType = sipType_Soprano_Server_DBusExportIterator;
    else if (dynamic_cast<Soprano::Server::ServerCore*>(sipCpp))
        sipType = sipType_Soprano_Server_ServerCore;
    else if (dynamic_cast<Soprano::Util::AsyncQuery*>(sipCpp))
        sipType = sipType_Soprano_Util_AsyncQuery;
    else if (dynamic_cast<Soprano::Util::AsyncResult*>(sipCpp))
        sipType = sipType_Soprano_Util_AsyncResult;
%End
"""
},
# ./soprano/tcpclient.sip
"TcpClient": { #TcpClient : QObject, Soprano::Error::ErrorCache
"code":
"""
%TypeHeaderCode
#include <soprano/tcpclient.h>
#include <soprano/servercore.h>
%End
"""
},
# ./soprano/nodeiterator.sip
"NodeIterator": { #NodeIterator
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'NodeIterator'
    sipType = NULL;

    if (dynamic_cast<Soprano::Client::DBusNodeIterator*>(sipCpp))
        sipType = sipType_Soprano_Client_DBusNodeIterator;
    else if (dynamic_cast<Soprano::Util::SimpleNodeIterator*>(sipCpp))
        sipType = sipType_Soprano_Util_SimpleNodeIterator;
%End
"""
},
# ./kdecore/kmimetype.sip
"QList<KMimeType::Ptr>": { #QList<KMimeType::Ptr>
    "code": list_typecode,
    "value": {
        "type": "KMimeType",
        "ptr": "KMimeType::Ptr",
        "HeldAs": HeldAs.POINTER,
    },
},
# ./kdecore/kurl.sip
"KUrl": { #KUrl : QUrl
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QUrl'
    sipType = NULL;

    if (dynamic_cast<KUrl*>(sipCpp))
        sipType = sipType_KUrl;
%End
"""
},
# ./kdecore/kcmdlineargs.sip
"KCmdLineOptions": { #KCmdLineOptions
"code":
"""
%TypeHeaderCode
#include <kcmdlineargs.h>
extern char **pyArgvToC(PyObject *argvlist,int *argcp);
extern void updatePyArgv(PyObject *argvlist,int argc,char **argv);
%End
"""
},
"KCmdLineArgs": { #KCmdLineArgs
"code":
"""
%TypeHeaderCode
#include <kcmdlineargs.h>
#include <qapplication.h>
extern char **pyArgvToC(PyObject *argvlist,int *argcp);
extern void updatePyArgv(PyObject *argvlist,int argc,char **argv);
%End
"""
},
# ./kdecore/kconfig.sip
"kconfig.h::KConfig": { #KConfig : KConfigBase
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'KConfigBase'
    sipType = NULL;

    if (dynamic_cast<KConfig*>(sipCpp))
        {
        sipType = sipType_KConfig;
        if (dynamic_cast<KDesktopFile*>(sipCpp))
            sipType = sipType_KDesktopFile;
        else if (dynamic_cast<KSharedConfig*>(sipCpp))
            sipType = sipType_KSharedConfig;
        }
    else if (dynamic_cast<KConfigGroup*>(sipCpp))
        sipType = sipType_KConfigGroup;
%End
"""
},
"KSharedPtr<TYPE>": { #KSharedPtr<TYPE>
"code":
"""
%ConvertFromTypeCode
    // Convert to a Python instance

    if (!sipCpp)
        return NULL;

    KSharedPtr<TYPE> *cPtr = new KSharedPtr<TYPE> (*(KSharedPtr<TYPE> *)sipCpp);
    TYPE *cpp = cPtr->data ();
    PyObject *obj = sipConvertFromType(cpp, sipType_TYPE, sipTransferObj);

    return obj;
%End
%ConvertToTypeCode
    // Convert a Python instance to a Ptr on the heap.
    if (sipIsErr == NULL) {
        return 1;
    }

    int iserr = 0;
    TYPE *cpp = (TYPE *)sipForceConvertToType(sipPy, sipType_TYPE, NULL, 0, NULL, &iserr);

    if (iserr)
    {
        *sipIsErr = 1;
        return 0;
    }

    *sipCppPtr = new KSharedPtr<TYPE> (cpp);

    return 1;
%End
"""
},
"QHash<TYPE1,TYPE2>": { #QHash<TYPE1,TYPE2>
"code":
"""
%ConvertFromTypeCode
    // Create the dictionary.
    PyObject *d = PyDict_New();

    if (!d)
        return NULL;

    // Set the dictionary elements.
    QHash<TYPE1, TYPE2>::const_iterator i = sipCpp->constBegin();

    while (i != sipCpp->constEnd())
    {
        TYPE1 *t1 = new TYPE1(i.key());
        TYPE2 *t2 = new TYPE2(i.value());

        PyObject *t1obj = sipConvertFromNewInstance(t1, sipClass_TYPE1, sipTransferObj);
        PyObject *t2obj = sipConvertFromNewInstance(t2, sipClass_TYPE2, sipTransferObj);

        if (t1obj == NULL || t2obj == NULL || PyDict_SetItem(d, t1obj, t2obj) < 0)
        {
            Py_DECREF(d);

            if (t1obj)
                Py_DECREF(t1obj);
            else
                delete t1;

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
            if (!sipCanConvertToInstance(t1obj, sipClass_TYPE1, SIP_NOT_NONE))
                return 0;

            if (!sipCanConvertToInstance(t2obj, sipClass_TYPE2, SIP_NOT_NONE))
                return 0;
        }

        return 1;
    }

    QHash<TYPE1, TYPE2> *qm = new QHash<TYPE1, TYPE2>;

    while (PyDict_Next(sipPy, &i, &t1obj, &t2obj))
    {
        int state1, state2;

        TYPE1 *t1 = reinterpret_cast<TYPE1 *>(sipConvertToInstance(t1obj, sipClass_TYPE1, sipTransferObj, SIP_NOT_NONE, &state1, sipIsErr));
        TYPE2 *t2 = reinterpret_cast<TYPE2 *>(sipConvertToInstance(t2obj, sipClass_TYPE2, sipTransferObj, SIP_NOT_NONE, &state2, sipIsErr));

        if (*sipIsErr)
        {
            sipReleaseInstance(t1, sipClass_TYPE1, state1);
            sipReleaseInstance(t2, sipClass_TYPE2, state2);

            delete qm;
            return 0;
        }

        qm->insert(*t1, *t2);

        sipReleaseInstance(t1, sipClass_TYPE1, state1);
        sipReleaseInstance(t2, sipClass_TYPE2, state2);
    }

    *sipCppPtr = qm;

    return sipGetState(sipTransferObj);
%End
"""
},
"QHash<TYPE1,TYPE2*>": { #QHash<TYPE1,TYPE2*>
"code":
"""
%ConvertFromTypeCode
    // Create the dictionary.
    PyObject *d = PyDict_New();

    if (!d)
        return NULL;

    // Set the dictionary elements.
    QHash<TYPE1, TYPE2*>::const_iterator i = sipCpp->constBegin();

    while (i != sipCpp->constEnd())
    {
        TYPE1 *t1 = new TYPE1(i.key());
        TYPE2 *t2 = i.value();

        PyObject *t1obj = sipConvertFromNewType(t1, sipType_TYPE1, sipTransferObj);
        PyObject *t2obj = sipConvertFromNewType(t2, sipType_TYPE2, sipTransferObj);

        if (t1obj == NULL || t2obj == NULL || PyDict_SetItem(d, t1obj, t2obj) < 0)
        {
            Py_DECREF(d);

            if (t1obj)
                Py_DECREF(t1obj);
            else
                delete t1;

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
            if (!sipCanConvertToType(t1obj, sipType_TYPE1, SIP_NOT_NONE))
                return 0;

            if (!sipCanConvertToType(t2obj, sipType_TYPE2, SIP_NOT_NONE))
                return 0;
        }

        return 1;
    }

    QHash<TYPE1, TYPE2*> *qm = new QHash<TYPE1, TYPE2*>;

    while (PyDict_Next(sipPy, &i, &t1obj, &t2obj))
    {
        int state1, state2;

        TYPE1 *t1 = reinterpret_cast<TYPE1 *>(sipConvertToType(t1obj, sipType_TYPE1, sipTransferObj, SIP_NOT_NONE, &state1, sipIsErr));
        TYPE2 *t2 = reinterpret_cast<TYPE2 *>(sipConvertToType(t2obj, sipType_TYPE2, sipTransferObj, SIP_NOT_NONE, &state2, sipIsErr));

        if (*sipIsErr)
        {
            sipReleaseType(t1, sipType_TYPE1, state1);
            sipReleaseType(t2, sipType_TYPE2, state2);

            delete qm;
            return 0;
        }

        qm->insert(*t1, t2);

        sipReleaseType(t1, sipType_TYPE1, state1);
        sipReleaseType(t2, sipType_TYPE2, state2);
    }

    *sipCppPtr = qm;

    return sipGetState(sipTransferObj);
%End
"""
},
"QPair<TYPE1,TYPE2>": { #QPair<TYPE1,TYPE2>
"code":
"""
%ConvertFromTypeCode
    // Create the tuple.
    TYPE1 *t1 = new TYPE1(sipCpp->first);
    TYPE2 *t2 = new TYPE2(sipCpp->second);

    PyObject *t1obj = sipConvertFromNewType(t1, sipType_TYPE1, sipTransferObj);
    PyObject *t2obj = sipConvertFromNewType(t2, sipType_TYPE2, sipTransferObj);

    if (t1obj == NULL || t2obj == NULL)
    {
        if (t1obj)
            Py_DECREF(t1obj);
        else
            delete t1;

        if (t2obj)
            Py_DECREF(t2obj);
        else
            delete t2;

        return NULL;
    }

    return Py_BuildValue((char *)"NN", t1obj, t2obj);
%End
%ConvertToTypeCode
    // Check the type if that is all that is required.
    if (sipIsErr == NULL)
        return (PyTuple_Size(sipPy) == 2);


    int state1, state2;

    PyObject *t1obj = PyTuple_GET_ITEM(sipPy, 0);
    PyObject *t2obj = PyTuple_GET_ITEM(sipPy, 1);

    TYPE1 *t1 = reinterpret_cast<TYPE1 *>(sipConvertToType(t1obj, sipType_TYPE1, sipTransferObj, SIP_NOT_NONE, &state1, sipIsErr));
    TYPE2 *t2 = reinterpret_cast<TYPE2 *>(sipConvertToType(t2obj, sipType_TYPE2, sipTransferObj, SIP_NOT_NONE, &state2, sipIsErr));

    if (*sipIsErr)
    {
        sipReleaseType(t1, sipType_TYPE1, state1);
        sipReleaseType(t2, sipType_TYPE2, state2);

        return 0;
    }

    QPair<TYPE1, TYPE2> *qp = new QPair<TYPE1, TYPE2>;

    qp->first  = *t1;
    qp->second = *t2;

    *sipCppPtr = qp;

    return sipGetState(sipTransferObj);
%End
"""
},
"QStack<TYPE*>": { #QStack<TYPE*>
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
        TYPE *t = (TYPE *)(sipCpp->at(i));
        PyObject *tobj;

        if ((tobj = sipConvertFromNewInstance(t, sipClass_TYPE, sipTransferObj)) == NULL)
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
            if (!sipCanConvertToInstance(PyList_GET_ITEM(sipPy, i), sipClass_TYPE, SIP_NOT_NONE))
                return 0;

        return 1;
    }

    QStack<TYPE*> *qv = new QStack<TYPE*>;

    for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i)
    {
        int state;
        TYPE *t = reinterpret_cast<TYPE *>(sipConvertToInstance(PyList_GET_ITEM(sipPy, i), sipClass_TYPE, sipTransferObj, SIP_NOT_NONE, &state, sipIsErr));

        if (*sipIsErr)
        {
            sipReleaseInstance(t, sipClass_TYPE, state);

            delete qv;
            return 0;
        }

        qv->append(t);

        sipReleaseInstance(t, sipClass_TYPE, state);
    }

    *sipCppPtr = qv;

    return sipGetState(sipTransferObj);
%End
"""
},
"QHash<int,int>": { #QHash<int,int>
"code":
"""
%ConvertFromTypeCode
    // Create the dictionary.
    PyObject *d = PyDict_New();

    if (!d)
        return NULL;

    // Set the dictionary elements.
    QHash<int, int>::const_iterator i = sipCpp->constBegin();

    while (i != sipCpp->constEnd())
    {
        int t1 = i.key();
        int t2 = i.value();

#if PY_MAJOR_VERSION >= 3
        PyObject *t1obj = PyLong_FromLong ((long)t1);
        PyObject *t2obj = PyLong_FromLong ((long)t2);
#else
        PyObject *t1obj = PyInt_FromLong ((long)t1);
        PyObject *t2obj = PyInt_FromLong ((long)t2);
#endif

        if (PyDict_SetItem(d, t1obj, t2obj) < 0)
        {
            Py_DECREF(d);

            if (t1obj)
                Py_DECREF(t1obj);

            if (t2obj)
                Py_DECREF(t2obj);

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

#if PY_MAJOR_VERSION >= 3
            if (!PyNumber_Check (t2obj))
#else
            if (!PyInt_Check (t2obj))
#endif
                return 0;
        }

        return 1;
    }

    QHash<int, int> *qm = new QHash<int, int>;

    while (PyDict_Next(sipPy, &i, &t1obj, &t2obj))
    {
        int state2;

#if PY_MAJOR_VERSION >= 3
        int t1 = PyLong_AsLong (t1obj);
#else
        int t1 = PyInt_AS_LONG (t1obj);
#endif

#if PY_MAJOR_VERSION >= 3
        int t2 = PyLong_AsLong (t2obj);
#else
        int t2 = PyInt_AS_LONG (t2obj);
#endif

        if (*sipIsErr)
        {
            delete qm;
            return 0;
        }

        qm->insert(t1, t2);
    }

    *sipCppPtr = qm;

    return sipGetState(sipTransferObj);
%End
"""
},
"QHash<TYPE1,bool>": { #QHash<TYPE1,bool>
"code":
"""
%ConvertFromTypeCode
    // Create the dictionary.
    PyObject *d = PyDict_New();

    if (!d)
        return NULL;

    // Set the dictionary elements.
    QHash<TYPE1, bool>::const_iterator i = sipCpp->constBegin();

    while (i != sipCpp->constEnd())
    {
        TYPE1 *t1 = new TYPE1(i.key());
        bool t2 = i.value();

        PyObject *t1obj = sipConvertFromNewType(t1, sipType_TYPE1, sipTransferObj);
#if PY_MAJOR_VERSION >= 3
        PyObject *t2obj = PyBool_FromLong ((long)t2);
#else
        PyObject *t2obj = PyBool_FromLong ((long)t2);
#endif

        if (t1obj == NULL || t2obj == NULL || PyDict_SetItem(d, t1obj, t2obj) < 0)
        {
            Py_DECREF(d);

            if (t1obj) {
                Py_DECREF(t1obj);
            } else {
                delete t1;
            }

            if (t2obj) {
                Py_DECREF(t2obj);
            }

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
            if (!sipCanConvertToType(t1obj, sipType_TYPE1, SIP_NOT_NONE))
                return 0;

#if PY_MAJOR_VERSION >= 3
            if (!PyBool_Check (t2obj))
#else
            if (!PyBool_Check (t2obj))
#endif
                return 0;
        }

        return 1;
    }

    QHash<TYPE1, bool> *qm = new QHash<TYPE1, bool>;

    while (PyDict_Next(sipPy, &i, &t1obj, &t2obj))
    {
        int state1, state2;

        TYPE1 *t1 = reinterpret_cast<TYPE1 *>(sipConvertToType(t1obj, sipType_TYPE1, sipTransferObj, SIP_NOT_NONE, &state1, sipIsErr));
#if PY_MAJOR_VERSION >= 3
        bool t2 = PyObject_IsTrue(t2obj);
#else
        bool t2 = PyObject_IsTrue (t2obj);
#endif

        if (*sipIsErr)
        {
            sipReleaseType(t1, sipType_TYPE1, state1);

            delete qm;
            return 0;
        }

        qm->insert(*t1, t2);

        sipReleaseType(t1, sipType_TYPE1, state1);
    }

    *sipCppPtr = qm;

    return sipGetState(sipTransferObj);
%End
"""
},
"QVector<int>": { #QVector<int>
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
        int t = (sipCpp->at(i));

#if PY_MAJOR_VERSION >= 3
        PyObject *tobj = PyLong_FromLong(t);
#else
        PyObject *tobj = PyInt_FromLong(t);
#endif

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

        for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i) {
            PyObject *tobj = PyList_GET_ITEM(sipPy, i);
#if PY_MAJOR_VERSION >= 3
            if (!PyNumber_Check(tobj))
#else
            if (!PyInt_Check(tobj))
#endif
                return 0;
        }
        return 1;
    }

    QVector<int> *qv = new QVector<int>;

    for (int i = 0; i < PyList_GET_SIZE(sipPy); ++i)
    {
        PyObject *tobj = PyList_GET_ITEM(sipPy, i);
#if PY_MAJOR_VERSION >= 3
        int t = PyLong_AsLong (tobj);
#else
        int t = PyInt_AS_LONG (tobj);
#endif

        if (*sipIsErr)
        {
            delete qv;
            return 0;
        }

        qv->append(t);
    }

    *sipCppPtr = qv;

    return sipGetState(sipTransferObj);
%End
"""
},
# ./kdecore/ktimezone.sip
"KTimeZone": { #KTimeZone
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'KTimeZone'
    sipType = NULL;

    if (dynamic_cast<KSystemTimeZone*>(sipCpp))
        sipType = sipType_KSystemTimeZone;
    else if (dynamic_cast<KTzfileTimeZone*>(sipCpp))
        sipType = sipType_KTzfileTimeZone;
%End
"""
},
"KTimeZoneBackend": { #KTimeZoneBackend
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'KTimeZoneBackend'
    sipType = NULL;

    if (dynamic_cast<KSystemTimeZoneBackend*>(sipCpp))
        sipType = sipType_KSystemTimeZoneBackend;
    else if (dynamic_cast<KTzfileTimeZoneBackend*>(sipCpp))
        sipType = sipType_KTzfileTimeZoneBackend;
%End
"""
},
"KTimeZoneSource": { #KTimeZoneSource
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'KTimeZoneSource'
    sipType = NULL;

    if (dynamic_cast<KSystemTimeZoneSource*>(sipCpp))
        sipType = sipType_KSystemTimeZoneSource;
    else if (dynamic_cast<KTzfileTimeZoneSource*>(sipCpp))
        sipType = sipType_KTzfileTimeZoneSource;
%End
"""
},
# ./kdecore/kmacroexpander.sip
"kmacroexpander.h::KCharMacroExpander": { #KCharMacroExpander : KMacroExpanderBase
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'KMacroExpanderBase'
    sipType = NULL;

    if (dynamic_cast<KCharMacroExpander*>(sipCpp))
        sipType = sipType_KCharMacroExpander;
    else if (dynamic_cast<KWordMacroExpander*>(sipCpp))
        sipType = sipType_KWordMacroExpander;
%End
"""
},
# ./dnssd/remoteservice.sip
"QList<DNSSD::RemoteService::Ptr>": { #QList<DNSSD::RemoteService::Ptr>
    "code": list_typecode,
    "value": {
        "type": "DNSSD::RemoteService",
        "ptr": "DNSSD::RemoteService::Ptr",
        "HeldAs": HeldAs.POINTER,
    },
},
# ./dnssd/servicebase.sip
"KDNSSD::ServiceBase": { #ServiceBase : KShared
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'ServiceBase'
    sipType = NULL;

    if (dynamic_cast<DNSSD::ServiceBase*>(sipCpp))
        {
        sipType = sipType_DNSSD_ServiceBase;
        if (dynamic_cast<DNSSD::PublicService*>(sipCpp))
            sipType = sipType_DNSSD_PublicService;
        else if (dynamic_cast<DNSSD::RemoteService*>(sipCpp))
            sipType = sipType_DNSSD_RemoteService;
        }
%End
"""
},
# ./dnssd/domainbrowser.sip
"KDNSSD::DomainBrowser": { #DomainBrowser : QObject
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QObject'
    sipType = NULL;

    if (dynamic_cast<DNSSD::DomainBrowser*>(sipCpp))
        sipType = sipType_DNSSD_DomainBrowser;
    else if (dynamic_cast<DNSSD::PublicService*>(sipCpp))
        sipType = sipType_DNSSD_PublicService;
    else if (dynamic_cast<DNSSD::RemoteService*>(sipCpp))
        sipType = sipType_DNSSD_RemoteService;
    else if (dynamic_cast<DNSSD::ServiceBrowser*>(sipCpp))
        sipType = sipType_DNSSD_ServiceBrowser;
    else if (dynamic_cast<DNSSD::ServiceTypeBrowser*>(sipCpp))
        sipType = sipType_DNSSD_ServiceTypeBrowser;
    else if (dynamic_cast<DNSSD::DomainModel*>(sipCpp))
        sipType = sipType_DNSSD_DomainModel;
    else if (dynamic_cast<DNSSD::ServiceModel*>(sipCpp))
        sipType = sipType_DNSSD_ServiceModel;
%End
"""
},
# ./kutils/dialog.sip
"Dialog": { #Dialog : KCMultiDialog
"code":
"""
%TypeHeaderCode
#include <dialog.h>
#include <kcmultidialog.h>
%End
"""
},
# ./kterminal/kterminal.sip
"KTerminal": { #KTerminal
"code":
"""
%TypeHeaderCode
#include <kde_terminal_interface.h>
#include <kde_terminal_interface_v2.h>
#include <kparts/part.h>
%End
"""
},
# ./kdeui/kpixmapcache.sip
"KPixmapCache": { #KPixmapCache
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'KPixmapCache'
    sipType = NULL;

    if (dynamic_cast<KIconCache*>(sipCpp))
        sipType = sipType_KIconCache;
%End
"""
},
# ./kdeui/kwidgetitemdelegate.sip
"QList<QEvent::Type>": { #QList<QEvent::Type>
    "code": list_typecode,
    "value": {
        "type": "QEvent::Type",
        "HeldAs": HeldAs.INTEGER,
    },
},
# ./kdeui/kcursor.sip
"kcursor.h::KCursor": { #KCursor : QCursor
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QCursor'
    sipType = NULL;

    if (dynamic_cast<KCursor*>(sipCpp))
        sipType = sipType_KCursor;
%End
"""
},
# ./kdeui/kapplication.sip
"KApplication": { #KApplication : QApplication
"code":
"""
%TypeCode
// Convert a Python argv list to a conventional C argc count and argv array.
static char **kdeui_ArgvToC(PyObject *argvlist, int &argc)
{
    char **argv;

    argc = PyList_GET_SIZE(argvlist);

    // Allocate space for two copies of the argument pointers, plus the
    // terminating NULL.
    if ((argv = (char **)sipMalloc(2 * (argc + 1) * sizeof (char *))) == NULL)
        return NULL;

    // Convert the list.
    for (int a = 0; a < argc; ++a)
    {
        char *arg;
#if PY_MAJOR_VERSION >= 3
        PyObject *utf8bytes = PyUnicode_AsUTF8String(PyList_GetItem(argvlist,a));
        arg = PyBytes_AsString(utf8bytes);
#else
        arg = PyString_AsString(PyList_GetItem(argvlist,a));
#endif
        // Get the argument and allocate memory for it.
        if (arg == NULL ||
            (argv[a] = (char *)sipMalloc(strlen(arg) + 1)) == NULL)
            return NULL;

        // Copy the argument and save a pointer to it.
        strcpy(argv[a], arg);
        argv[a + argc + 1] = argv[a];
#if PY_MAJOR_VERSION >= 3
        Py_DECREF(utf8bytes);
#endif
    }

    argv[argc + argc + 1] = argv[argc] = NULL;

    return argv;
}


// Remove arguments from the Python argv list that have been removed from the
// C argv array.
static void kdeui_UpdatePyArgv(PyObject *argvlist, int argc, char **argv)
{
    for (int a = 0, na = 0; a < argc; ++a)
    {
        // See if it was removed.
        if (argv[na] == argv[a + argc + 1])
            ++na;
        else
            PyList_SetSlice(argvlist, na, na + 1, NULL);
    }
}
%End
"""
},
# ./kdeui/kstandardaction.sip
"QList<KStandardAction::StandardAction>": { #QList<KStandardAction::StandardAction>
    "code": list_typecode,
    "value": {
        "type": "KStandardAction::StandardAction",
        "HeldAs": HeldAs.INTEGER,
    },
},
# ./kdeui/kicon.sip
"KIcon": { #KIcon : QIcon
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'QIcon'
    sipType = NULL;

    if (dynamic_cast<KIcon*>(sipCpp))
        sipType = sipType_KIcon;
%End
"""
},
# ./kdeui/kiconcache.sip
"KIconCache": { #KIconCache : KPixmapCache
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'KPixmapCache'
    sipType = NULL;

    if (dynamic_cast<KIconCache*>(sipCpp))
        sipType = sipType_KIconCache;
%End
"""
},
# ./kdeui/kconfigskeleton.sip
"kconfigskeleton.h::KConfigSkeleton": { #KConfigSkeleton : KCoreConfigSkeleton
"code":
"""
%ConvertToSubClassCode
    // CTSCC for subclasses of 'KConfigSkeletonItem'
    sipType = NULL;

    if (dynamic_cast<KConfigSkeleton::ItemColor*>(sipCpp))
        sipType = sipType_KConfigSkeleton_ItemColor;
    else if (dynamic_cast<KConfigSkeleton::ItemFont*>(sipCpp))
        sipType = sipType_KConfigSkeleton_ItemFont;
%End
"""
},
# ./kdeui/kwindowsystem.sip
"QList<WId>": { #QList<WId>
    "code": list_typecode,
    "value": {
        "type": "WId",
        "HeldAs": HeldAs.INTEGER,
    },
},
}
