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
import subprocess
import sys
import traceback

from clang.cindex import AccessSpecifier, Config, Index, SourceRange, StorageClass, TokenKind, TypeKind
import pcpp.preprocessor

import clangcparser
import rule_helpers
import utils
from clangcparser import CursorKind
import rules_engine
from utils import item_describe, trace_discarded_by, trace_generated_for, trace_modified_by


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
VARIABLE_KINDS = [CursorKind.VAR_DECL, CursorKind.FIELD_DECL]
FN_KINDS = [CursorKind.CXX_METHOD, CursorKind.FUNCTION_DECL, CursorKind.FUNCTION_TEMPLATE,
            CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR, CursorKind.CONVERSION_FUNCTION]
#
# All Qt-specific logic is driven from these identifiers. Setting them to
# nonsense values would effectively disable all Qt-specific logic.
#
QFLAGS = "QFlags"
Q_NULLPTR = "Q_NULLPTR"
Q_OBJECT = "Q_OBJECT"
Q_SIGNALS = "Q_SIGNALS"
Q_SLOTS = "Q_SLOTS"
Q_DECLARE_PRIVATE = "Q_DECLARE_PRIVATE"
QScopedPointer = "QScopedPointer"
#
# Function pointers are a tricky area. We need to detect them by text matching.
#
FUNC_PTR = "(*)"
#
# Function decorator keywords.
#
FN_PREFIX_INLINE = "inline "
FN_PREFIX_STATIC = "static "
FN_PREFIX_VIRTUAL = "virtual "
FN_SUFFIX_CONST = " const"
FN_SUFFIX_PURE = " = 0"


class SourceProcessor(pcpp.preprocessor.Preprocessor):
    """
    Centralise all processing of the source.

    Ideally, we'd use Clang for everything, but on occasion, we'll need access
    to the source, both with and without pre-processing too, and for that we
    use pcpp.preprocessor.Preprocessor. At least by keeping all the logic here,
    we try to avoid drift between the two.
    """
    def __init__(self, exe_clang, compile_flags, verbose):
        super(SourceProcessor, self).__init__()
        self.exe_clang = exe_clang
        self.compile_flags = compile_flags
        self.verbose = verbose
        self.source = None
        self.unpreprocessed_source = []
        self.preproc = None

    def compile(self, source):
        """
        Use Clang to parse the source and return its AST.

        :param source:              The source file.
        """
        if source != self.source:
            self.unpreprocessed_source = []
            self.preproc = None
            self.source = source
        if self.verbose:
            logger.info(" ".join(self.compile_flags + [self.source]))
        tu = Index.create().parse(self.source, self.compile_flags)
        #
        # Stash ourselves on the tu for later use.
        #
        tu.source_processor = self
        return tu

    def on_error(self, file, line, msg):
        logger.error(msg)
        self.return_code += 1

    def on_warning(self, file, line, msg):
        logger.error(msg)

    def on_directive_unknown(self, directive, toks, ifpassthru):
        msg = _("Unknown directive '{}'").format("".join(tok.value for tok in toks))
        if directive.value == "warning":
            self.on_warning(directive.source, directive.lineno, msg)
        else:
            self.on_error(directive.source, directive.lineno, msg)
        return True

    def on_include_not_found(self, is_system_include, curdir, includepath):
        msg = _("Include file '{}' not found").format(includepath)
        self.on_error(self.lastdirective.source, self.lastdirective.lineno, msg)

    def unpreprocessed(self, extent, nl=" "):
        """
        Read the given range from the raw source.

        :param extent:              The range of text required.
        """
        assert self.source, "Must call compile() first!"
        if not self.unpreprocessed_source:
            self.unpreprocessed_source = self._read(self.source)
        text = self._extract(self.unpreprocessed_source, extent)
        if nl != "\n":
            text = text.replace("\n", nl)
        return text

    def preprocessed(self, extent, alternate_source=None, nl=" "):
        """
        Read the given range from the pre-processed source.

        :param extent:              The range of text required.
        """
        if alternate_source:
            lines = self._read(alternate_source)
            text = self._extract(lines, extent)
        else:
            text = self.unpreprocessed(extent, nl="\n")
        return self.expand(text, nl=nl)

    def expand(self, text, nl=" "):
        assert self.source, "Must call compile() first!"
        if not self.preproc:
            #
            # Clang cannot do -fsyntax-only...get the macros by hand.
            #
            cmd = [self.exe_clang] + self.compile_flags + ["-dM", "-E"] + [self.source]
            if self.verbose:
                logger.info(" ".join(cmd))
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = p.communicate()
            if stderr:
                logger.error(_("While expanding '{}':\n{})".format(text, stderr)))
            self.preproc = pcpp.preprocessor.Preprocessor()
            self.preproc.parser = self.preproc.parsegen(stdout)
            #
            # This is what takes the most time, not Clang preprocessing above!
            #
            self.preproc.write()
        #
        # Tokenize the input text (and then fixup the needed token.source).
        #
        tokens = self.preproc.tokenize(text)
        for t in tokens:
            t.source = self.source
        #
        # Now the actual expansion.
        #
        tokens = self.preproc.expand_macros(tokens)
        text = "".join([t.value for t in tokens])
        if nl != "\n":
            text = text.replace("\n", nl)
        return text

    def _read(self, source):
        lines = []
        with open(source, "rU") as f:
            for line in f:
                lines.append(line)
        return lines

    def _extract(self, lines, extent):
        extract = lines[extent.start.line - 1:extent.end.line]
        if extent.start.line == extent.end.line:
            extract[0] = extract[0][extent.start.column - 1:extent.end.column - 1]
        else:
            extract[0] = extract[0][extent.start.column - 1:]
            extract[-1] = extract[-1][:extent.end.column - 1]
        #
        # Return a single buffer of text.
        #
        return "".join(extract)


