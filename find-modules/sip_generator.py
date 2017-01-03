#!/usr/bin/env python
#=============================================================================
# Copyright 2016 by Shaheed Haque (srhaque@theiet.org)
# Copyright 2016 by Stephen Kelly (steveire@gmail.com)
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
#=============================================================================

"""SIP file generator for PyQt."""

from __future__ import print_function
import argparse
import gettext
import inspect
import logging
import os
import re
import sys
import traceback
from clang import cindex
from clang.cindex import AccessSpecifier, CursorKind, SourceRange, StorageClass, TokenKind, TypeKind, TranslationUnit

import rules_engine


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _


EXPR_KINDS = [
    CursorKind.UNEXPOSED_EXPR,
    CursorKind.CONDITIONAL_OPERATOR, CursorKind.UNARY_OPERATOR, CursorKind.BINARY_OPERATOR,
    CursorKind.INTEGER_LITERAL, CursorKind.FLOATING_LITERAL, CursorKind.STRING_LITERAL,
    CursorKind.CXX_BOOL_LITERAL_EXPR, CursorKind.CXX_STATIC_CAST_EXPR, CursorKind.DECL_REF_EXPR
]
TEMPLATE_KINDS = [
                     CursorKind.TYPE_REF, CursorKind.TEMPLATE_REF, CursorKind.NAMESPACE_REF
                 ] + EXPR_KINDS


