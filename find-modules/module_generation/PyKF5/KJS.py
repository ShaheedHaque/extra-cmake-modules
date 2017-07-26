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
SIP binding customisation for PyKF5.KJS. This modules describes:

    * Supplementary SIP file generator rules.
"""

from clang.cindex import StorageClass

import builtin_rules
import rule_helpers
import rules_engine


def function_discard_inlines(container, function, sip, matcher):
    if function.storage_class == StorageClass.NONE:
        rule_helpers.function_discard(container, function, sip, matcher)


def container_fix_template_w_literal_compilestate(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "WTF::Vector<unsigned char, 0>",
                                                 "WTF::Vector<KJS::CompileState::NestInfo, 0>")


def container_fix_template_w_literal_localstorage(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "WTF::Vector<KJS::LocalStorageEntry, 32>")



def container_fix_template_w_literal_opcodes(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "WTF::Vector<unsigned char, 0>")


def container_fix_template_w_literal_nodes(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "WTF::Vector<unsigned char, 0>")


def container_fix_template_w_literal_ustring(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "WTF::Vector<KJS::UChar, 0>")


def container_fix_fn_ptr(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "bool (*f)(int)",
                                                 "WTF::Vector<KJS::UChar, 0>")


def container_fix_typename_countedset(container, sip, matcher):
    clazz = "typename HashMap<Value, unsigned int, HashFunctions, Traits, HashTraits<unsigned int> >"
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, clazz + "::iterator",
                                                      clazz + "::const_iterator")


def container_fix_typename_hashmaphm(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "typename KeyTraitsArg::TraitType",
                                                 "typename MappedTraitsArg::TraitType",
                                                 "typename PairHashTraits<KeyTraitsArg, MappedTraitsArg>::TraitType")


def container_fix_typename_hashmappfe(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "typename PairType::first_type")


def container_fix_typename_hashmaphmt(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "typename ValueType::first_type",
                                                 "typename ValueType::second_type")


def container_fix_typename_hashset(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "typename KeyTraitsArg::TraitType",
                                                 "HashSet<Value, HashFunctions, Traits>",
                                                 "typename TraitsArg::TraitType")


def container_fix_typename_hashtable(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher,
                                                 "HashTableIterator<Key, Value, Extractor, HashFunctions, Traits, KeyTraits>",
                                                 "HashTableConstIterator<Key, Value, Extractor, HashFunctions, Traits, KeyTraits>",
                                                 "IdentityHashTranslator<Key, Value, HashFunctions>")


def container_fix_typename_hashtableia(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "typename HashTableType::const_iterator",
                                                 "typename HashTableType::iterator")


def container_fix_typename_hashtraits(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "typename FirstTraitsArg::TraitType",
                                                 "typename SecondTraitsArg::TraitType",
                                                 "GenericHashTraits<pair<typename FirstTraitsArg::TraitType, typename SecondTraitsArg::TraitType> >")
    sip["base_specifiers"][0] = "__2_t"


def container_fix_typename_refptrhashmap(container, sip, matcher):
    rule_helpers.container_add_supplementary_typedefs(container, sip, matcher, "typename ValueType::first_type",
                                                 "typename ValueType::second_type", "typename ValueTraits::FirstTraits",
                                                 "typename ValueTraits::SecondTraits")


def variable_rewrite_array(container, variable, sip, matcher):
    builtin_rules.variable_rewrite_extern(container, variable, sip, matcher)
    sip["code"] += """
{
%GetCode
// TODO
%End
}"""


def variable_rewrite_array_rw(container, variable, sip, matcher):
    builtin_rules.variable_rewrite_extern(container, variable, sip, matcher)
    variable_rewrite_rw(container, variable, sip, matcher)


def variable_rewrite_rw(container, variable, sip, matcher):
    sip["code"] += """
{
%GetCode
// TODO
%End

%SetCode
// TODO
%End
}"""


def module_discard_duplicate(filename, sip, entry):
    if sip["name"] != filename:
        sip["name"] = ""


def module_fix_kjs(filename, sip, matcher):
    #
    # Fixup the recursion.
    #
    lines = []
    for l in sip["decl"].split("\n"):
        if "kjs/bytecode/bytecodemod.sip" in l:
            #
            # These modules refer to each other.
            #
            lines.append("%If (KJsEmbed_KJsEmbed_KJsEmbedmod)")
            lines.append(l)
            lines.append("%End")
            continue
        lines.append(l)
    sip["decl"] = "\n".join(lines)


def module_fix_wtf(filename, sip, matcher):
    #
    # Fixup the recursion.
    #
    lines = []
    for l in sip["decl"].split("\n"):
        if "kjs/kjsmod.sip" in l:
            #
            # These modules refer to each other.
            #
            lines.append("// " + l)
            continue
        lines.append(l)
    sip["decl"] = "\n".join(lines)


def container_rules():
    return [
        #
        # SIP cannot handle templates with literal parameters.
        # https://www.riverbankcomputing.com/pipermail/pyqt/2017-July/039390.html
        #
        ["KJS", "CompileState", ".*", ".*", ".*", container_fix_template_w_literal_compilestate],
        ["KJS", "CodeGen", ".*", ".*", ".*", container_fix_template_w_literal_opcodes],
        ["KJS", "FunctionBodyNode", ".*", ".*", ".*", container_fix_template_w_literal_nodes],
        ["KJS", "UString", ".*", ".*", ".*", container_fix_template_w_literal_ustring],
        #
        # SIP cannot handle function pointer arguments.
        #
        ["KJS", "Lexer", ".*", ".*", ".*", container_fix_fn_ptr],
        #
        # SIP cannot handle "typename ...".
        #
        ["WTF", "HashCountedSet", ".*", ".*", ".*", container_fix_typename_countedset],
        ["WTF", "HashMap", ".*", ".*", ".*", container_fix_typename_hashmaphm],
        ["WTF", "PairFirstExtractor", ".*", ".*", ".*", container_fix_typename_hashmappfe],
        ["WTF", "HashMapTranslator", ".*", ".*", ".*", container_fix_typename_hashmaphmt],
        ["WTF", "HashTable", ".*", ".*", ".*", container_fix_typename_hashtable],
        ["WTF", "HashTable(Const|)IteratorAdapter", ".*", ".*", ".*", container_fix_typename_hashtableia],
        ["WTF", "HashSet", ".*", ".*", ".*", container_fix_typename_hashset],
        ["WTF", "PairHashTraits", ".*", ".*", ".*", container_fix_typename_hashtraits],
        ["WTF", "RefPtrHashMapRawKeyTranslator", ".*", ".*", ".*", container_fix_typename_refptrhashmap],
        #
        # SIP does not seem to be able to handle these type specialization, but we can live without them?
        #
        ["KJS", "CellSize", ".*", ".*", ".*", rule_helpers.container_discard],
        ["WTF", "DefaultHash", ".*", ".*", ".*", rule_helpers.container_discard],
        ["WTF", "GenericHashTraitsBase", ".*", ".*", ".*", rule_helpers.container_discard],
        ["WTF", "HashTraits", ".*", ".*", ".*", rule_helpers.container_discard],
        ["WTF", "IntTypes", ".*", ".*", ".*", rule_helpers.container_discard],
        ["WTF", "IsInteger", ".*", ".*", ".*", rule_helpers.container_discard],
        ["WTF", "IsPod", ".*", ".*", ".*", rule_helpers.container_discard],
        ["WTF", "Mover", ".*", ".*", ".*", rule_helpers.container_discard],
        ["WTF", "PtrHash", "P", ".*", ".*", rule_helpers.container_discard],
        ["WTF", "Vector(Destructor|Initializer|Mover|Copier|Filler|Comparer|Buffer|(Traits(Base|)))", ".*", ".*", ".*", rule_helpers.container_discard],
    ]


def forward_declaration_rules():
    return [
        ["KJS", "AttachedInterpreter", ".*", rules_engine.noop],
    ]


def function_rules():
    return [
        ["KJS", "jsString", ".*", ".*", "const char \*__0.*", rule_helpers.function_discard],
        ["KJS", "jsNumber", ".*", ".*", ".*(int|long).*", rule_helpers.function_discard],
        ["KJS::Collector", "cellBlock", ".*", "(?!const ).*", ".*", rule_helpers.function_discard],
        ["KJS::Collector", "rootObjectTypeCounts|markOtherThreadConservatively", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KJS::JSImmediate", "from", ".*", ".*", "(?!long long ).*", rule_helpers.function_discard],
        ["KJS::JSImmediate", "getNumber", ".*", "double", ".*", rule_helpers.function_discard],
        ["KJS::JSImmediate", "getTruncatedInt32", ".*", "int", ".*", rule_helpers.function_discard],
        ["KJS::JSImmediate", "getTruncatedUInt32", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KJS::JSValue", "get(Boolean|Number)", ".*", ".*", "", rule_helpers.function_discard],
        ["KJS::JSValue", "getObject|asCell", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        ["KJS::JSValue", "to(U|)Int32", ".*", ".*", "KJS::ExecState \*__0", rule_helpers.function_discard],
        ["KJS::JSCell", "getNumber", ".*", ".*", "", rule_helpers.function_discard],
        ["KJS::JSCell", "getObject", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        ["KJS::JSObject", "getDirect(Write|)Location", ".*", ".*", ".*", rule_helpers.function_discard],
        #
        # Inline implementations.
        #
        ["KJS::JS(Cell|Value)", "isObject", ".*", ".*", ".*", ".*inline .*", ".*", rule_helpers.function_discard],
        ["KJS", "is(NaN|Finite|(Pos|Neg|)Inf)|signBit", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["KJS::OpValue", "OpValue", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["KJS::JSVariableObject", "~JSVariableObject", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["KJS::JSWrapperObject", "JSWrapperObject", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["KJS::JSObject", "JSObject", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["KJS::PropertyMap", "PropertyMap", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["KJS::UChar", "UChar", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["KJS::UString", "UString", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["KJS::JSValue", "(~|)JSValue", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["KJS::JSCell", "(~|)JSCell", ".*", ".*", ".*", ".*inline .*", "", rule_helpers.function_discard],
        ["MathExtras.h", ".*", ".*", "float", ".*", rule_helpers.function_discard],
        ["WTF", "(is|to)ASCII.*", ".*", ".*", "(char|unsigned short|int) c", rule_helpers.function_discard],
        ["WTF", "intHash", ".*", ".*", "unsigned (char|short|int) key.*", rule_helpers.function_discard],
        #
        # Get rid of operators we don't like.
        #
        ["KJS::JSCell", "operator.*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KJS::ListIterator", "operator.*", ".*", "KJS::JSValue.*", ".*", rule_helpers.function_discard],
        ["KJS::ProtectedPtr", "operator.*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["KJS::ScopeChainIterator", "operator.*", ".*", "KJS.*", ".*", rule_helpers.function_discard],
        ["KJS::FunctionBodyNode", "code", ".*", ".*", ".*", ".*", "(?! const)", rule_helpers.function_discard],
        ["WTF::HashTable(Const|)(Keys|Values|)Iterator(Adapter|)", "operator.*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["WTF::Own(Array|)Ptr", "operator.*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["WTF::(Pass|)RefPtr", "operator.*", ".*", ".*", ".*", rule_helpers.function_discard],
        ["WTF::SharedPtr", "operator.*", ".*", ".*", ".*", rule_helpers.function_discard],
    ]


def typedef_rules():
    return [
        ["KJS", "CodeBlock*", ".*", ".*", rule_helpers.typedef_discard],
        ["KJS", "LocalStorage*", ".*", ".*", rule_helpers.typedef_discard],
        ["WTF", "dummyWTF_.*", ".*", ".*", rule_helpers.typedef_discard],
        ["WTF::HashMap", "(Key|Mapped|Value)Type", ".*", ".*", rule_helpers.typedef_discard],
        ["WTF::Own(Array|)Ptr", "UnspecifiedBoolType", ".*", ".*", rule_helpers.typedef_discard],
        ["WTF::(Pass|)RefPtr", "UnspecifiedBoolType", ".*", ".*", rule_helpers.typedef_discard],
    ]


def variable_rules():
    return [
        ["KJS", "OpTypeVals|ConvOpVals|OpNameVals|OpByteCodeVals|opsForOpCodes|opSpecializations|opTypeIsAlign8", ".*", variable_rewrite_array],
        ["KJS::Error", "errorNames", ".*", variable_rewrite_array_rw],
        ["KJS::OpValue", "value", ".*", variable_rewrite_rw],
        ["KJS::CollectorCell::.*", "freeCell", ".*", variable_rewrite_rw],
        ["KJS::CollectorCell", "u", ".*", variable_rewrite_rw],
        ["KJS::LocalStorageEntry", "val", ".*", variable_rewrite_rw],
        ["YYSTYPE", ".*", ".* \*", rule_helpers.variable_discard],
    ]


def unexposed_rules():
    return [
        #
        # Random crap we don't like.
        #
        ["WTF", "HashMap", "template.*\n.*HashMap", rule_helpers.unexposed_discard],
    ]


def modulecode():
    return {
        "ExecState.h": {
            "code": module_discard_duplicate,
        },
        "kjsmod.sip": {
            "code": module_fix_kjs,
        },
        "wtfmod.sip": {
            "code": module_fix_wtf,
        },
    }