class TemplatingStack(list):
    """
    A stack of sets of templated objects.
    """
    def parameters_fixup(self, sip, key):
        """
        Clang seems to replace template parameter N of the form "T" with
        "type-parameter-<depth>-N"...so we need to put "T" back.

        :param sip:                 The sip.
        :param key:                 The key in the sip which may need
                                    fixing up.
        :return:
        """
        for depth, templated_object in enumerate(self):
            template_parameters = templated_object.template_parameters
            for clang_parameter, real_parameter in enumerate(template_parameters):
                clang_parameter = "type-parameter-{}-{}".format(depth, clang_parameter)
                #
                # Depending on the type of the SIP entry, replace the Clang
                # version of the value with the actual version.
                #
                assert not isinstance(real_parameter, tuple)
                value = sip[key]
                if isinstance(value, str):
                    sip[key] = value.replace(clang_parameter, real_parameter)
                elif isinstance(value, list):
                    for j, item in enumerate(value):
                        sip[key][j] = item.replace(clang_parameter, real_parameter)
                elif isinstance(value, dict):
                    for j, item in value.items():
                        sip[key][j] = item.replace(clang_parameter, real_parameter)

    def push_first(self, templated_object, new_parameter):
        """
        Push a new level onto the stack, and add a new parameter.
        """
        if not self or self[-1] is not templated_object:
            self.append(templated_object)
        if templated_object.template_parameters is None:
            templated_object.template_parameters = []
        templated_object.template_parameters.append(new_parameter)

    def pop_last(self, templated_object):
        """
        Pop an old level off the stack as needed.
        """
        if self and self[-1] is templated_object:
            self.pop()


