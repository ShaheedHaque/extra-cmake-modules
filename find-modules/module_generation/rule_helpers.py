#
# Copyright 2017 by Shaheed Haque (srhaque@theiet.org)
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

"""Some common rule actions, as a convenience for rule writers."""
import os
import re

from clangcparser import CursorKind


def cursor_parents(cursor):
    parents = ""
    parent = cursor.semantic_parent
    while parent and parent.kind != CursorKind.TRANSLATION_UNIT:
        parents = parent.spelling + "::" + parents
        parent = parent.semantic_parent
    if parent and not parents:
        return os.path.basename(parent.spelling)
    return parents[:-2]


def item_describe(item, alternate_spelling=None):
    if isinstance(item, str):
        return item
    if alternate_spelling is None:
        text = item.spelling
    else:
        text = alternate_spelling
    return "{} on line {} '{}::{}'".format(item.kind.name, item.extent.start.line, cursor_parents(item), text)


def trace_inserted_for(item, rule):
    trace = "// Inserted for {} (by {}):\n".format(item_describe(item), rule)
    return trace


def trace_discarded_by(item, rule):
    trace = "// Discarded {} (by {})\n".format(item_describe(item), rule)
    return trace


def trace_generated_for(item, rule, extra):
    trace = "// Generated for {} (by {}): {}\n".format(item_describe(item), rule, extra)
    return trace


def trace_modified_by(item, rule):
    trace = "// Modified {} (by {}):\n".format(item_describe(item), rule)
    return trace


def container_discard(container, sip, matcher):
    sip["name"] = ""


def forward_declaration_discard(container, sip, matcher):
    sip["name"] = ""


def function_discard(container, function, sip, matcher):
    sip["name"] = ""


def typedef_discard(container, typedef, sip, matcher):
    sip["name"] = ""


def variable_discard(container, variable, sip, matcher):
    sip["name"] = ""


def unexposed_discard(container, unexposed, sip, matcher):
    sip["name"] = ""


def container_discard_QSharedData_base(container, sip, matcher):
    sip["base_specifiers"].remove("QSharedData")


def container_mark_abstract(container, sip, matcher):
    sip["annotations"].add("Abstract")


def forward_declaration_mark_external(container, sip, matcher):
    sip["annotations"].add("External")


def parameter_in(container, function, parameter, sip, matcher):
    sip["annotations"].add("In")


def parameter_out(container, function, parameter, sip, matcher):
    sip["annotations"].add("Out")


def parameter_transfer_to_parent(container, function, parameter, sip, matcher):
    if function.is_static_method():
        sip["annotations"].add("Transfer")
    else:
        sip["annotations"].add("TransferThis")


def param_rewrite_mode_t_as_int(container, function, parameter, sip, matcher):
    sip["decl"] = sip["decl"].replace("mode_t", "unsigned int")


def parameter_strip_class_enum(container, function, parameter, sip, matcher):
    sip["decl"] = sip["decl"].replace("class ", "").replace("enum ", "")


def modulecode_delete(basename, sip, rule, *keys):
    """
    Delete duplicate modulecode entries from the current module.
    This prevents clashes when the current module A, imports B and both define
    the same thing.

    :param basename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param keys:            The keys to the entries.
    """
    for key in keys:
        trace = trace_discarded_by(key, rule)
        del sip["modulecode"][key]
        sip["modulecode"][key] = trace


def modulecode_make_local(basename, sip, rule, *keys):
    """
    Make modulecode entries local to the current module using the feature name.
    This prevents clashes when the current module A, and another module B both:

        - define the same thing
        - are imported by a third module C

    :param basename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param keys:            The keys to the entries.
    """
    feature = sip["name"].replace(".", "_") + "_" + os.path.splitext(basename)[0]
    for key in keys:
        tmp = sip["modulecode"][key]
        trace = trace_inserted_for(key, rule)
        tmp = trace + "%If (!" + feature + ")\n" + tmp + "%End\n"
        sip["modulecode"][key] = tmp


def module_add_classes(basename, sip, rule, *classes):
    """
    Add missing class declarations to a module.

    :param basename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param classes:         The classes to add.
    """
    feature = sip["name"].replace(".", "_") + "_" + os.path.splitext(basename)[0]
    tmp = ""
    for key in classes:
        tmp += "class " + key + ";\n"
    trace = trace_generated_for(sip["name"], rule, "missing classes")
    tmp = trace + "%If (!" + feature + ")\n" + tmp + "%End\n"
    sip["code"] += tmp


def module_add_imports(basename, sip, rule, *modules):
    """
    Add missing imports to a module.

    :param basename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param modules:         The modules to add.
    """
    feature = sip["name"].replace(".", "_") + "_" + os.path.splitext(basename)[0]
    tmp = ""
    for key in modules:
        tmp += "%Import(name=" + key + ")\n"
    trace = trace_generated_for(sip["name"], rule, "missing imports")
    tmp = trace + "%If (!" + feature + ")\n" + tmp + "%End\n"
    sip["code"] += tmp


def container_add_supplementary_typedefs(container, sip, rule, *typedefs):
    """
    There are many cases of types which SIP cannot handle, but where adding a C++ typedef is a useful workaround.

    :param container:       The container in question.
    :param sip:             The sip.
    :param rule:            The rule.
    :param typedefs:        The typedefs to add.
    """
    def get_template(text):
        QUALIFIED_ID = re.compile("(?:[a-z_][a-z_0-9]*::)*([a-z_][a-z_0-9]*)$", re.I)
        args = text.split("<", 1)[-1]
        args = args.rsplit(">", 1)[0]
        if args == text:
            return None
        args = [a.strip() for a in args.split(",")]
        args = [a for a in args if QUALIFIED_ID.match(a)]
        if args == text:
            return "<" + ", ".join(args) + ">"
        else:
            return ""

    basename = os.path.basename(container.translation_unit.spelling)
    feature = sip["name"].replace(".", "_") + "_" + os.path.splitext(basename)[0]
    tmp = ""
    for key, value in enumerate(typedefs):
        key = "__{}{}_t".format(container.spelling, key)
        template = get_template(value)
        if template:
            tmp += "    template" + template + "\n"
            key += template
        tmp += "    typedef " + value + " " + key + ";\n"
        sip["body"] = sip["body"].replace(value, key)
    trace = trace_generated_for(sip["name"], rule, "supplementary typedefs")
    tmp = trace + "%TypeHeaderCode\n" + tmp + "%End\n"
    sip["code"] += tmp


def container_add_supplementary_includes(container, sip, rule, *includes):
    """
    There are many cases where adding a #include is a useful workaround.

    :param container:       The container in question.
    :param sip:             The sip.
    :param rule:            The rule.
    :param includes:        The includes to add.
    """
    basename = os.path.basename(container.translation_unit.spelling)
    feature = sip["name"].replace(".", "_") + "_" + os.path.splitext(basename)[0]
    tmp = ""
    for key in includes:
        tmp += "#include " + key + "\n"
    trace = trace_generated_for(sip["name"], rule, "supplementary includes")
    tmp = trace + "%TypeHeaderCode\n" + tmp + "%End\n"
    sip["code"] += tmp
