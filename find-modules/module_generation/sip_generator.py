#!/usr/bin/env python
#
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
#

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
from clang.cindex import AccessSpecifier, CursorKind, SourceRange, StorageClass, TokenKind, TypeKind

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


def clang_diagnostic_to_logging_diagnostic(lvl):
    """

    The diagnostic levels in cindex.py are

        Ignored = 0
        Note    = 1
        Warning = 2
        Error   = 3
        Fatal   = 4

    and the leves in the python logging module are

        NOTSET      0
        DEBUG       10
        INFO        20
        WARNING     30
        ERROR       40
        CRITICAL    50

    """
    return (logging.NOTSET,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL)[lvl]


def diagnostic_word(lvl):
    return ("", "info", "warning", "error", "fatality")[lvl]


def trace_discarded_by(cursor, rule, text=None):
    trace = "// Discarded {} (by {})\n".format(SipGenerator.describe(cursor, text), rule)
    return trace


def trace_generated_for(cursor, fn, extra, text=None):
    trace = "// Generated for {}, {} (by {}:{}): {}\n".format(os.path.basename(cursor.extent.start.file.name),
                                                              SipGenerator.describe(cursor, text),
                                                              os.path.basename(inspect.getfile(fn)), fn.__name__,
                                                              extra)
    return trace


def trace_modified_by(cursor, rule, text=None):
    trace = "// Modified {} (by {}):\n".format(SipGenerator.describe(cursor, text), rule)
    return trace