class SipGenerator(object):
    def __init__(self, project_rules, compile_flags, verbose=False, dump_includes=False, dump_privates=False):
        """
        Constructor.

        :param project_rules:       The rules for the file.
        :param compile_flags:       The compile flags for the file.
        :param dump_includes:       Turn on diagnostics for include files.
        :param dump_privates:       Turn on diagnostics for omitted private items.
        """
        self.rules = project_rules
        self.compile_flags = compile_flags
        self.verbose = verbose
        self.dump_includes = dump_includes
        self.dump_privates = dump_privates
        self.diagnostics = set()
        self.tu = None
        self.unpreprocessed_source = None

    @staticmethod
    def describe(cursor, text=None):
        if not text:
            text = cursor.spelling
        return "{} on line {} '{}'".format(cursor.kind.name, cursor.extent.start.line, text)

    def create_sip(self, root, h_file):
        """
        Actually convert the given source header file into its SIP equivalent.

        :param root:                The root of the source tree.
        :param h_file:              Add this suffix to the root to find the source (header) file of interest.
        """

        #
        # Read in the original file.
        #
        source = os.path.join(root, h_file)
        self.unpreprocessed_source = []
        with open(source, "rU") as f:
            for line in f:
                self.unpreprocessed_source.append(line)

        index = cindex.Index.create()
        self.tu = index.parse(source, ["-x", "c++"] + self.compile_flags)
        for diag in self.tu.diagnostics:
            #
            # We expect to be run over hundreds of files. Any parsing issues are likely to be very repetitive.
            # So, to avoid bothering the user, we suppress duplicates.
            #
            loc = diag.location
            msg = "{}:{}[{}] {}".format(loc.file, loc.line, loc.column, diag.spelling)
            if msg in self.diagnostics:
                continue
            self.diagnostics.add(msg)
            logger.log(diag.severity, "Parse error {}".format(msg))
        if self.dump_includes:
            for include in sorted(set(self.tu.get_includes())):
                logger.debug(_("Used includes {}").format(include.include.name))
        #
        # Run through the top level children in the translation unit.
        #
        body, typecodes = self._container_get(self.tu.cursor, -1, h_file)
        if body:
            #
            # Any module-related manual code (%ExportedHeaderCode, %ModuleCode, %ModuleHeaderCode or other
            # module-level directives?
            #
            name = os.path.basename(h_file)
            sip = {
                "name": name,
                "decl": body
            }
            body = ""
            modifying_rule = self.rules.modulecode(name, sip)
            if modifying_rule:
                body += "// Modified {} (by {}):\n".format(name, modifying_rule)
            body += sip["decl"] + sip["code"]
            for typecode in typecodes:
                body += "\n\n" + typecode + "\n\n"
        return body, self.tu.get_includes

    CONTAINER_SKIPPABLE_UNEXPOSED_DECL = re.compile("_DECLARE_PRIVATE|friend|;")
    CONTAINER_SKIPPABLE_ATTR = re.compile("_EXPORT")
    FN_SKIPPABLE_ATTR = re.compile("_EXPORT|Q_REQUIRED_RESULT|format\(printf")
    VAR_SKIPPABLE_ATTR = re.compile("_EXPORT")
    TYPEDEF_SKIPPABLE_ATTR = re.compile("_EXPORT")

    def _container_get(self, container, level, h_file):
        """
        Generate the (recursive) translation for a class or namespace.

        :param container:           A class or namespace.
        :param h_file:              Name of header file being processed.
        :param level:               Recursion level controls indentation.
        :return:                    A string.
        """

        def skippable_attribute(member, text):
            """
            We don't seem to have access to the __attribute__(())s, but at least we can look for stuff we care about.

            :param member:          The attribute.
            :param text:            The raw source corresponding to the region of member.
            """
            if text.find("_DEPRECATED") != -1:
                sip["annotations"].add("Deprecated")
                return True
            if SipGenerator.CONTAINER_SKIPPABLE_ATTR.search(text):
                return True
            SipGenerator._report_ignoring(container, member, text)

        sip = {
            "name": container.displayname,
            "annotations": set()
        }
        name = container.displayname
        if container.access_specifier == AccessSpecifier.PRIVATE:
            if self.dump_privates:
                logger.debug("Ignoring private {}".format(SipGenerator.describe(container)))
            return "",[]
        body = ""
        base_specifiers = []
        template_type_parameters = []
        had_copy_constructor = False
        had_const_member = False
        typecodes = []
        for member in container.get_children():
            #
            # Only emit items in the translation unit.
            #
            if member.location.file.name != self.tu.spelling:
                continue
            decl = ""
            if member.kind in [CursorKind.CXX_METHOD, CursorKind.FUNCTION_DECL, CursorKind.FUNCTION_TEMPLATE,
                               CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR, CursorKind.CONVERSION_FUNCTION]:
                decl = self._fn_get(container, member, level + 1)
                #
                # Abstract?
                #
                if member.is_pure_virtual_method():
                    sip["annotations"].add("Abstract")
            elif member.kind == CursorKind.ENUM_DECL:
                decl = self._enum_get(container, member, level + 1) + ";\n"
            elif member.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
                decl = self._get_access_specifier(member, level + 1)
            elif member.kind == CursorKind.TYPEDEF_DECL:
                decl, mapped_typecodes = self._typedef_get(container, member, level + 1)
                typecodes.extend(mapped_typecodes)
            elif member.kind == CursorKind.CXX_BASE_SPECIFIER:
                #
                # Strip off the leading "class". Except for TypeKind.UNEXPOSED...
                #
                base_specifiers.append(member.displayname.split(None, 2)[-1])
            elif member.kind == CursorKind.TEMPLATE_TYPE_PARAMETER:
                template_type_parameters.append(member.displayname)
            elif member.kind == CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
                template_type_parameters.append(member.type.spelling + " " + member.displayname)
            elif member.kind in [CursorKind.VAR_DECL, CursorKind.FIELD_DECL]:
                had_const_member = had_const_member or member.type.is_const_qualified()
                decl = self._var_get(container, member, level + 1)
            elif member.kind in [CursorKind.NAMESPACE, CursorKind.CLASS_DECL,
                                 CursorKind.CLASS_TEMPLATE, CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
                                 CursorKind.STRUCT_DECL, CursorKind.UNION_DECL]:
                decl, tmp = self._container_get(member, level + 1, h_file)
                typecodes.extend(tmp)
            elif member.kind in TEMPLATE_KINDS + [CursorKind.USING_DECLARATION, CursorKind.USING_DIRECTIVE,
                                                  CursorKind.CXX_FINAL_ATTR]:
                #
                # Ignore:
                #
                #   TEMPLATE_KINDS: Template type parameter.
                #   CursorKind.USING_DECLARATION, CursorKind.USING_DIRECTIVE: Using? Pah!
                #   CursorKind.CXX_FINAL_ATTR: Again, not much to be done with this.
                #
                pass
            else:
                text = self._read_source(member.extent)
                if member.kind in [CursorKind.UNEXPOSED_ATTR, CursorKind.VISIBILITY_ATTR]:
                    if skippable_attribute(member, text):
                        pass
                    else:
                        decl = self._unexposed_get(container, member, text, level + 1)
                elif member.kind == CursorKind.UNEXPOSED_DECL:
                    if SipGenerator.CONTAINER_SKIPPABLE_UNEXPOSED_DECL.search(text):
                        pass
                    else:
                        decl = self._unexposed_get(container, member, text, level + 1)
                else:
                    SipGenerator._report_ignoring(container, member)

            def is_copy_constructor(member):
                if member.kind != CursorKind.CONSTRUCTOR:
                    return False
                numParams = 0
                hasSelfType = False
                for child in member.get_children():
                    numParams += 1
                    if child.kind == CursorKind.PARM_DECL:
                        paramType = child.type.spelling
                        paramType = paramType.split("::")[-1]
                        paramType = paramType.replace("const", "").replace("&", "").strip()
                        hasSelfType = paramType == container.displayname
                return numParams == 1 and hasSelfType

            def has_parameter_default(parameter):
                for member in parameter.get_children():
                    if member.kind.is_expression():
                        return True
                return False

            def is_default_constructor(member):
                if member.kind != CursorKind.CONSTRUCTOR:
                    return False
                numParams = 0
                for parameter in member.get_children():
                    if (has_parameter_default(parameter)):
                        break
                    numParams += 1
                return numParams == 0

            had_copy_constructor = had_copy_constructor or is_copy_constructor(member)
            #
            # Discard almost anything which is private.
            #
            if member.access_specifier == AccessSpecifier.PRIVATE:
                if member.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
                    #
                    # We need these because...
                    #
                    pass
                elif is_copy_constructor(member) or is_default_constructor(member):
                    #
                    # ...we need to pass private copy contructors to the SIP compiler.
                    #
                    pass
                else:
                    if self.dump_privates:
                        logger.debug("Ignoring private {}".format(SipGenerator.describe(member)))
                    continue

            if decl:
                if self.verbose:
                    pad = " " * ((level + 1) * 4)
                    body += pad + "// {}\n".format(SipGenerator.describe(member))
                body += decl
        #
        # Empty containers are still useful if they provide namespaces or forward declarations.
        #
        if not body and level >= 0:
            body = "\n"
            text = self._read_source(container.extent)
            if not text.endswith("}"):
                #
                # Forward declaration.
                #
                sip["annotations"].add("External")
        if body and level >= 0:
            if container.kind == CursorKind.NAMESPACE:
                container_type = "namespace " + name
            elif container.kind in [CursorKind.CLASS_DECL, CursorKind.CLASS_TEMPLATE,
                                    CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION]:
                container_type = "class " + name
            elif container.kind == CursorKind.STRUCT_DECL:
                container_type = "struct {}".format(name or "__struct{}".format(container.extent.start.line))
            elif container.kind == CursorKind.UNION_DECL:
                container_type = "union {}".format(name or "__union{}".format(container.extent.start.line))
            else:
                raise AssertionError(
                    _("Unexpected container {}: {}[{}]").format(container.kind, name, container.extent.start.line))
            #
            # Generate private copy constructor for non-copyable types.
            #
            if had_const_member and not had_copy_constructor:
                body += "    private:\n        {}(const {} &); // Generated\n".format(name, container.type.get_canonical().spelling)
            #
            # Flesh out the SIP context for the rules engine.
            #
            sip["template_parameters"] = ", ".join(template_type_parameters)
            sip["decl"] = container_type
            sip["base_specifiers"] = ", ".join(base_specifiers)
            sip["body"] = body
            self.rules.container_rules().apply(container, sip)
            pad = " " * (level * 4)
            if sip["name"]:
                #
                # Any type-related code (%BIGetBufferCode, %BIGetReadBufferCode, %BIGetWriteBufferCode,
                # %BIGetSegCountCode, %BIGetCharBufferCode, %BIReleaseBufferCode, %ConvertToSubClassCode,
                # %ConvertToTypeCode, %GCClearCode, %GCTraverseCode, %InstanceCode, %PickleCode, %TypeCode,
                # %TypeHeaderCode other type-related directives)?
                #
                self.rules.typecode(container, sip)
                decl += pad + sip["decl"]
                if "External" in sip["annotations"]:
                    #
                    # SIP /External/ does not seem to work as one might wish. Suppress.
                    #
                    body = decl + " /External/;\n"
                    body = pad + "// Discarded {}\n".format(SipGenerator.describe(container))
                else:
                    if sip["base_specifiers"]:
                        decl += ": " + sip["base_specifiers"]
                    if sip["annotations"]:
                        decl += " /" + ",".join(sip["annotations"]) + "/"
                    if sip["template_parameters"]:
                        decl = pad + "template <" + sip["template_parameters"] + ">\n" + decl
                    decl += "\n" + pad + "{\n"
                    decl += "%TypeHeaderCode\n#include <{}>\n%End\n".format(h_file)
                    decl += sip["code"]
                    body = decl + sip["body"] + pad + "};\n"
                    if sip["mapped_type"]:
                        mapped_typecode = "%MappedType " + sip["name"] + "\n{\n" + sip["mapped_type"] + "};\n"
                        typecodes.append(mapped_typecode)
            else:
                body = pad + "// Discarded {}\n".format(SipGenerator.describe(container))
        return body, typecodes

    def _get_access_specifier(self, member, level):
        """
        In principle, we just want member.access_specifier.name.lower(), except that we need to handle:

          Q_OBJECT
          Q_SIGNALS:|signals:
          public|private|protected Q_SLOTS:|slots:

        which are converted by the preprocessor...so read the original text.

        :param member:                  The access_specifier.
        :return:
        """
        access_specifier = self._read_source(member.extent)
        if access_specifier == "signals:":
            pass
        elif access_specifier == "Q_SIGNALS:":
            access_specifier = "signals:"
        elif access_specifier.endswith("slots:") or access_specifier.endswith("Q_SLOTS:"):
            access_specifier = access_specifier.split()[0] + ":"
        elif access_specifier not in ["public:", "protected:", "private:"]:
            access_specifier = "public: // Mapped from " + access_specifier
        pad = " " * ((level - 1) * 4)
        decl = pad + access_specifier + "\n"
        return decl

    def _enum_get(self, container, enum, level):
        pad = " " * (level * 4)
        decl = pad + "enum {} {{\n".format(enum.displayname or "__enum{}".format(enum.extent.start.line))
        enumerations = []
        for enum in enum.get_children():
            #
            # Skip visibility attributes and the like.
            #
            if enum.kind == CursorKind.ENUM_CONSTANT_DECL:
                enumerations.append(pad + "    {}".format(enum.displayname))
        decl += ",\n".join(enumerations) + "\n"
        decl += pad + "}"
        return decl

    def _fn_get(self, container, function, level):
        """
        Generate the translation for a function.

        :param container:           A class or namespace.
        :param function:            The function object.
        :param level:               Recursion level controls indentation.
        :return:                    A string.
        """

        def skippable_attribute(member, text):
            """
            We don't seem to have access to the __attribute__(())s, but at least we can look for stuff we care about.

            :param member:          The attribute.
            :param text:            The raw source corresponding to the region of member.
            """
            if text.find("_DEPRECATED") != -1:
                sip["annotations"].add("Deprecated")
                return True
            if SipGenerator.FN_SKIPPABLE_ATTR.search(text):
                return True
            SipGenerator._report_ignoring(function, member, text)

        sip = {
            "name": function.spelling,
            "annotations": set()
        }
        parameters = []
        template_parameters = []
        for child in function.get_children():
            if child.kind == CursorKind.PARM_DECL:
                parameter = child.displayname or "__{}".format(len(parameters))
                #
                # So far so good, but we need any default value.
                #
                theType = child.type.get_canonical()
                typeSpelling = theType.spelling
                if theType.kind == TypeKind.POINTER:
                    typeSpelling = theType.get_pointee().spelling + "* "

                decl = "{} {}".format(typeSpelling, parameter)
                decl = decl.replace("* ", "*").replace("& ", "&")
                child_sip = {
                    "name": parameter,
                    "decl": decl,
                    "init": self._fn_get_parameter_default(function, child),
                    "annotations": set()
                }
                self.rules.parameter_rules().apply(container, function, child, child_sip)
                decl = child_sip["decl"]
                if child_sip["annotations"]:
                    decl += " /" + ",".join(child_sip["annotations"]) + "/"
                if child_sip["init"]:
                    decl += " = " + child_sip["init"]
                parameters.append(decl)
            elif child.kind in [CursorKind.COMPOUND_STMT, CursorKind.CXX_OVERRIDE_ATTR,
                                CursorKind.MEMBER_REF, CursorKind.DECL_REF_EXPR, CursorKind.CALL_EXPR] + TEMPLATE_KINDS:
                #
                # Ignore:
                #
                #   CursorKind.COMPOUND_STMT: Function body.
                #   CursorKind.CXX_OVERRIDE_ATTR: The "override" keyword.
                #   CursorKind.MEMBER_REF, CursorKind.DECL_REF_EXPR, CursorKind.CALL_EXPR: Constructor initialisers.
                #   TEMPLATE_KINDS: The result type.
                #
                pass
            elif child.kind == CursorKind.TEMPLATE_TYPE_PARAMETER:
                template_parameters.append(child.displayname)
            elif child.kind == CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
                template_parameters.append(child.type.spelling + " " + child.displayname)
            elif child.kind == CursorKind.TEMPLATE_TEMPLATE_PARAMETER:
                template_parameters.append(self._template_template_param_get(child))
            else:
                text = self._read_source(child.extent)
                if child.kind in [CursorKind.UNEXPOSED_ATTR, CursorKind.VISIBILITY_ATTR] and skippable_attribute(child,
                                                                                                                 text):
                    pass
                else:
                    SipGenerator._report_ignoring(function, child)
        #
        # Flesh out the SIP context for the rules engine.
        #
        sip["template_parameters"] = template_parameters
        if function.kind in [CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR]:
            sip["fn_result"] = ""
        else:
            sip["fn_result"] = function.result_type.spelling
        sip["parameters"] = parameters
        sip["prefix"], sip["suffix"] = self._fn_get_decorators(function)
        self.rules.function_rules().apply(container, function, sip)
        pad = " " * (level * 4)
        if sip["name"]:
            #
            # Any method-related code (%MethodCode, %VirtualCatcherCode, VirtualCallCode
            # or other method-related directives)?
            #
            self.rules.methodcode(function, sip)
            sip["template_parameters"] = ", ".join(sip["template_parameters"])
            if not isinstance(sip["parameters"], str):
                sip["parameters"] = ", ".join(sip["parameters"])
            sip["annotations"] = ",".join(sip["annotations"])
            decl += sip["name"] + "(" + sip["parameters"] + ")"
            if sip["decl2"] or sip["fn_result2"]:
                if not isinstance(sip["decl2"], str):
                    sip["decl2"] = ", ".join(sip["decl2"])
                decl += "\n    " + pad + "["
                #
                # SIP does not want the result for constructors.
                #
                if function.kind != CursorKind.CONSTRUCTOR:
                    if sip["fn_result2"][-1] in "*&":
                        decl += sip["fn_result2"]
                    else:
                        decl += sip["fn_result2"] + " "
                decl += "(" + sip["decl2"] + ")]"
            if sip["fn_result"]:
                if sip["fn_result"][-1] in "*&":
                    decl = sip["fn_result"] + decl
                else:
                    decl = sip["fn_result"] + " " + decl
            decl = pad + sip["prefix"] + decl + sip["suffix"]
            if sip["annotations"]:
                decl += " /" + sip["annotations"] + "/"
            if sip["template_parameters"]:
                decl = pad + "template <" + sip["template_parameters"] + ">\n" + decl
            decl += ";\n"
            decl += sip["code"]
        else:
            decl = pad + "// Discarded {}\n".format(SipGenerator.describe(function))
        return decl

    def _template_template_param_get(self, container):
        """
        Recursive template template parameter walk.

        :param container:                   The template template object.
        :return:                            String containing the template template parameter.
        """
        template_type_parameters = []
        for member in container.get_children():
            if member.kind == CursorKind.TEMPLATE_TYPE_PARAMETER:
                template_type_parameters.append("typename")
            elif member.kind == CursorKind.TEMPLATE_TEMPLATE_PARAMETER:
                template_type_parameters.append(self._template_template_param_get(member))
            else:
                SipGenerator._report_ignoring(container, member)
        template_type_parameters = "template <" + (", ".join(template_type_parameters)) + "> class " + \
                                   container.displayname
        return template_type_parameters

    def _fn_get_decorators(self, function):
        """
        The parser does not provide direct access to the complete keywords (explicit, const, static, etc) of a function
        in the displayname. It would be nice to get these from the AST, but I cannot find where they are hiding.

        Now, we could resort to using the original source. That does not bode well if you have macros (QOBJECT,
        xxxDEPRECATED?), inlined bodies and the like, using the rule engine could be used to patch corner cases...

        ...or we can try to guess what SIP cares about, i.e static and maybe const. Luckily (?), we have those to hand!

        :param function:                    The function object.
        :return: prefix, suffix             String containing any prefix or suffix keywords.
        """
        suffix = ""
        if function.is_const_method():
            suffix += " const"
        prefix = ""
        if function.is_static_method():
            prefix += "static "
        if function.is_virtual_method():
            prefix += "virtual "
            if function.is_pure_virtual_method():
                suffix += " = 0"
        return prefix, suffix

    def _fn_get_parameter_default(self, function, parameter):
        """
        The parser does not seem to provide access to the complete text of a parameter.
        This makes it hard to find any default values, so we:

            1. Run the lexer from "here" to the end of the file, bailing out when we see the ","
            or a ")" marking the end.
            2. Watch for the assignment.
        """
        possible_extent = SourceRange.from_locations(parameter.extent.start, function.extent.end)
        text = ""
        bracket_level = 0
        found_end = False
        was_punctuated = True
        default_value = None
        for token in self.tu.get_tokens(extent=possible_extent):
            if bracket_level <= 0 and token.spelling in [",", ")", ";"]:
                found_end = True
                break
            elif token.spelling == "(":
                was_punctuated = True
                bracket_level += 1
                text += token.spelling
            elif token.spelling == ")":
                was_punctuated = True
                bracket_level -= 1
                text += token.spelling
            elif token.kind == TokenKind.PUNCTUATION:
                was_punctuated = True
                text += token.spelling
                if token.spelling == "=" and default_value is None:
                    default_value = len(text)
            else:
                if not was_punctuated:
                    text += " "
                text += token.spelling
                was_punctuated = False
        if not found_end and text:
            RuntimeError(_("No end found for {}::{}, '{}'").format(function.spelling, parameter.spelling, text))
        if default_value:
            #
            # Strip any whitespace and brackets.
            #
            text = text[default_value:].strip()
            if text.startswith("("):
                text = text[1:-1]
            return text
        else:
            return ""

    def _typedef_get(self, container, typedef, level):
        """
        Generate the translation for a typedef.

        :param container:           A class or namespace.
        :param typedef:             The typedef object.
        :param level:               Recursion level controls indentation.
        :return:                    A string.
        """
        def skippable_attribute(member, text):
            """
            We don't seem to have access to the __attribute__(())s, but at least we can look for stuff we care about.

            :param member:          The attribute.
            :param text:            The raw source corresponding to the region of member.
            """
            if text.find("_DEPRECATED") != -1:
                sip["annotations"].add("Deprecated")
                return True
            if SipGenerator.TYPEDEF_SKIPPABLE_ATTR.search(text):
                return True
            SipGenerator._report_ignoring(typedef, member, text)

        sip = {
            "name": typedef.displayname,
            "annotations": set()
        }
        args = []
        result_type = ""
        typecodes = []
        for child in typedef.get_children():
            if child.kind == CursorKind.TEMPLATE_REF:
                result_type = child.displayname
            elif child.kind == CursorKind.TYPE_REF:
                #
                # Sigh. For results which are pointers, we dont have a way of detecting the need for the "*".
                #
                result_type = child.type.spelling
            elif child.kind == CursorKind.ENUM_DECL:
                if child.underlying_typedef_type:
                    #
                    # Typedefs for inlined enums seem to be emitted twice. Refer back to original.
                    #
                    enum = child.type.get_declaration()
                    decl = "__enum{}".format(enum.extent.start.line)
                else:
                    decl = self._enum_get(container, child, level)
                args.append(decl)
            elif child.kind == CursorKind.STRUCT_DECL:
                if child.underlying_typedef_type:
                    #
                    # Typedefs for inlined structs seem to be emitted twice. Refer back to original.
                    #
                    struct = child.type.get_declaration()
                    decl = "__struct{}".format(struct.extent.start.line)
                else:
                    decl, tmp = self._container_get(child, level, None)
                    typecodes.extend(tmp)
                args.append(decl)
            elif child.kind == CursorKind.PARM_DECL:
                decl = child.displayname or "__{}".format(len(args))
                #
                # So far so good, but we need any default value.
                #
                decl = "{} {}".format(child.type.spelling, decl)
                args.append(decl)
            elif child.kind in EXPR_KINDS + [CursorKind.NAMESPACE_REF]:
                #
                # Ignore:
                #
                #   EXPR_KINDS: Array size etc.
                #   CursorKind.NAMESPACE_REF: Type stuff.
                #
                pass
            else:
                text = self._read_source(child.extent)
                if child.kind in [CursorKind.UNEXPOSED_ATTR, CursorKind.VISIBILITY_ATTR] and skippable_attribute(child,
                                                                                                                 text):
                    pass
                else:
                    SipGenerator._report_ignoring(typedef, child)
        #
        # Flesh out the SIP context for the rules engine.
        #
        sip["fn_result"] = ""
        if typedef.underlying_typedef_type.kind == TypeKind.MEMBERPOINTER:
            sip["fn_result"] = result_type
            sip["decl"] = ", ".join(args)
        elif typedef.underlying_typedef_type.kind == TypeKind.RECORD:
            sip["decl"] = result_type
        else:
            sip["decl"] = typedef.underlying_typedef_type.spelling
        sip["args"] = args
        #
        # Working out if a typedef is for a function pointer seems hard if not impossible in many cases. For such
        # cases, the only recourse right now is the following heristic (maybe it is safer to put this in the rules
        # engine?)
        #
        if typedef.underlying_typedef_type.kind != TypeKind.MEMBERPOINTER:
            if sip["decl"].endswith(")"):
                parts = sip["decl"].split("(*)", 2)
                if len(parts) == 2 and parts[1].startswith("("):
                    sip["fn_result"] = parts[0]
                    sip["decl"] = parts[1][1:-1]
        self.rules.typedef_rules().apply(container, typedef, sip)
        #
        # Now the rules have run, add any prefix/suffix.
        #
        pad = " " * (level * 4)
        if sip["name"]:
            #
            # Any type-related code (%BIGetBufferCode, %BIGetReadBufferCode, %BIGetWriteBufferCode,
            # %BIGetSegCountCode, %BIGetCharBufferCode, %BIReleaseBufferCode, %ConvertToSubClassCode,
            # %ConvertToTypeCode, %GCClearCode, %GCTraverseCode, %InstanceCode, %PickleCode, %TypeCode
            # or %TypeHeaderCode)?
            #
            self.rules.typecode(typedef, sip)
            if sip["fn_result"]:
                decl = pad + "typedef {}(*{})({})".format(sip["fn_result"], sip["name"], sip["decl"])
                decl = decl.replace("* ", "*").replace("& ", "&")
            else:
                decl = pad + "typedef {} {}".format(sip["decl"], sip["name"])
            #
            # SIP does not support deprecation of typedefs.
            #
            sip["annotations"].discard("Deprecated")
            if sip["annotations"]:
                decl += " /" + ",".join(sip["annotations"]) + "/"
            decl += sip["code"] + ";\n"
            if sip["mapped_type"]:
                mapped_typecode = "%MappedType " + typedef.type.get_canonical().spelling + "\n{\n" + sip["mapped_type"] + "};\n"
                typecodes.append(mapped_typecode)
        else:
            decl = pad + "// Discarded {}\n".format(SipGenerator.describe(typedef))
        return decl, typecodes

    def _unexposed_get(self, container, unexposed, text, level):
        """
        The parser does not seem to provide access to the complete text of an unexposed decl.

            1. Run the lexer from "here" to the end of the outer scope, bailing out when we see the ";"
            or a "{" marking the end.
        """
        sip = {
            "name": unexposed.displayname,
            "annotations": set()
        }
        #
        # Flesh out the SIP context for the rules engine.
        #
        sip["decl"] = text
        self.rules.unexposed_rules().apply(container, unexposed, sip)
        #
        # Now the rules have run, add any prefix/suffix.
        #
        pad = " " * (level * 4)
        if sip["name"]:
            decl = pad + sip["decl"] + "\n"
        else:
            decl = pad + "// Discarded {}\n".format(SipGenerator.describe(unexposed))
        return decl

    def _var_get(self, container, variable, level):
        """
        Generate the translation for a variable.

        :param container:           A class or namespace.
        :param variable:            The variable object.
        :param level:               Recursion level controls indentation.
        :return:                    A string.
        """

        def skippable_attribute(member, text):
            """
            We don't seem to have access to the __attribute__(())s, but at least we can look for stuff we care about.

            :param member:          The attribute.
            :param text:            The raw source corresponding to the region of member.
            """
            if SipGenerator.VAR_SKIPPABLE_ATTR.search(text):
                return True
            SipGenerator._report_ignoring(container, member, text)

        sip = {
            "name": variable.spelling,
            "annotations": set()
        }
        for child in variable.get_children():
            if child.kind in TEMPLATE_KINDS + [CursorKind.STRUCT_DECL, CursorKind.UNION_DECL]:
                #
                # Ignore:
                #
                #   TEMPLATE_KINDS, CursorKind.STRUCT_DECL, CursorKind.UNION_DECL: : The variable type.
                #
                pass
            else:
                text = self._read_source(child.extent)
                if child.kind == CursorKind.VISIBILITY_ATTR and skippable_attribute(child, text):
                    pass
                else:
                    SipGenerator._report_ignoring(variable, child)
        #
        # Flesh out the SIP context for the rules engine.
        #
        decl = variable.type.spelling
        sip["decl"] = decl
        self.rules.variable_rules().apply(container, variable, sip)
        #
        # Now the rules have run, add any prefix/suffix.
        #
        pad = " " * (level * 4)
        if sip["name"]:
            prefix = self._var_get_keywords(variable)
            decl = pad + prefix + sip["decl"]
            if decl[-1] not in "*&":
                decl += " "
            decl += sip["name"]
            if sip["annotations"]:
                decl += " /" + ",".join(sip["annotations"]) + "/"
            #
            # SIP does not support protected variables, so we ignore them.
            #
            if variable.access_specifier == AccessSpecifier.PROTECTED:
                decl = pad + "// Discarded {}\n".format(SipGenerator.describe(variable))
            else:
                decl = decl + sip["code"] + ";\n"
        else:
            decl = pad + "// Discarded {}\n".format(SipGenerator.describe(variable))
        return decl

    def _var_get_keywords(self, variable):
        """
        The parser does not provide direct access to the complete keywords (static, etc) of a variable
        in the displayname. It would be nice to get these from the AST, but I cannot find where they are hiding.

        :param variable:                    The variable object.
        :return: prefix                     String containing any prefix keywords.
        """
        if variable.storage_class == StorageClass.STATIC:
            #
            # SIP does not support "static".
            #
            prefix = ""
        else:
            prefix = ""
        return prefix

    def _read_source(self, extent):
        """
        Read the given range from the unpre-processed source.

        :param extent:              The range of text required.
        """
        extract = self.unpreprocessed_source[extent.start.line - 1:extent.end.line]
        if extent.start.line == extent.end.line:
            extract[0] = extract[0][extent.start.column - 1:extent.end.column - 1]
        else:
            extract[0] = extract[0][extent.start.column - 1:]
            extract[-1] = extract[-1][:extent.end.column - 1]
        #
        # Return a single line of text.
        #
        return "".join(extract).replace("\n", " ")

    @staticmethod
    def _report_ignoring(parent, child, text=None):
        if not text:
            text = child.displayname or child.spelling
        logger.debug(_("Ignoring {} {} child {}").format(parent.kind.name, parent.spelling, SipGenerator.describe(child, text)))