class SipGenerator(object):
    def __init__(self, exe_clang, rules_pkg, compile_flags, dump_modules=False, dump_items=False, dump_includes=False,
                 dump_privates=False, verbose=False):
        """
        Constructor.

        :param exe_clang:           The Clang compiler.
        :param rules_pkg:           The rules for the file.
        :param compile_flags:       The compile flags for the file.
        :param dump_modules:        Turn on tracing for modules.
        :param dump_items:          Turn on tracing for container members.
        :param dump_includes:       Turn on diagnostics for include files.
        :param dump_privates:       Turn on diagnostics for omitted private items.
        :param verbose:             Turn on diagnostics for command lines.
        """
        self.exe_clang = exe_clang
        self.compiled_rules = rules_engine.rules(rules_pkg)
        self.compile_flags = compile_flags
        self.dump_modules = dump_modules
        self.dump_items = dump_items
        self.dump_includes = dump_includes
        self.dump_privates = dump_privates
        self.verbose = verbose
        self.diagnostics = set()
        self.tu = None
        self.source_processor = None

    def create_sip(self, h_file, include_filename):
        """
        Actually convert the given source header file into its SIP equivalent.
        This is the main entry point for this class.

        :param h_file:              The source header file of interest.
        :param include_filename:    The short header to include in the sip file.
        :returns: A (body, modulecode, includes). The body is the SIP text
                corresponding to the h_file, it can be a null string indicating
                there was nothing that could be generated. The modulecode is
                a dictionary of fragments of code that are to be emitted at
                module scope. The includes is a iterator over the files which
                clang #included while processing h_file.
        """
        #
        # Read in the original file.
        #
        source = h_file
        self.source_processor = SourceProcessor(self.exe_clang, ["-x", "c++"] + self.compile_flags, self.verbose)
        tu = self.source_processor.compile(source)
        self.tu = clangcparser.TranslationUnitCursor(tu.cursor)
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
            logger.log(diag.severity, "While parsing: {}".format(msg))
        if self.dump_includes:
            logger.info(_("File {} (include {})").format(h_file, include_filename))
            for include in sorted(set(self.tu.get_includes())):
                logger.info(_("    #includes {}").format(include.include.name))
        #
        # Run through the top level children in the translation unit.
        #
        body, modulecode = self._container_get(self.tu, -1, h_file, include_filename, TemplatingStack())
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
            if self.dump_modules:
                logger.info(_("Processing module for {}").format(include_filename))
            modifying_rule = self.compiled_rules.modulecode(include_filename, sip)
            if sip["name"]:
                if modifying_rule:
                    body += "// Modified {} (by {}):\n".format(include_filename, modifying_rule)
                body += sip["decl"] + sip["code"]
                #
                # Support any global externs.
                #
                body = """
%ModuleHeaderCode
#include <{}>
%End\n""".format(include_filename) + body
            else:
                body = "// Discarded {} (by {}):\n".format(h_name, modifying_rule)
        return body, modulecode, self.tu.get_includes

    def skippable_attribute(self, parent, member, text, sip):
        """
        We don't seem to have access to the __attribute__(())s, but at least we can look for stuff we care about.

        :param parent:          Parent object.
        :param member:          The attribute.
        :param text:            The raw source corresponding to the region of member.
        :param sip:             the sip.
        """
        if member.kind == CursorKind.UNEXPOSED_ATTR and text.find("_DEPRECATED") != -1:
            sip["annotations"].add("Deprecated")
            return True
        if member.kind != CursorKind.VISIBILITY_ATTR:
            return False
        if member.spelling == "hidden":
            if self.dump_privates:
                SipGenerator._report_ignoring(parent, "hidden")
            sip["name"] = ""
            return True
        return False

    def _container_get(self, container, level, h_file, include_filename, templating_stack):
        """
        Generate the (recursive) translation for a class or namespace.

        :param container:           A class or namespace.
        :param level:               Recursion level controls indentation.
        :param h_file:              The source header file of interest.
        :param include_filename:    The short header to include in the sip file.
        :param templating_stack:    The stack of sets of template parameters.
        :return:                    A string.
        """

        def in_class(item):
            parent = item.semantic_parent
            while parent and parent.kind != CursorKind.CLASS_DECL:
                parent = parent.semantic_parent
            return True if parent else False

        sip = {
            "name": container.spelling,
            "annotations": set()
        }
        body = ""
        base_specifiers = []
        had_copy_constructor = None
        need_private_copy_constructor = False
        had_assignment_operator = None
        modulecode = {}
        is_signal = False
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
                #   - Any existing constructors (no-copy constructor support).
                #   - Any destructors and virtuals (for SIP as per
                #     https://www.riverbankcomputing.com/pipermail/pyqt/2017-March/038944.html).
                #   - VARIABLE_KINDS to see any const variables (no-copy constructor support).
                #   - CursorKind.CXX_ACCESS_SPEC_DECL so that changes in visibility are seen.
                #   - CursorKind.USING_DECLARATION for any functions being access-tweaked.
                #
                if (member.kind == CursorKind.CONSTRUCTOR and (member.is_converting_constructor() or
                                                                   member.is_copy_constructor() or
                                                                   member.is_default_constructor() or
                                                                   member.is_move_constructor())) or \
                      (member.kind == CursorKind.DESTRUCTOR) or \
                      (member.kind in FN_KINDS and member.is_virtual_method()) or \
                      (member.kind in VARIABLE_KINDS + [CursorKind.CXX_ACCESS_SPEC_DECL, CursorKind.USING_DECLARATION]):
                    pass
                else:
                    if self.dump_privates:
                        SipGenerator._report_ignoring(member, "private")
                    continue
            decl = ""
            if member.kind in FN_KINDS:
                #
                # Abstract?
                #
                if member.is_pure_virtual_method():
                    sip["annotations"].add("Abstract")
                elif member.is_copy_constructor():
                    if self.source_processor.preprocessed(member.extent).endswith("= delete;"):
                        need_private_copy_constructor = True
                        continue
                    else:
                        had_copy_constructor = member
                elif member.spelling == "operator=":
                    had_assignment_operator = member
                decl, tmp = self._fn_get(container, member, level + 1, is_signal, templating_stack)
                modulecode.update(tmp)
            elif member.kind == CursorKind.ENUM_DECL:
                decl, tmp = self._enum_get(container, member, level + 1)
                modulecode.update(tmp)
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
                    original = child.SIP_TYPE_NAME + " " + child.spelling + "\n"
                    typedef = child.SIP_TYPE_NAME + " " + member.type.spelling + "\n"
                    body = body.replace(original, typedef, 1)
                else:
                    decl, tmp = self._typedef_get(container, member, level + 1, h_file, include_filename,
                                                  templating_stack)
                    modulecode.update(tmp)
            elif member.kind == CursorKind.CXX_BASE_SPECIFIER:
                #
                # SIP does not want protected or private base specifiers...
                #
                if member.access_specifier == AccessSpecifier.PUBLIC:
                    base_specifiers.append(member.type.get_canonical().spelling)
            elif isinstance(member, clangcparser.TemplateParameterCursor):
                templating_stack.push_first(container, member.SIP_TYPE_NAME)
            elif isinstance(member, clangcparser.VariableCursor):
                if member.access_specifier != AccessSpecifier.PRIVATE:
                    decl, tmp = self._var_get(container, member, level + 1)
                    modulecode.update(tmp)
                else:
                    if member.type.is_const_qualified() or member.type.spelling.startswith(QScopedPointer):
                        need_private_copy_constructor = True
                    if self.dump_privates:
                        SipGenerator._report_ignoring(member, "private")
            elif member.kind in [CursorKind.NAMESPACE, CursorKind.CLASS_DECL,
                                 CursorKind.CLASS_TEMPLATE, CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
                                 CursorKind.STRUCT_DECL, CursorKind.UNION_DECL]:
                decl, tmp = self._container_get(member, level + 1, h_file, include_filename, templating_stack)
                modulecode.update(tmp)
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
                modulecode.update(tmp)
            else:
                text = self.source_processor.unpreprocessed(member.extent)
                if self.skippable_attribute(container, member, text, sip):
                    if not sip["name"]:
                        templating_stack.pop_last(container)
                        return "", modulecode
                elif member.kind == CursorKind.UNEXPOSED_DECL:
                    if text.startswith(Q_DECLARE_PRIVATE + "("):
                        need_private_copy_constructor = True
                    decl, tmp = self._unexposed_get(container, member, text, level + 1)
                    modulecode.update(tmp)
                else:
                    SipGenerator._report_ignoring(member, "unusable")
            if self.dump_items:
                logger.info(_("Processing {}").format(item_describe(member)))
                body += "// Processing {}\n".format(item_describe(member))
            if decl:
                body += decl

        if isinstance(container, clangcparser.TranslationUnitCursor):
            templating_stack.pop_last(container)
            return body, modulecode

        sip["decl"] = container.SIP_TYPE_NAME + " " + sip["name"]
        sip["template_parameters"] = container.template_parameters
        sip["base_specifiers"] = base_specifiers

        pad = " " * (level * 4)
        #
        # Empty containers are still useful if they provide namespaces, classes or forward declarations.
        #
        if not body:
            text = self.source_processor.unpreprocessed(container.extent)
            if not text.endswith("}"):
                #
                # Forward declaration.
                #
                modifying_rule = self.compiled_rules.forward_declaration_rules().apply(container, sip)
                if sip["name"]:
                    if modifying_rule:
                        body += trace_modified_by(container, modifying_rule)
                    body += pad + sip["decl"]
                    if sip["annotations"]:
                        body += " /" + ",".join(sip["annotations"]) + "/"
                    body += ";\n"
                else:
                    body = pad + trace_discarded_by(container, modifying_rule)
                templating_stack.pop_last(container)
                return body, modulecode
            else:
                #
                # Empty body provides a namespace or no-op subclass.
                #
                body = pad + "    // Empty!\n"
        #
        # Flesh out the SIP context for the rules engine.
        #
        sip["body"] = body
        templating_stack.parameters_fixup(sip, "body")
        templating_stack.parameters_fixup(sip, "base_specifiers")
        modifying_rule = self.compiled_rules.container_rules().apply(container, sip)
        if sip["name"]:
            decl = ""
            if modifying_rule:
                templating_stack.parameters_fixup(sip, "body")
                templating_stack.parameters_fixup(sip, "base_specifiers")
                decl += pad + trace_modified_by(container, modifying_rule)
            #
            # Any type-related code (%BIGetBufferCode, %BIGetReadBufferCode, %BIGetWriteBufferCode,
            # %BIGetSegCountCode, %BIGetCharBufferCode, %BIReleaseBufferCode, %ConvertToSubClassCode,
            # %ConvertToTypeCode, %GCClearCode, %GCTraverseCode, %InstanceCode, %PickleCode, %TypeCode,
            # %TypeHeaderCode other type-related directives)?
            #
            modifying_rule = self.compiled_rules.typecode(container, sip)
            if modifying_rule:
                templating_stack.parameters_fixup(sip, "body")
                templating_stack.parameters_fixup(sip, "base_specifiers")
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
            if isinstance(container, clangcparser.ContainerCursor) and container.initial_access_specifier:
                decl += pad + container.initial_access_specifier + "\n"
            decl += sip["code"]
            body = decl + sip["body"]
            if container.kind != CursorKind.NAMESPACE and not sip["decl"].startswith("%Exception"):
                #
                # Generate private copy constructor for non-copyable types.
                #
                if need_private_copy_constructor and not had_copy_constructor:
                    body += pad + "private:\n"
                    body += pad + "    " + trace_generated_for(container, "non-copyable type handling", {})
                    body += pad + "    {}(const {} &);\n".format(sip["name"], sip["name"])
                #
                # Generate private assignment operator for non-assignable types.
                #
                if had_assignment_operator:
                    body += pad + "private:\n"
                    body += pad + "    " + trace_generated_for(container, "non-assignable type handling", {})
                    body += pad + "    {} &operator=(const {} &);\n".format(sip["name"], sip["name"])
            body += pad + "};\n"
            if sip["modulecode"]:
                modulecode.update(sip["modulecode"])
        else:
            body = pad + trace_discarded_by(container, modifying_rule)
        templating_stack.pop_last(container)
        return body, modulecode

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
        access_specifier_text = self.source_processor.unpreprocessed(member.extent)
        if access_specifier_text == Q_OBJECT:
            return access_specifier, is_signal
        pad = " " * ((level - 1) * 4)
        if access_specifier_text in (Q_SIGNALS + ":", "signals:"):
            access_specifier = access_specifier_text
            is_signal = True
        elif access_specifier_text in ("public " + Q_SLOTS + ":", "public slots:", "protected " + Q_SLOTS + ":",
                                       "protected slots:"):
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
        sip = {
            "name": enum.spelling,
            "annotations": set(),
        }
        modulecode = {}
        enumerations = []
        for enumeration in enum.get_children():
            #
            # Skip visibility attributes and the like.
            #
            if enumeration.kind == CursorKind.ENUM_CONSTANT_DECL:
                enumerations.append(enumeration.displayname)
            else:
                SipGenerator._report_ignoring(enumeration, "unusable")
        sip["decl"] = "enum " + sip["name"]
        sip["enumerations"] = enumerations
        modifying_rule = self.compiled_rules.variable_rules().apply(container, enum, sip)
        pad = " " * (level * 4)
        if sip["name"]:
            decl = ""
            if modifying_rule:
                decl += pad + trace_modified_by(enum, modifying_rule)
            decl += pad + sip["decl"] + "\n"
            decl += pad + "{\n"
            decl += ",\n".join([pad + "    " + e for e in sip["enumerations"]]) + "\n"
            decl += pad + "}"
            if sip["annotations"]:
                decl += " /" + ",".join(sip["annotations"]) + "/"
            decl = decl + sip["code"] + ";\n"
            if sip["modulecode"]:
                modulecode.update(sip["modulecode"])
        else:
            decl = pad + trace_discarded_by(enum, modifying_rule)
        return decl, modulecode

    def _fn_get(self, container, fn, level, is_signal, templating_stack):
        """
        Generate the translation for a function.

        :param container:           A class or namespace.
        :param fn:                  The function object.
        :param level:               Recursion level controls indentation.
        :param is_signal:           Is this a Qt signal?
        :param templating_stack:    The stack of sets of template parameters.
        :return:                    A string.
        """
        #
        # Discard inline implementations of functions declared in a class/struct.
        #
        if fn.is_implementation(container):
            SipGenerator._report_ignoring(fn, "inline method")
            return "", {}

        sip = {
            "name": fn.spelling,
            "annotations": set(),
            "is_signal": is_signal,
        }
        #
        # Constructors for templated classes end up with spurious template parameters.
        #
        if fn.kind == CursorKind.CONSTRUCTOR:
            sip["name"] = sip["name"].split("<")[0]
        parameters = []
        parameter_modifying_rules = []
        modulecode = {}
        for child in fn.get_children():
            if child.kind == CursorKind.PARM_DECL:
                #
                # So far so good, but we need any default value.
                #
                decl = child.SIP_TYPE_NAME
                #
                # SIP does not support "const char *const foo".
                #
                decl = decl.replace("*const " + child.spelling, "*" + child.spelling)
                child_sip = {
                    "name": child.spelling,
                    "decl": decl,
                    "init": self._fn_get_parameter_default(fn, child),
                    "annotations": set()
                }
                templating_stack.parameters_fixup(child_sip, "decl")
                modifying_rule = self.compiled_rules.parameter_rules().apply(container, fn, child, child_sip)
                if modifying_rule:
                    templating_stack.parameters_fixup(child_sip, "decl")
                    parameter_modifying_rules.append(trace_modified_by(child, modifying_rule))
                decl = child_sip["decl"]
                if child_sip["annotations"]:
                    decl += " /" + ",".join(child_sip["annotations"]) + "/"
                if child_sip["init"]:
                    decl += " = " + child_sip["init"]
                if child_sip["modulecode"]:
                    templating_stack.parameters_fixup(child_sip, "modulecode")
                    modulecode.update(child_sip["modulecode"])
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
            elif isinstance(child, clangcparser.TemplateParameterCursor):
                templating_stack.push_first(fn, child.SIP_TYPE_NAME)
            else:
                text = self.source_processor.unpreprocessed(child.extent)
                if self.skippable_attribute(fn, child, text, sip):
                    if not sip["name"]:
                        templating_stack.pop_last(fn)
                        return "", modulecode
                else:
                    SipGenerator._report_ignoring(child, "unusable")
        #
        # Flesh out the SIP context for the rules engine.
        #
        sip["template_parameters"] = fn.template_parameters
        if fn.kind in [CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR]:
            sip["fn_result"] = ""
        else:
            #
            # If the function returns a function, emit the non-lowered type to
            # maximise the probability that SIP can handle the output.
            #
            if fn.result_type.get_canonical().is_a_function:
                sip["fn_result"] = fn.result_type.spelling
            else:
                sip["fn_result"] = fn.result_type.get_canonical().spelling
        sip["parameters"] = parameters
        sip["prefix"], sip["suffix"] = self._fn_get_decorators(container, fn)
        templating_stack.parameters_fixup(sip, "fn_result")
        templating_stack.parameters_fixup(sip, "parameters")
        modifying_rule = self.compiled_rules.function_rules().apply(container, fn, sip)
        pad = " " * (level * 4)
        if sip["name"]:
            decl1 = ""
            if modifying_rule:
                templating_stack.parameters_fixup(sip, "fn_result")
                templating_stack.parameters_fixup(sip, "parameters")
                decl1 += pad + trace_modified_by(fn, modifying_rule)
            for modifying_rule in parameter_modifying_rules:
                decl1 += pad + modifying_rule
            decl = ""
            #
            # Any method-related code (%MethodCode, %VirtualCatcherCode, VirtualCallCode
            # or other method-related directives)?
            #
            modifying_rule = self.compiled_rules.methodcode(fn, sip)
            if modifying_rule:
                templating_stack.parameters_fixup(sip, "fn_result")
                templating_stack.parameters_fixup(sip, "parameters")
                decl1 += pad + trace_modified_by(fn, modifying_rule)
            decl += self._function_render(fn, sip, pad)
            decl = decl1 + decl
            if sip["modulecode"]:
                templating_stack.parameters_fixup(sip, "modulecode")
                modulecode.update(sip["modulecode"])
        else:
            decl = pad + trace_discarded_by(fn, modifying_rule)
        templating_stack.pop_last(fn)
        return decl, modulecode

    def _function_render(self, fn, sip, pad):
        """
        Render a function as output text.
        """
        decl = sip["name"] + "(" + ", ".join(sip["parameters"]) + ")"
        if sip["fn_result"]:
            if sip["fn_result"][-1] in "*&":
                decl = sip["fn_result"] + decl
            else:
                decl = sip["fn_result"] + " " + decl
        #
        # Note that we never emit any "inline" prefix: it is only there to help rule-writers.
        #
        prefix = sip["prefix"].replace(FN_PREFIX_INLINE, "")
        decl = pad + prefix + decl + sip["suffix"]
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
            if fn.kind != CursorKind.CONSTRUCTOR:
                if sip["cxx_fn_result"][-1] in "*&":
                    decl += sip["cxx_fn_result"]
                else:
                    decl += sip["cxx_fn_result"] + " "
            decl += "(" + sip["cxx_parameters"] + ")]"
        decl += ";\n"
        decl += sip["code"]
        return decl

    def _fn_get_decorators(self, container, fn):
        """
        The parser does not provide direct access to the complete keywords (explicit, const, static, etc) of a function
        in the displayname. It would be nice to get these from the AST, but I cannot find where they are hiding.

        Now, we could resort to using the original source. That does not bode well if you have macros (QOBJECT,
        xxxDEPRECATED?), inlined bodies and the like, using the rule engine could be used to patch corner cases...

        ...or we can try to guess what SIP cares about, i.e static and maybe const. Luckily (?), we have those to hand!

        :param fn:                          The function object.
        :return: prefix, suffix             String containing any prefix or suffix keywords.
        """
        suffix = ""
        if fn.is_const_method():
            suffix += FN_SUFFIX_CONST
        prefix = ""
        if fn.is_definition():
            #
            # The support for "inline" is for the benefit of rule-writers who might, for example, need to suppress
            # *any* definition, not necessarily one that the user marked as "inline". It is never emitted.
            #
            prefix += FN_PREFIX_INLINE
        #
        # A namespace cannot have "virtual" or "static".
        #
        if container.kind != CursorKind.NAMESPACE:
            if fn.is_static_method():
                prefix += FN_PREFIX_STATIC
            if fn.is_virtual_method():
                prefix += FN_PREFIX_VIRTUAL
                if fn.is_pure_virtual_method():
                    suffix += FN_SUFFIX_PURE
        return prefix, suffix

    QUALIFIED_ID = re.compile("(?:[a-z_][a-z_0-9]*::)*([a-z_][a-z_0-9]*)", re.I)

    def _fn_get_parameter_default(self, function, parameter):
        """
        The parser does not seem to provide access to the complete text of a parameter.
        This makes it hard to find any default values, so we:

            1. Run the lexer from "here" to the end of the file, bailing out when we see the ","
            or a ")" marking the end.
            2. Watch for the assignment.
        """
        def decompose_arg(arg, spellings):
            template, args = utils.decompose_template(arg)
            spellings.append(template)
            if args is not None:
                for arg in args:
                    decompose_arg(arg, spellings)

        def _get_param_type(parameter):
            q_flags_enum = None
            canonical = underlying = parameter.type
            spellings = []
            while underlying:
                prefixes, name, operators, suffixes, next = underlying.decomposition()
                name, args = utils.decompose_template(name)
                #
                # We want the name (or name part of the template), plus any template parameters to deal with:
                #
                #  QList<KDGantt::Constraint> &constraints = QList<Constraint>()
                #
                spellings.append(name)
                if args is not None:
                    for arg in args:
                        decompose_arg(arg, spellings)
                    if name == QFLAGS:
                        #
                        # The name of the enum.
                        #
                        q_flags_enum = args[0]
                        return spellings, q_flags_enum, underlying
                canonical = underlying
                underlying = next
            return spellings, q_flags_enum, canonical.get_canonical()

        def _get_param_value(text, parameter):

            def mangler_enum(spellings, rhs, fqn):
                #
                # Is rhs the suffix of any of the typedefs?
                #
                for spelling in spellings[:-1]:
                    name, args = utils.decompose_template(spelling)
                    if name.endswith(rhs):
                        return name
                prefix = spellings[-1].rsplit("::", 1)[0] + "::"
                return prefix + rhs

            def mangler_other(spellings, rhs, fqn):
                #
                # Is rhs the suffix of any of the typedefs?
                #
                for spelling in spellings:
                    name, args = utils.decompose_template(spelling)
                    if name.endswith(rhs):
                        return name
                return fqn

            if text in ["", "0", "nullptr", Q_NULLPTR]:
                return text
            spellings, q_flags_enum, canonical_t = _get_param_type(parameter)
            if text == "{}":
                if q_flags_enum or canonical_t.kind == TypeKind.ENUM:
                    return "0"
                if canonical_t.kind == TypeKind.POINTER:
                    return "nullptr"
                #
                # TODO: return the lowest or highest type?
                #
                return spellings[-1] + "()"
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
            #       LookUpMode(exactOnly) | defaultOnly
            #                                   parents::LookUpMode(parents::exactOnly) | parents::defaultOnly
            #
            #     So, prefix any identifier with the prefix of the enum.
            #
            #   - For other cases, if any (qualified) id in the default value matches the RHS of the parameter
            #     type, use the parameter type.
            #
            if q_flags_enum or canonical_t.kind == TypeKind.ENUM:
                mangler = mangler_enum
            else:
                mangler = mangler_other
            tmp = ""
            match = SipGenerator.QUALIFIED_ID.search(text)
            while match:
                tmp += match.string[:match.start()]
                rhs = match.group(1)
                fqn = match.group()
                tmp += mangler(spellings, rhs, fqn)
                text = text[match.end():]
                match = SipGenerator.QUALIFIED_ID.search(text)
            tmp += text
            return tmp

        for member in parameter.get_children():
            if member.kind.is_expression():
                #
                # Get the text after the "=". Macro expansion can make relying on tokens fraught...and
                # member.get_tokens() simply does not always return anything.
                #
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
                        if (token.kind != TokenKind.PUNCTUATION and not was_punctuated) or (token.spelling in "*&"):
                            text += " "
                        text += token.spelling
                        was_punctuated = token.kind == TokenKind.PUNCTUATION
                if not found_end and text:
                    raise RuntimeError(_("No end found for {}::{}, '{}'").format(function.spelling, parameter.spelling,
                                                                                 text))
                #
                # SIP does not like outer brackets as in "(QHash<QColor,QColor>())". Get rid of them.
                #
                while text.startswith("("):
                    text = text[1:-1]
                #
                # Use some heuristics to format the default value as SIP wants in most cases.
                #
                return _get_param_value(text, parameter)
        return ""

    def _typedef_get(self, container, typedef, level, h_file, include_filename, templating_stack):
        """
        Generate the translation for a typedef.

        :param container:           A class or namespace.
        :param typedef:             The typedef object.
        :param level:               Recursion level controls indentation.
        :param h_file:              The source header file of interest.
        :param include_filename:    The short header to include in the sip file.
        :param templating_stack:    The stack of sets of template parameters.
        :return:                    A string.
        """
        sip = {
            "name": typedef.displayname,
            "annotations": set()
        }
        modulecode = {}
        for child in typedef.get_children():
            if child.kind in [CursorKind.STRUCT_DECL, CursorKind.UNION_DECL] and not child.underlying_type:
                decl, tmp = self._container_get(child, level, h_file, include_filename, templating_stack)
                modulecode.update(tmp)
            else:
                text = self.source_processor.unpreprocessed(child.extent)
                if self.skippable_attribute(typedef, child, text, sip):
                    if not sip["name"]:
                        return "", modulecode
                else:
                    SipGenerator._report_ignoring(child, "unusable")
        #
        # Flesh out the SIP context for the rules engine.
        #
        sip["decl"] = typedef.SIP_TYPE_NAME
        #
        # If the typedef is for a function type, emit the non-lowered type to
        # maximise the probability that SIP can handle the output.
        #
        if typedef.underlying_type.get_canonical().is_a_function:
            sip["fn_result"] = typedef.underlying_type.get_canonical().result_type.spelling
        else:
            sip["fn_result"] = ""
        templating_stack.parameters_fixup(sip, "decl")
        modifying_rule = self.compiled_rules.typedef_rules().apply(container, typedef, sip)
        #
        # Now the rules have run, add any prefix/suffix.
        #
        pad = " " * (level * 4)
        if sip["name"]:
            decl = ""
            if modifying_rule:
                templating_stack.parameters_fixup(sip, "decl")
                decl += pad + trace_modified_by(typedef, modifying_rule)
            #
            # Any type-related code (%BIGetBufferCode, %BIGetReadBufferCode, %BIGetWriteBufferCode,
            # %BIGetSegCountCode, %BIGetCharBufferCode, %BIReleaseBufferCode, %ConvertToSubClassCode,
            # %ConvertToTypeCode, %GCClearCode, %GCTraverseCode, %InstanceCode, %PickleCode, %TypeCode
            # or %TypeHeaderCode)?
            #
            modifying_rule = self.compiled_rules.typecode(typedef, sip)
            if modifying_rule:
                templating_stack.parameters_fixup(sip, "decl")
                decl += pad + trace_modified_by(typedef, modifying_rule)
            if sip["fn_result"]:
                decl += pad + "typedef {} (*{})({})".format(sip["fn_result"], sip["name"], sip["decl"])
                decl = decl.replace("* ", "*").replace("& ", "&")
            elif typedef.underlying_type.kind == TypeKind.DEPENDENTSIZEDARRAY:
                decl += pad + "typedef {}".format(sip["decl"])
            else:
                decl += pad + "typedef {} {}".format(sip["decl"], sip["name"])
            #
            # SIP does not support deprecation of typedefs.
            #
            sip["annotations"].discard("Deprecated")
            if sip["annotations"]:
                decl += " /" + ",".join(sip["annotations"]) + "/"
            decl += sip["code"] + ";\n"
            if sip["modulecode"]:
                templating_stack.parameters_fixup(sip, "modulecode")
                modulecode.update(sip["modulecode"])
        else:
            decl = pad + trace_discarded_by(typedef, modifying_rule)
        return decl, modulecode

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
        modulecode = {}
        modifying_rule = self.compiled_rules.unexposed_rules().apply(container, unexposed, sip)
        #
        # Now the rules have run, add any prefix/suffix.
        #
        pad = " " * (level * 4)
        if sip["name"]:
            decl = ""
            if modifying_rule:
                item = item_describe(unexposed, " ".join(text.split(None, 3)[:3]))
                decl += pad + trace_modified_by(item, modifying_rule)
            decl += pad + sip["decl"] + "\n"
            if sip["modulecode"]:
                modulecode.update(sip["modulecode"])
        else:
            if not modifying_rule:
                modifying_rule = "default unexposed handling"
            item = item_describe(unexposed, " ".join(text.split(None, 3)[:3]))
            decl = pad + trace_discarded_by(item, modifying_rule)
        return decl, modulecode

    def _using_get(self, container, using, level):
        """
        SIP does not support using declarations, so rule-writers will generally
        have to intervene.
        """
        sip = {
            "name": using.spelling,
            "annotations": set(),
        }
        modulecode = {}
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
                item = item_describe(using, using.spelling + " -> " + using_class)
                decl += pad + trace_modified_by(item, modifying_rule)
            if is_function:
                decl += self._function_render(using, sip, pad)
            else:
                decl += self._var_render(using, sip, pad)
            if sip["modulecode"]:
                modulecode.update(sip["modulecode"])
        else:
            item = item_describe(using, using.spelling + " -> " + using_class)
            decl = pad + trace_discarded_by(item, modifying_rule)
        return decl, modulecode

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
        modulecode = {}
        for child in variable.get_children():
            text = self.source_processor.unpreprocessed(child.extent)
            if self.skippable_attribute(variable, child, text, sip):
                if not sip["name"]:
                    return "", modulecode
            else:
                SipGenerator._report_ignoring(child, "unusable")
        #
        # Flesh out the SIP context for the rules engine.
        #
        the_type = variable.type
        if the_type.get_canonical().is_a_function:
            #
            # SIP does not generally like function pointers. Here the problem
            # is that variables just don't support canonical function pointers,
            # so use the typedef if one is known. Else, rules are needed to fix
            # them up. See rule_helpers.container_add_typedefs().
            #
            if the_type.spelling.find("(") == -1:
                decl = the_type.spelling
            else:
                the_type = the_type.get_canonical()
                decl = the_type.fmt_args()
        else:
            decl = the_type.get_canonical().spelling
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
            if sip["modulecode"]:
                modulecode.update(sip["modulecode"])
        else:
            decl = pad + trace_discarded_by(variable, modifying_rule)
        return decl, modulecode

    def _var_render(self, variable, sip, pad):
        """
        Render a variable as output text.

        :param variable:
        :param sip:
        :param pad:
        :return:
        """
        the_type = variable.type
        decl = sip["decl"]
        space = ("" if decl[-1] in "*&" else " ")
        if the_type.get_canonical().is_a_function:
            #
            # SIP does not generally like function pointers, so keep any typedef.
            #
            if the_type.spelling.find("(") == -1:
                decl = decl + space + sip["name"]
            else:
                the_type = the_type.get_canonical()
                result = the_type.fmt_result()
                decl = "{}({})({})".format(result, sip["name"], sip["decl"])
        else:
            prefixes, type_, operators, dims = utils.decompose_type(sip["decl"])
            decl = "".join(prefixes)
            decl += type_
            decl += " "
            decl += "".join(operators)
            decl += sip["name"]
            decl += "".join(dims)
        decl = pad + decl
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
        if "const " in sip["decl"]:
            sip["annotations"].add("NoSetter")
        if re.search(r"\w\[", sip["decl"]):
            sip["decl"] = sip["decl"].replace("[", " [").replace("] [", "][")
        prefix = ""
        if variable.storage_class == StorageClass.STATIC:
            prefix += "static "
        elif variable.storage_class == StorageClass.EXTERN:
            prefix += "extern "
        sip["decl"] = prefix + sip["decl"]

    @staticmethod
    def _report_ignoring(child, reason):
        logger.debug(_("Ignoring {} {}").format(reason, item_describe(child)))


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
        Config.set_library_file(args.libclang)
        exe_clang = "clang++-3.9"
        #
        # Generate!
        #
        rules_pkg = os.path.normpath(args.rules)
        if rules_pkg.endswith("__init__.py"):
            rules_pkg = os.path.dirname(rules_pkg)
        elif rules_pkg.endswith(".py"):
            rules_pkg = rules_pkg[:-3]
        g = SipGenerator(exe_clang, rules_pkg, args.flags.lstrip().split(";"), verbose=args.verbose)
        body, modulecode, includes = g.create_sip(args.source, args.include_filename)
        with open(args.output, "w") as f:
            #
            # The modulecode dictionary ensures there can be no duplicates, even if multiple sip files might have
            # contributed the same item. By emitting it here, it can provide declare-before-use (needed for
            # %Exceptions).
            #
            for mc in sorted(modulecode):
                f.write("\n\n")
                f.write(modulecode[mc])
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
    if sys.argv[-1] != "--self-check":
        sys.exit(main())
    else:
        Config.set_library_file(sys.argv[2])
