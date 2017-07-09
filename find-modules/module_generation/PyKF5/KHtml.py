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
SIP binding customisation for PyKF5.KHtml. This modules describes:

    * Supplementary SIP file generator rules.
"""

import rule_helpers


def module_fix_mapped_types(filename, sip, entry):
    #
    # SIP cannot handle duplicate %MappedTypes.
    #
    rule_helpers.modulecode_delete(filename, sip, entry, "QMap<QString, QString>")
    rule_helpers.code_add_classes(filename, sip, entry, "DOM::CSSRuleImpl")

def module_fix_mapped_types_dom(filename, sip, entry):
    rule_helpers.code_add_classes(filename, sip, entry, "DOM::AbstractViewImpl", "DOM::AttrImpl",
                                  "DOM::CDATASectionImpl", "DOM::CharacterDataImpl", "DOM::CommentImpl",
                                  "DOM::CounterImpl", "DOM::CSSCharsetRuleImpl", "DOM::CSSFontFaceRuleImpl",
                                  "DOM::CSSImportRuleImpl", "DOM::CSSMediaRuleImpl", "DOM::CSSNamespaceRuleImpl",
                                  "DOM::CSSPageRuleImpl", "DOM::CSSPrimitiveValueImpl", "DOM::CSSRuleImpl",
                                  "DOM::CSSRuleListImpl", "DOM::CSSStyleDeclarationImpl", "DOM::CSSStyleRuleImpl",
                                  "DOM::CSSStyleSheetImpl", "DOM::CSSUnknownRuleImpl", "DOM::CSSValueImpl",
                                  "DOM::CSSValueListImpl", "DOM::DocumentFragmentImpl", "DOM::DocumentImpl",
                                  "DOM::DocumentTypeImpl", "DOM::DOMImpl", "DOM::DOMImplementationImpl",
                                  "DOM::DOMStringImpl", "DOM::ElementImpl", "DOM::EntityImpl",
                                  "DOM::EntityReferenceImpl", "DOM::EventImpl", "DOM::HTMLAnchorElementImpl",
                                  "DOM::HTMLAppletElementImpl", "DOM::HTMLAreaElementImpl", "DOM::HTMLBaseElementImpl",
                                  "DOM::HTMLBaseFontElementImpl", "DOM::HTMLBodyElementImpl", "DOM::HTMLBRElementImpl",
                                  "DOM::HTMLButtonElementImpl", "DOM::HTMLCollectionImpl",
                                  "DOM::HTMLDirectoryElementImpl", "DOM::HTMLDivElementImpl",
                                  "DOM::HTMLDListElementImpl", "DOM::HTMLDocumentImpl", "DOM::HTMLElementImpl",
                                  "DOM::HTMLFieldSetElementImpl", "DOM::HTMLFontElementImpl",
                                  "DOM::HTMLFormElementImpl", "DOM::HTMLFrameElementImpl",
                                  "DOM::HTMLFrameSetElementImpl", "DOM::HTMLGenericElementImpl",
                                  "DOM::HTMLGenericFormElementImpl", "DOM::HTMLHeadElementImpl",
                                  "DOM::HTMLHRElementImpl", "DOM::HTMLHtmlElementImpl", "DOM::HTMLIFrameElementImpl",
                                  "DOM::HTMLImageElementImpl", "DOM::HTMLInputElementImpl",
                                  "DOM::HTMLIsIndexElementImpl", "DOM::HTMLLabelElementImpl",
                                  "DOM::HTMLLayerElementImpl", "DOM::HTMLLegendElementImpl", "DOM::HTMLLIElementImpl",
                                  "DOM::HTMLLinkElementImpl", "DOM::HTMLMapElementImpl", "DOM::HTMLMenuElementImpl",
                                  "DOM::HTMLMetaElementImpl", "DOM::HTMLObjectBaseElementImpl",
                                  "DOM::HTMLObjectElementImpl", "DOM::HTMLOListElementImpl",
                                  "DOM::HTMLOptGroupElementImpl", "DOM::HTMLOptionElementImpl",
                                  "DOM::HTMLParamElementImpl", "DOM::HTMLPartContainerElementImpl",
                                  "DOM::HTMLPreElementImpl", "DOM::HTMLScriptElementImpl", "DOM::HTMLSelectElementImpl",
                                  "DOM::HTMLStyleElementImpl", "DOM::HTMLTableCaptionElementImpl",
                                  "DOM::HTMLTableCellElementImpl", "DOM::HTMLTableColElementImpl",
                                  "DOM::HTMLTableElementImpl", "DOM::HTMLTableRowElementImpl",
                                  "DOM::HTMLTableSectionElementImpl", "DOM::HTMLTextAreaElementImpl",
                                  "DOM::HTMLTitleElementImpl", "DOM::HTMLUListElementImpl", "DOM::MediaListImpl",
                                  "DOM::MouseEventImpl", "DOM::MutationEventImpl", "DOM::NamedNodeMapImpl",
                                  "DOM::NodeFilterImpl", "DOM::NodeImpl", "DOM::NodeIteratorImpl", "DOM::NodeListImpl",
                                  "DOM::NotationImpl", "DOM::ProcessingInstructionImpl", "DOM::RangeImpl",
                                  "DOM::RectImpl", "DOM::StyleListImpl", "DOM::StyleSheetImpl",
                                  "DOM::StyleSheetListImpl", "DOM::TextImpl", "DOM::TreeWalkerImpl", "DOM::UIEventImpl",
                                  "KHTMLView")


def modulecode():
    return {
        "KHtmlmod.sip": {
            "code": module_fix_mapped_types,
        },
        "dommod.sip": {
            "code": module_fix_mapped_types_dom,
        },
    }