class SipGenerator(object):
    def __init__(self, rules_pkg, compile_flags, verbose=False, dump_includes=False, dump_privates=False):
        """
        Constructor.

        :param rules_pkg:           The rules for the file.
        :param compile_flags:       The compile flags for the file.
        :param dump_includes:       Turn on diagnostics for include files.
        :param dump_privates:       Turn on diagnostics for omitted private items.
        """
        self.compiled_rules = rules_engine.rules(rules_pkg)
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

    def create_sip(self, h_file, include_filename):
        """
        Actually convert the given source header file into its SIP equivalent.
        This is the main entry point for this class.

        :param h_file:              The source (header) file of interest.
        :param include_filename:    The (header) to generate in the sip file.
        :returns: A (body, module_code, includes). The body is the SIP text
                corresponding to the h_file, it can be a null string indicating
                there was nothing that could be generated. The module_code is
                a dictionary of fragments of code that are to be emitted at
                module scope. The includes is a iterator over the files which
                clang #included while processing h_file.
        """
        #
        # Read in the original file.
        #
        source = h_file
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
            if diag.spelling == "#pragma once in main file":
                continue
            if msg in self.diagnostics:
                continue
            self.diagnostics.add(msg)
            logger.log(clang_diagnostic_to_logging_diagnostic(diag.severity),
                       "Parse {}: {}".format(diagnostic_word(diag.severity), msg))
        if self.dump_includes:
            for include in sorted(set(self.tu.get_includes())):
                logger.debug(_("Used includes {}").format(include.include.name))
        #
        # Run through the top level children in the translation unit.
        #
        body, module_code = self._container_get(self.tu.cursor, -1, h_file, include_filename)
        if body:
            #
            # Any module-related manual code (%ExportedHeaderCode, %ModuleCode, %ModuleHeaderCode or other
            # module-level directives?
            #
            h_name = os.path.basename(h_file)
            sip = {
                "name": os.path.basename(include_filename),
                "decl": body
            }
            body = ""
            modifying_rule = self.compiled_rules.modulecode(h_name, sip)
            if modifying_rule:
                body += "// Modified {} (by {}):\n".format(h_name, modifying_rule)
            body += sip["decl"] + sip["code"]
        return body, module_code, self.tu.get_includes

    def skippable_attribute(self, parent, member, text, sip):
        """
        We don't seem to have access to the __attribute__(())s, but at least we can look for stuff we care about.

        :param member:          The attribute.
        :param text:            The raw source corresponding to the region of member.
        """
        if member.kind == CursorKind.UNEXPOSED_ATTR and text.find("_DEPRECATED") != -1:
            sip["annotations"].add("Deprecated")
            return True
        if member.kind != CursorKind.VISIBILITY_ATTR:
            return False
        if member.spelling == "hidden":
            if self.dump_privates:
                logger.debug("Ignoring private {}".format(SipGenerator.describe(parent)))
            sip["name"] = ""
            return True
        return False

    def _container_get(self, container, level, h_file, include_filename):
        """
        Generate the (recursive) translation for a class or namespace.

        :param container:           A class or namespace.
        :param h_file:              Name of header file being processed.
        :param level:               Recursion level controls indentation.
        :return:                    A string.
        """
        def in_class(item):
            parent = item.semantic_parent
            while parent and parent.kind != CursorKind.CLASS_DECL:
                parent = parent.semantic_parent
            return True if parent else False

        def is_copy_constructor(member):
            if member.kind != CursorKind.CONSTRUCTOR:
                return False
            num_params = 0
            has_self_type = False
            for child in member.get_children():
                num_params += 1
                if child.kind == CursorKind.PARM_DECL:
                    param_type = child.type.spelling
                    param_type = param_type.split("::")[-1]
                    param_type = param_type.replace("const", "").replace("&", "").strip()
                    has_self_type = param_type == container.displayname
            return num_params == 1 and has_self_type

        def has_parameter_default(parameter):
            for member in parameter.get_children():
                if member.kind.is_expression():
                    return True
            return False

        def is_default_constructor(member):
            if member.kind != CursorKind.CONSTRUCTOR:
                return False
            num_params = 0
            for parameter in member.get_children():
                if has_parameter_default(parameter):
                    break
                num_params += 1
            return num_params == 0

        def nameless_template_parameters_get(tokens, template_parameters):
            """
            Fix the issue that nameless template parameters go missing.
            """
            assert tokens[1].spelling == "<"
            tokens = tokens[2:]
            tmp = []
            non_missing_parameter = 0
            for token in tokens:
                if token.extent.end.offset <= template_parameters[non_missing_parameter][1].start.offset:
                    if token.kind == TokenKind.IDENTIFIER:
                        #
                        # We found a nameless template parameter.
                        #
                        tmp.append("__{}".format(len(tmp)))
                elif token.extent.end.offset == template_parameters[non_missing_parameter][1].end.offset:
                    #
                    # Consume a non-nameless template parameter.
                    #
                    tmp.append(template_parameters[non_missing_parameter][0])
                    non_missing_parameter += 1
            #
            # Consume any remaining non-nameless template parameters.
            #
            template_parameters = [i[0] for i in template_parameters if i[0]]
            tmp.extend(template_parameters[non_missing_parameter:])
            return tmp

        sip = {
            "name": container.spelling,
            "annotations": set()
        }
        body = ""
        base_specifiers = []
        template_parameters = []
        had_copy_constructor = False
        had_const_member = False
        module_code = {}
        is_signal = False
        VARIABLE_KINDS = [CursorKind.VAR_DECL, CursorKind.FIELD_DECL]
        FN_KINDS = [CursorKind.CXX_METHOD, CursorKind.FUNCTION_DECL, CursorKind.FUNCTION_TEMPLATE,
                    CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR, CursorKind.CONVERSION_FUNCTION]
        for member in container.get_children():
            #
            # Only emit items in the translation unit.
            #
            if member.location.file.name != self.tu.spelling:
                continue
            #
            # Skip almost anything which is private.
            #
            if member.access_specifier == AccessSpecifier.PRIVATE:
                #
                # We need to see:
                #
                #   - FN_KINDS for any existing constructors (no-copy constructor support) and any pure virtuals (for
                #     /Abstract/ support).
                #   - VARIABLE_KINDS to see any const variables (no-copy constructor support).
                #   - CursorKind.CXX_BASE_SPECIFIER just to preserve any inheritance (is this actually needed?).
                #   - CursorKind.CXX_ACCESS_SPEC_DECL so that changes in visibility are seen.
                #   - CursorKind.USING_DECLARATION for any functions being access-tweaked.
                #
                if member.kind in FN_KINDS + VARIABLE_KINDS + [CursorKind.CXX_ACCESS_SPEC_DECL,
                                                               CursorKind.CXX_BASE_SPECIFIER,
                                                               CursorKind.USING_DECLARATION]:
                    pass
                else:
                    if self.dump_privates:
                        logger.debug("Ignoring private {}".format(SipGenerator.describe(member)))
                    continue
            decl = ""
            if member.kind in FN_KINDS:
                #
                # Abstract?
                #
                if member.is_pure_virtual_method():
                    sip["annotations"].add("Abstract")
                had_copy_constructor = had_copy_constructor or is_copy_constructor(member)
                #
                # SIP needs to see private functions at least for the case described in
                # https://www.riverbankcomputing.com/pipermail/pyqt/2017-March/038944.html.
                #
                decl, tmp = self._fn_get(container, member, level + 1, is_signal)
                module_code.update(tmp)
            elif member.kind == CursorKind.ENUM_DECL:
                decl = self._enum_get(container, member, level + 1) + ";\n"
            elif member.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
                decl, is_signal = self._get_access_specifier(member, level + 1)
            elif member.kind == CursorKind.TYPEDEF_DECL:
                #
                # Typedefs for inlined enums/structs/unions seem to be emitted twice. Refer back to original.
                # There should be only one child...
                #
                typedef_children = list(member.get_children())
                if len(typedef_children) == 1 and typedef_children[0].kind in [CursorKind.ENUM_DECL,
                                                                               CursorKind.STRUCT_DECL,
                                                                               CursorKind.UNION_DECL]:
                    child = typedef_children[0]
                    if child.kind == CursorKind.ENUM_DECL:
                        original = "enum {}\n".format(child.displayname or "__enum{}".format(child.extent.start.line))
                        typedef = "enum {}\n".format(member.type.spelling)
                    elif child.kind == CursorKind.STRUCT_DECL:
                        original = "struct {}\n".format(child.displayname or "__struct{}".format(child.extent.start.line))
                        typedef = "struct {}\n".format(member.type.spelling)
                    elif child.kind == CursorKind.UNION_DECL:
                        original = "union {}\n".format(child.displayname or "__union{}".format(child.extent.start.line))
                        #
                        # Render a union as a struct. From the point of view of the accessors created for the bindings,
                        # this should behave as expected!
                        #
                        typedef = "/* union */ struct {}\n".format(member.type.spelling)
                    body = body.replace(original, typedef, 1)
                else:
                    decl, tmp = self._typedef_get(container, member, level + 1)
                    module_code.update(tmp)
            elif member.kind == CursorKind.CXX_BASE_SPECIFIER:
                #
                # Strip off the leading "class". Except for TypeKind.UNEXPOSED...
                #
                base_specifiers.append(member.type.get_canonical().spelling)
            elif member.kind == CursorKind.TEMPLATE_TYPE_PARAMETER:
                template_parameters.append((member.spelling, member.extent))
            elif member.kind == CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
                #
                # Weird: nameless template parameters don't show up as members:
                #
                # - Given "template <T, int U, typename V>", we get called for "int U" and "typename V", and not T.
                # - Given "template <T, int U, V>" we get called for "int U" and ">", and not T or V.
                # - Even container.displayname gets terribly confused!
                #
                # We'll fix this up later. For now, just record the point before which any
                # nameless template must have ended or after which any must start.
                #
                if member.spelling:
                    template_parameters.append((member.spelling, member.extent))
                else:
                    #
                    # This is the case that given "template <T, int U, V>" we get called for ">".
                    #
                    template_parameters.append((None, SourceRange.from_locations(member.location, member.location)))
            elif member.kind in [CursorKind.VAR_DECL, CursorKind.FIELD_DECL]:
                had_const_member = had_const_member or member.type.is_const_qualified()
                if member.access_specifier != AccessSpecifier.PRIVATE:
                    decl, tmp = self._var_get(container, member, level + 1)
                    module_code.update(tmp)
                elif self.dump_privates:
                    logger.debug("Ignoring private {}".format(SipGenerator.describe(member)))
            elif member.kind in [CursorKind.NAMESPACE, CursorKind.CLASS_DECL,
                                 CursorKind.CLASS_TEMPLATE, CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
                                 CursorKind.STRUCT_DECL, CursorKind.UNION_DECL]:
                decl, tmp = self._container_get(member, level + 1, h_file, include_filename)
                module_code.update(tmp)
            elif member.kind in TEMPLATE_KINDS + [CursorKind.USING_DIRECTIVE,
                                                  CursorKind.CXX_FINAL_ATTR]:
                #
                # Ignore:
                #
                #   TEMPLATE_KINDS: Template type parameter.
                #   CursorKind.USING_DIRECTIVE: Using? Pah!
                #   CursorKind.CXX_FINAL_ATTR: Again, not much to be done with this.
                #
                pass
            elif member.kind == CursorKind.USING_DECLARATION and in_class(member):
                #
                # If we are not in a class, a USING_DECLARATION cannot be modifying access levels.
                #
                decl, tmp = self._using_get(container, member, level + 1)
                module_code.update(tmp)
            else:
                text = self._read_source(member.extent)
                if self.skippable_attribute(container, member, text, sip):
                    if not sip["name"]:
                        return "", module_code
                elif member.kind == CursorKind.UNEXPOSED_DECL:
                    decl, tmp = self._unexposed_get(container, member, text, level + 1)
                    module_code.update(tmp)
                else:
                    SipGenerator._report_ignoring(container, member)
            if decl:
                if self.verbose:
                    pad = " " * ((level + 1) * 4)
                    body += pad + "// {}\n".format(SipGenerator.describe(member))
                body += decl

        if container.kind == CursorKind.TRANSLATION_UNIT:
            return body, module_code

        if container.kind == CursorKind.NAMESPACE:
            container_type = "namespace " + sip["name"]
        elif container.kind in [CursorKind.CLASS_DECL, CursorKind.CLASS_TEMPLATE,
                                CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION]:
            container_type = "class " + sip["name"]
            if template_parameters:
                tokens = SourceRange.from_locations(container.extent.start, template_parameters[-1][1].start)
                tokens = list(self.tu.get_tokens(extent=tokens))
                template_parameters = nameless_template_parameters_get(tokens, template_parameters)
        elif container.kind == CursorKind.STRUCT_DECL:
            if not sip["name"]:
                sip["name"] = "__struct{}".format(container.extent.start.line)
            container_type = "struct {}".format(sip["name"])
        elif container.kind == CursorKind.UNION_DECL:
            if not sip["name"]:
                sip["name"] = "__union{}".format(container.extent.start.line)
            container_type = "/* union */ struct {}".format(sip["name"])
        else:
            raise AssertionError(
                _("Unexpected container {}: {}[{}]").format(container.kind, sip["name"], container.extent.start.line))
        sip["decl"] = container_type
        sip["template_parameters"] = template_parameters
        sip["base_specifiers"] = base_specifiers

        pad = " " * (level * 4)
        #
        # Empty containers are still useful if they provide namespaces, classes or forward declarations.
        #
        if not body:
            text = self._read_source(container.extent)
            if not text.endswith("}"):
                #
                # Forward declaration.
                #
                modifying_rule = self.compiled_rules.forward_declaration_rules().apply(container, sip)
                if sip["name"]:
                    if modifying_rule:
                        body += trace_modified_by(container, modifying_rule)
                    if "External" in sip["annotations"]:
                        body += pad + sip["decl"]
                        body += " /External/;\n"
                    else:
                        body = pad + trace_discarded_by(container, "default forward declaration handling")
                else:
                    body = pad + trace_discarded_by(container, modifying_rule)
                return body, module_code
            else:
                #
                # Empty body provides a namespace or no-op subclass.
                #
                body = pad + "    // Empty!\n"
        #
        # Flesh out the SIP context for the rules engine.
        #
        sip["body"] = body
        #
        # Sigh. Clang seems to replace template parameter N of the form "T" in
        # various places with "type-parameter-0-N"...
        #
        if template_parameters:
            for i, p in enumerate(template_parameters):
                i = "type-parameter-0-{}".format(i)
                sip["body"] = sip["body"].replace(i, p)
                for j, b in enumerate(sip["base_specifiers"]):
                    sip["base_specifiers"][j] = b.replace(i, p)
        modifying_rule = self.compiled_rules.container_rules().apply(container, sip)
        if sip["name"]:
            decl = ""
            if modifying_rule:
                decl += pad + trace_modified_by(container, modifying_rule)
            #
            # Any type-related code (%BIGetBufferCode, %BIGetReadBufferCode, %BIGetWriteBufferCode,
            # %BIGetSegCountCode, %BIGetCharBufferCode, %BIReleaseBufferCode, %ConvertToSubClassCode,
            # %ConvertToTypeCode, %GCClearCode, %GCTraverseCode, %InstanceCode, %PickleCode, %TypeCode,
            # %TypeHeaderCode other type-related directives)?
            #
            modifying_rule = self.compiled_rules.typecode(container, sip)
            if modifying_rule:
                decl += pad + trace_modified_by(container, modifying_rule)
            decl += pad + sip["decl"]
            if sip["base_specifiers"]:
                decl += ": " + ", ".join(sip["base_specifiers"])
            if sip["annotations"]:
                decl += " /" + ",".join(sip["annotations"]) + "/"
            if sip["template_parameters"]:
                decl = pad + "template <" + ", ".join(sip["template_parameters"]) + ">\n" + decl
            decl += "\n" + pad + "{\n"
            decl += "%TypeHeaderCode\n#include <{}>\n%End\n".format(include_filename)
            decl += sip["code"]
            body = decl + sip["body"]
            #
            # Generate private copy constructor for non-copyable types.
            #
            if had_const_member and not had_copy_constructor and container.kind != CursorKind.NAMESPACE:
                body += pad + "private:\n"
                body += pad + "    " + trace_generated_for(container, self._container_get, "non-copyable type handling")
                body += pad + "    {}(const {} &);\n".format(sip["name"], sip["name"])
            body += pad + "};\n"
            if sip["module_code"]:
                module_code.update(sip["module_code"])
        else:
            body = pad + trace_discarded_by(container, modifying_rule)
        return body, module_code

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
        access_specifier = ""
        is_signal = False
        access_specifier_text = self._read_source(member.extent)
        if access_specifier_text == "Q_OBJECT":
            return access_specifier, is_signal
        pad = " " * ((level - 1) * 4)
        if access_specifier_text in ("Q_SIGNALS:", "signals:"):
            access_specifier = access_specifier_text
            is_signal = True
        elif access_specifier_text in ("public Q_SLOTS:", "public slots:", "protected Q_SLOTS:", "protected slots:"):
            access_specifier = access_specifier_text
        elif member.access_specifier == AccessSpecifier.PRIVATE:
            access_specifier = "private:"
        elif member.access_specifier == AccessSpecifier.PROTECTED:
            access_specifier = "protected:"
        elif member.access_specifier == AccessSpecifier.PUBLIC:
            access_specifier = "public:"
        else:
            access_specifier = "public: // Mapped from " + access_specifier_text
            logger.warn(_("// Replaced '{}' with 'public' (by {})".format(access_specifier_text,
                                                                          "access specifier handling")))
        decl = pad + access_specifier + "\n"
        return decl, is_signal

    def _enum_get(self, container, enum, level):
        pad = " " * (level * 4)
        decl = pad + "enum {}\n".format(enum.displayname or "__enum{}".format(enum.extent.start.line))
        decl += pad + "{\n"
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

    def _fn_get(self, container, function, level, is_signal):
        """
        Generate the translation for a function.

        :param container:           A class or namespace.
        :param function:            The function object.
        :param level:               Recursion level controls indentation.
        :param is_signal:           Is this a Qt signal?
        :return:                    A string.
        """
        if container.kind == CursorKind.TRANSLATION_UNIT and \
                (function.semantic_parent.kind == CursorKind.CLASS_DECL or
                 function.semantic_parent.kind == CursorKind.STRUCT_DECL) and \
                function.is_definition():
            # Skip inline methods
            return "", {}

        sip = {
            "name": function.spelling,
            "annotations": set(),
            "is_signal": is_signal,
        }
        #
        # Constructors for templated classes end up with spurious template parameters.
        #
        if function.kind == CursorKind.CONSTRUCTOR:
            sip["name"] = sip["name"].split("<")[0]
        parameters = []
        parameter_modifying_rules = []
        template_parameters = []
        module_code = {}
        for child in function.get_children():
            if child.kind == CursorKind.PARM_DECL:
                parameter = child.displayname or "__{}".format(len(parameters))
                #
                # So far so good, but we need any default value.
                #
                the_type = child.type.get_canonical()
                type_spelling = the_type.spelling
                #
                # Get rid of any pointer const-ness and add a pointer suffix. Not removing the const-ness causes
                # SIP to generate sequences which the C++ compiler seems to optimise away:
                #
                #   QObject* const a1 = 0;
                #
                #   if (sipParseArgs(..., &a1))
                #
                if the_type.kind == TypeKind.POINTER:
                    #
                    # Except that function pointers need special consideration. See elsewhere too...
                    #
                    fn_ptr = type_spelling.find("(*)")
                    if fn_ptr == -1:
                        decl = "{}* {}".format(the_type.get_pointee().spelling, parameter)
                    else:
                        decl = "{}(*{}){}".format(type_spelling[:fn_ptr], parameter, type_spelling[fn_ptr + 3:])
                else:
                    decl = "{} {}".format(type_spelling, parameter)
                    decl = decl.replace("* ", "*").replace("& ", "&")
                child_sip = {
                    "name": parameter,
                    "decl": decl,
                    "init": self._fn_get_parameter_default(function, child),
                    "annotations": set()
                }
                modifying_rule = self.compiled_rules.parameter_rules().apply(container, function, child, child_sip)
                if modifying_rule:
                    parameter_modifying_rules.append(trace_modified_by(child, modifying_rule))
                decl = child_sip["decl"]
                if child_sip["annotations"]:
                    decl += " /" + ",".join(child_sip["annotations"]) + "/"
                if child_sip["init"]:
                    decl += " = " + child_sip["init"]
                if child_sip["module_code"]:
                    module_code.update(child_sip["module_code"])
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
                if self.skippable_attribute(function, child, text, sip):
                    if not sip["name"]:
                        return "", module_code
                else:
                    SipGenerator._report_ignoring(function, child)
        #
        # Flesh out the SIP context for the rules engine.
        #
        sip["template_parameters"] = template_parameters
        if function.kind in [CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR]:
            sip["fn_result"] = ""
        else:
            sip["fn_result"] = function.result_type.get_canonical().spelling
            #
            # If the result is a function pointer, the canonical spelling is likely to be
            # a problem for SIP. Working out if we have such a case seems hand: the approach
            # now is the following heuristic...
            #
            #   - We have a pointer AND
            #   - We see what looks like the thing Clang seems to use for a function pointer
            #
            if function.result_type.get_canonical().kind == TypeKind.POINTER and sip["fn_result"].find("(*)") != -1:
                sip["fn_result"] = function.result_type.spelling
        sip["parameters"] = parameters
        sip["prefix"], sip["suffix"] = self._fn_get_decorators(function)
        modifying_rule = self.compiled_rules.function_rules().apply(container, function, sip)
        pad = " " * (level * 4)
        if sip["name"]:
            decl1 = ""
            if modifying_rule:
                decl1 += pad + trace_modified_by(function, modifying_rule)
            for modifying_rule in parameter_modifying_rules:
                decl1 += pad + modifying_rule
            decl = ""
            #
            # Any method-related code (%MethodCode, %VirtualCatcherCode, VirtualCallCode
            # or other method-related directives)?
            #
            modifying_rule = self.compiled_rules.methodcode(function, sip)
            if modifying_rule:
                decl1 += pad + trace_modified_by(function, modifying_rule)
            decl += self._function_render(function, sip, pad)
            decl = decl1 + decl
            if sip["module_code"]:
                module_code.update(sip["module_code"])
        else:
            decl = pad + trace_discarded_by(function, modifying_rule)
        return decl, module_code

    def _function_render(self, function, sip, pad):
        """
        Render a function as output text.

        :param function:
        :param sip:
        :param pad:
        :return:
        """
        decl = sip["name"] + "(" + ", ".join(sip["parameters"]) + ")"
        if sip["fn_result"]:
            if sip["fn_result"][-1] in "*&":
                decl = sip["fn_result"] + decl
            else:
                decl = sip["fn_result"] + " " + decl
        decl = pad + sip["prefix"] + decl + sip["suffix"]
        if sip["annotations"]:
            decl += " /" + ",".join(sip["annotations"]) + "/"
        if sip["template_parameters"]:
            decl = pad + "template <" + ", ".join(sip["template_parameters"]) + ">\n" + decl
        if sip["cxx_parameters"] or sip["cxx_fn_result"]:
            if not isinstance(sip["cxx_parameters"], str):
                sip["cxx_parameters"] = ", ".join(sip["cxx_parameters"])
            decl += "\n    " + pad + "["
            #
            # SIP does not want the result for constructors.
            #
            if function.kind != CursorKind.CONSTRUCTOR:
                if sip["cxx_fn_result"][-1] in "*&":
                    decl += sip["cxx_fn_result"]
                else:
                    decl += sip["cxx_fn_result"] + " "
            decl += "(" + sip["cxx_parameters"] + ")]"
        decl += ";\n"
        decl += sip["code"]
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

    #
    # There are many cases of parameter defaults we don't handle in _fn_get_parameter_default(). Try to catch those
    # that break our simple logic...
    #
    UNHANDLED_DEFAULT_TYPES = re.compile(
        r"[a-z0-9_]+<.*::.*>$|" +                           # Right-most "::" inside "<>".
                                                            #   QSharedPointer<Syndication::RSS2::Document>
        r"<.*\(.*\)>",                                      # Brackets "()" inside template "<>".
                                                            #   std::function<bool(const KPluginMetaData &)>()
        re.I)
    UNHANDLED_DEFAULT_EXPRESSION = re.compile(
        r"\(.*\).*\||\|.*\(.*\)",                           # "|"-op outside "()".
                                                            #   LookUpMode(exactOnly) | defaultOnly
        re.I)

    def _fn_get_parameter_default(self, function, parameter):
        """
        The parser does not seem to provide access to the complete text of a parameter.
        This makes it hard to find any default values, so we:

            1. Run the lexer from "here" to the end of the file, bailing out when we see the ","
            or a ")" marking the end.
            2. Watch for the assignment.
        """
        def _get_param_type(parameter):
            result = parameter.type.get_declaration().type

            if result.kind not in [TypeKind.ENUM, TypeKind.TYPEDEF] and parameter.type.kind == TypeKind.LVALUEREFERENCE:
                if parameter.type.get_pointee().get_declaration().type.kind != TypeKind.INVALID:
                    return parameter.type.get_pointee().get_declaration().type
                return parameter.type.get_pointee()

            if parameter.type.get_declaration().type.kind == TypeKind.INVALID:
                return parameter.type

            if parameter.type.get_declaration().type.kind == TypeKind.TYPEDEF:
                is_q_flags = False
                for member in parameter.type.get_declaration().get_children():
                    if member.kind == CursorKind.TEMPLATE_REF and member.spelling == "QFlags":
                        is_q_flags = True
                    if is_q_flags and member.kind == CursorKind.TYPE_REF:
                        result = member.type
                        break
            return result

        def _get_param_value(text, parameter):
            if text in ["", "0", "nullptr", "Q_NULLPTR"]:
                return text
            parameter_type = _get_param_type(parameter)
            if text == "{}":
                if parameter_type.kind == TypeKind.ENUM:
                    return "0"
                if parameter_type.kind == TypeKind.POINTER:
                    return "nullptr"
                if parameter_type.spelling.startswith("const "):
                    return parameter_type.spelling[6:] + "()"
                return parameter_type.spelling + "()"
            if "::" not in parameter_type.spelling:
                return text
            #
            # SIP wants things fully qualified. Without creating a full AST, we can only hope to cover the common
            # cases:
            #
            #   - Enums may come as a single value or an or'd list:
            #
            #       Input                       Output
            #       -----                       ------
            #       Option1                     parents::Option1
            #       Flag1|Flag3                 parents::Flag1|parents::Flag3
            #       FlagsType(Flag1|Flag3)      parents::FlagsType(parents::Flag1|parents::Flag3)
            #
            #   - Other stuff:
            #
            #       Input                       Output
            #       -----                       ------
            #       QString()                   QString::QString()
            #       QVector<const char*>()      QVector<const char *>::QVector<const char*>()
            #       QSharedPointer<Document>    QSharedPointer<Syndication::RSS2::Document>()
            #
            #
            if SipGenerator.UNHANDLED_DEFAULT_TYPES.search(parameter_type.spelling):
                logger.warn(_("Default for {} has unhandled type {}").format(SipGenerator.describe(parameter),
                                                                             parameter_type.spelling))
                return text
            if SipGenerator.UNHANDLED_DEFAULT_EXPRESSION.search(text):
                logger.warn(_("Default for {} has unhandled expression {}").format(SipGenerator.describe(parameter),
                                                                                   text))
                return text
            prefix = parameter_type.spelling.rsplit("::", 1)[0] + "::"
            tmp = re.split("[(|)]", text)
            if text.endswith(")"):
                tmp = tmp[:-1]
            tmp = [(word.rsplit("::", 1)[1] if "::" in word else word) for word in tmp]
            tmp = [prefix + word if word else "" for word in tmp]
            result = tmp[0]
            if len(tmp) > 1 or parameter_type.kind != TypeKind.ENUM:
                if text.endswith(")"):
                    result += "(" + "|".join(tmp[1:]) + ")"
                else:
                    result = "|".join(tmp)
            return result

        for member in parameter.get_children():
            if member.kind.is_expression():

                possible_extent = SourceRange.from_locations(parameter.extent.start, function.extent.end)
                text = ""
                bracket_level = 0
                found_start = False
                found_end = False
                was_punctuated = True
                for token in self.tu.get_tokens(extent=possible_extent):
                    #
                    # Now count balanced anything-which-can-contain-a-comma till we get to the end.
                    #
                    if bracket_level == 0 and token.spelling == "=" and not found_start:
                        found_start = True
                    elif bracket_level == 0 and token.spelling in ",)":
                        found_end = True
                        text = text[1:]
                        break
                    elif token.spelling in "<(":
                        bracket_level += 1
                    elif token.spelling in ")>":
                        bracket_level -= 1
                    if found_start:
                        if token.kind != TokenKind.PUNCTUATION and not was_punctuated:
                            text += " "
                        text += token.spelling
                        was_punctuated = token.kind == TokenKind.PUNCTUATION
                if not found_end and text:
                    RuntimeError(_("No end found for {}::{}, '{}'").format(function.spelling, parameter.spelling, text))
                #
                # SIP does not like outer brackets as in "(QHash<QColor,QColor>())". Get rid of them.
                #
                if text.startswith("("):
                    text = text[1:-1]
                #
                # Use some heuristics to format the default value as SIP wants in most cases.
                #
                return _get_param_value(text, parameter)
        return ""

    def _typedef_get(self, container, typedef, level):
        """
        Generate the translation for a typedef.

        :param container:           A class or namespace.
        :param typedef:             The typedef object.
        :param level:               Recursion level controls indentation.
        :return:                    A string.
        """
        sip = {
            "name": typedef.displayname,
            "annotations": set()
        }
        args = []
        result_type = ""
        module_code = {}
        for child in typedef.get_children():
            if child.kind == CursorKind.TEMPLATE_REF:
                result_type = child.displayname
            elif child.kind == CursorKind.TYPE_REF:
                #
                # Sigh. For results which are pointers, we dont have a way of detecting the need for the "*".
                #
                result_type = child.type.get_canonical().spelling
            elif child.kind == CursorKind.ENUM_DECL:
                #
                # Typedefs for enums are not suported by SIP, we deal wih them elsewhere.
                #
                assert False
            elif child.kind == CursorKind.STRUCT_DECL:
                if child.underlying_typedef_type:
                    #
                    # Typedefs for inlined structs seem to be emitted twice. Refer back to original.
                    #
                    struct = child.type.get_declaration()
                    decl = "__struct{}".format(struct.extent.start.line)
                else:
                    decl, tmp = self._container_get(child, level, None)
                    module_code.update(tmp)
                args.append(decl)
            elif child.kind == CursorKind.UNION_DECL:
                if child.underlying_typedef_type:
                    #
                    # Typedefs for inlined unions seem to be emitted twice. Refer back to original.
                    #
                    union = child.type.get_declaration()
                    decl = "__union{}".format(union.extent.start.line)
                else:
                    decl, tmp = self._container_get(child, level, None)
                    module_code.update(tmp)
                args.append(decl)
            elif child.kind == CursorKind.PARM_DECL:
                decl = child.displayname or "__{}".format(len(args))
                args.append((child.type.spelling, decl))
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
                if self.skippable_attribute(typedef, child, text, sip):
                    if not sip["name"]:
                        return "", module_code
                else:
                    SipGenerator._report_ignoring(typedef, child)
        #
        # Flesh out the SIP context for the rules engine.
        #
        sip["fn_result"] = ""
        if typedef.underlying_typedef_type.kind == TypeKind.MEMBERPOINTER:
            sip["fn_result"] = result_type
            args = ["{} {}".format(spelling, name) for spelling, name in args]
            sip["decl"] = ", ".join(args).replace("* ", "*").replace("& ", "&")
        elif typedef.underlying_typedef_type.kind == TypeKind.RECORD:
            sip["decl"] = result_type
        else:
            sip["decl"] = typedef.underlying_typedef_type.get_canonical().spelling
            #
            # If the typedef is for a function pointer, the canonical spelling is likely to be
            # a problem for SIP. Working out if we have such a case seems hand: the approach
            # now is the following heuristic...
            #
            #   - We are not dealing with a TypeKind.MEMBERPOINTER (handled above) AND
            #   (
            #   - The typedef has a result OR
            #   - We found some arguments OR
            #   - We see what looks like the thing Clang seems to use for a function pointer
            #   )
            #
            if typedef.result_type.kind != TypeKind.INVALID or args or sip["decl"].find("(*)") != -1:
                if typedef.result_type.kind != TypeKind.INVALID:
                    sip["fn_result"] = typedef.result_type.spelling
                else:
                    sip["fn_result"] = sip["decl"].split("(*)", 1)[0]
                args = [spelling for spelling, name in args]
                sip["decl"] = ", ".join(args).replace("* ", "*").replace("& ", "&")
        modifying_rule = self.compiled_rules.typedef_rules().apply(container, typedef, sip)
        #
        # Now the rules have run, add any prefix/suffix.
        #
        pad = " " * (level * 4)
        if sip["name"]:
            decl = ""
            if modifying_rule:
                decl += pad + trace_modified_by(typedef, modifying_rule)
            #
            # Any type-related code (%BIGetBufferCode, %BIGetReadBufferCode, %BIGetWriteBufferCode,
            # %BIGetSegCountCode, %BIGetCharBufferCode, %BIReleaseBufferCode, %ConvertToSubClassCode,
            # %ConvertToTypeCode, %GCClearCode, %GCTraverseCode, %InstanceCode, %PickleCode, %TypeCode
            # or %TypeHeaderCode)?
            #
            modifying_rule = self.compiled_rules.typecode(typedef, sip)
            if modifying_rule:
                decl += pad + trace_modified_by(typedef, modifying_rule)
            if sip["fn_result"]:
                decl += pad + "typedef {} (*{})({})".format(sip["fn_result"], sip["name"], sip["decl"])
                decl = decl.replace("* ", "*").replace("& ", "&")
            else:
                decl += pad + "typedef {} {}".format(sip["decl"], sip["name"])
            #
            # SIP does not support deprecation of typedefs.
            #
            sip["annotations"].discard("Deprecated")
            if sip["annotations"]:
                decl += " /" + ",".join(sip["annotations"]) + "/"
            decl += sip["code"] + ";\n"
            if sip["module_code"]:
                module_code.update(sip["module_code"])
        else:
            decl = pad + trace_discarded_by(typedef, modifying_rule)
        return decl, module_code

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
        # Flesh out the SIP context for the rules engine. NOTE: Typically, the sip["name"] for an unexposed item will
        # be "", and thus trigger the discard logic (unless there is a rule in place to set the sip["name"]!).
        #
        sip["decl"] = text
        module_code = {}
        modifying_rule = self.compiled_rules.unexposed_rules().apply(container, unexposed, sip)
        #
        # Now the rules have run, add any prefix/suffix.
        #
        pad = " " * (level * 4)
        if sip["name"]:
            decl = ""
            if modifying_rule:
                decl += pad + trace_modified_by(unexposed, modifying_rule, text)
            decl += pad + sip["decl"] + "\n"
            if sip["module_code"]:
                module_code.update(sip["module_code"])
        else:
            if not modifying_rule:
                modifying_rule = "default unexposed handling"
            decl = pad + trace_discarded_by(unexposed, modifying_rule, text)
        return decl, module_code

    def _using_get(self, container, using, level):
        """
        SIP does not support using declarations, so rule-writers will generally
        have to intervene.
        """
        sip = {
            "name": using.spelling,
            "annotations": set(),
        }
        module_code = {}
        #
        # Is this for a function or a variable?
        #
        is_function = False
        using_class = None
        for child in using.get_children():
            if child.kind == CursorKind.OVERLOADED_DECL_REF:
                is_function = True
            elif child.kind == CursorKind.TYPE_REF:
                using_class = child.spelling.split()[-1]
        if is_function:
            sip["template_parameters"] = []
            sip["fn_result"] = "void"
            sip["parameters"] = []
            sip["prefix"], sip["suffix"] = "", ""
            modifying_rule = self.compiled_rules.function_rules().apply(container, using, sip)
        else:
            sip["decl"] = ""
            modifying_rule = self.compiled_rules.variable_rules().apply(container, using, sip)
        #
        # Make it clear that we intervened.
        #
        if not modifying_rule:
            modifying_rule = "default using handling"
        pad = " " * (level * 4)
        if sip["name"]:
            decl = ""
            if modifying_rule:
                decl += pad + trace_modified_by(using, modifying_rule, using_class + "::" + using.spelling)
            if is_function:
                decl += self._function_render(using, sip, pad)
            else:
                decl += self._var_render(using, sip, pad)
            if sip["module_code"]:
                module_code.update(sip["module_code"])
        else:
            decl = pad + trace_discarded_by(using, modifying_rule, using_class + "::" + using.spelling)
        return decl, module_code

    def _var_get(self, container, variable, level):
        """
        Generate the translation for a variable.

        :param container:           A class or namespace.
        :param variable:            The variable object.
        :param level:               Recursion level controls indentation.
        :return:                    A string.
        """
        sip = {
            "name": variable.spelling,
            "annotations": set(),
        }
        module_code = {}
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
                if self.skippable_attribute(variable, child, text, sip):
                    if not sip["name"]:
                        return "", module_code
                else:
                    SipGenerator._report_ignoring(variable, child)
        #
        # Flesh out the SIP context for the rules engine.
        #
        decl = variable.type.get_canonical().spelling
        if variable.type.kind == TypeKind.ELABORATED and "anonymous" in decl:
            #
            # The spelling will be of the form 'N::n::(anonymous union at /usr/include/KF5/kjs/bytecode/opargs.h:66:5)'
            #
            words = decl.split("(", 1)[1][:-1]
            words = re.split("[ :]", words)
            assert words[1] in ["enum", "struct", "union"]
            #
            # Render a union as a struct. From the point of view of the accessors created for the bindings,
            # this should behave as expected!
            #
            if words[1] == "union":
                decl = "/* union */ struct __struct" + words[-2]
            else:
                decl = words[1] + " __" + words[1] + words[-2]
        sip["decl"] = decl
        #
        # Before the rules have run, add/remove any prefix.
        #
        self._var_get_keywords(container, variable, sip)
        modifying_rule = self.compiled_rules.variable_rules().apply(container, variable, sip)
        pad = " " * (level * 4)
        if sip["name"]:
            decl = ""
            if modifying_rule:
                decl += pad + trace_modified_by(variable, modifying_rule)
            decl += self._var_render(variable, sip, pad)
            #
            # SIP does not support protected variables, so we ignore them.
            #
            if variable.access_specifier == AccessSpecifier.PROTECTED:
                decl = pad + trace_discarded_by(variable, "protected handling")
                return decl, {}
            if sip["module_code"]:
                module_code.update(sip["module_code"])
        else:
            decl = pad + trace_discarded_by(variable, modifying_rule)
        return decl, module_code

    def _var_render(self, variable, sip, pad):
        """
        Render a variable as output text.

        :param variable:
        :param sip:
        :param pad:
        :return:
        """
        decl = pad + sip["decl"]
        if decl[-1] not in "*&":
            decl += " "
        decl += sip["name"]
        if sip["annotations"]:
            decl += " /" + ",".join(sip["annotations"]) + "/"
        decl = decl + sip["code"] + ";\n"
        return decl

    def _var_get_keywords(self, container, variable, sip):
        """
        The parser does not provide direct access to the complete keywords (static, etc) of a variable
        in the displayname. It would be nice to get these from the AST, but I cannot find where they are hiding.

        :param container:                   The variable's container.
        :param variable:                    The variable object.
        :param sip:                         The variable's sip. The decl will be updated with any prefix keywords.
        """
        #
        # HACK...we seem to get "char const[5]" instead of "const char[5]".
        #
        if re.search(r" const\b", sip["decl"]):
            sip["decl"] = "const " + sip["decl"].replace(" const", "")
        if re.search(r"\w\[", sip["decl"]):
            sip["decl"] = sip["decl"].replace("[", " [").replace("] [", "][")
        prefix = ""
        if variable.storage_class == StorageClass.STATIC:
            prefix += "static "
        elif variable.storage_class == StorageClass.EXTERN:
            prefix += "extern "
        sip["decl"] = prefix + sip["decl"]

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
        logger.debug(_("Ignoring {} {} child {}").format(parent.kind.name, parent.spelling,
                                                         SipGenerator.describe(child, text)))


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
    parser.add_argument("--include_filename", help=_("C++ header include to compile"))
    parser.add_argument("--dump-rule-usage", action="store_true", default=False,
                        help=_("Debug dump rule usage statistics"))
    parser.add_argument("libclang", help=_("libclang library to use for parsing"))
    parser.add_argument("rules", help=_("Project rules package"))
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
        rules_pkg = os.path.normpath(args.rules)
        if rules_pkg.endswith("__init__.py"):
            rules_pkg = os.path.dirname(rules_pkg)
        elif rules_pkg.endswith(".py"):
            rules_pkg = rules_pkg[:-3]
        g = SipGenerator(rules_pkg, args.flags.lstrip().split(";"), args.verbose)
        body, module_code, includes = g.create_sip(args.source, args.include_filename)
        with open(args.output, "w") as f:
            #
            # The module_code dictionary ensures there can be no duplicates, even if multiple sip files might have
            # contributed the same item. By emitting it here, it can provide declare-before-use (needed for
            # %Exceptions).
            #
            for mc in sorted(module_code):
                f.write("\n\n")
                f.write(module_code[mc])
                f.write("\n\n")
            f.write(body)
        #
        # Dump a summary of the rule usage.
        #
        if args.dump_rule_usage:
            #
            # Fill the dict of the used rules.
            #
            def add_usage(rule, usage_count):
                rule_usage[str(rule)] = usage_count

            rule_usage = {}
            g.compiled_rules.dump_unused(add_usage)
            for rule in sorted(rule_usage.keys()):
                usage_count = rule_usage[rule]
                if usage_count:
                    logger.info(_("Rule {} used {} times".format(rule, usage_count)))
                else:
                    logger.warn(_("Rule {} was not used".format(rule)))
    except Exception as e:
        tbk = traceback.format_exc()
        print(tbk)
        return -1


if __name__ == "__main__":
    if sys.argv[1] != "--self-check":
        sys.exit(main())
    else:
        cindex.Config.set_library_file(sys.argv[2])