def main(argv=None):
    """
    Take a single C++ header file and generate the corresponding SIP file.
    Beyond simple generation of the SIP file from the corresponding C++
    header file, a set of rules can be used to customise the generated
    SIP file.

    Examples:

        sip_generator.py /usr/include/KF5/KItemModels/kselectionproxymodel.h
    """
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(epilog=inspect.getdoc(main),
                                     formatter_class=HelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help=_("Enable verbose output"))
    parser.add_argument("--flags",
                        help=_("Semicolon-separated C++ compile flags to use"))
    parser.add_argument("libclang", help=_("libclang library to use for parsing"))
    parser.add_argument("project_rules", help=_("Project rules"))
    parser.add_argument("source", help=_("C++ header to process"))
    parser.add_argument("output", help=_("output filename to write"))
    try:
        args = parser.parse_args(argv[1:])
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        #
        # Load the given libclang.
        #
        cindex.Config.set_library_file(args.libclang)
        #
        # Generate!
        #
        rules = rules_engine.rules(args.project_rules)
        g = SipGenerator(rules, args.flags.lstrip().split(";"), args.verbose)
        root = os.path.dirname(args.source)
        h_file = os.path.basename(args.source)
        body, includes = g.create_sip(root, h_file)
        with open(args.output, "w") as outputFile:
            outputFile.write(body)
    except Exception as e:
        tbk = traceback.format_exc()
        print(tbk)
        return -1


if __name__ == "__main__":
    if sys.argv[1] != "--self-check":
        sys.exit(main())
    else:
        cindex.Config.set_library_file(sys.argv[2])
