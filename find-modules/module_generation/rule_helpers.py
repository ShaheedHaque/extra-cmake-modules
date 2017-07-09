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

import rules_engine


def noop(*args):
    """
    This action function "does nothing" but without causing a warning.
    """
    pass


def container_discard(container, sip, matcher):
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


def container_mark_forward_declaration_external(container, sip, matcher):
    sip["annotations"].add("External")


def container_mark_abstract(container, sip, matcher):
    sip["annotations"].add("Abstract")


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


def return_rewrite_mode_t_as_int(container, function, sip, matcher):
    sip["fn_result"] = "unsigned int"


def parameter_strip_class_enum(container, function, parameter, sip, matcher):
    sip["decl"] = sip["decl"].replace("class ", "").replace("enum ", "")


def function_discard_impl(container, function, sip, matcher):
    if function.extent.start.column == 1:
        sip["name"] = ""


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
        trace = rules_engine.trace_deleted_by(key, "duplicate delete")
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
        trace = rules_engine.trace_inserted_for(key, "duplicate make local")
        tmp = trace + "%If (!" + feature + ")\n" + tmp + "%End\n"
        sip["modulecode"][key] = tmp


def code_add_classes(basename, sip, rule, *classes):
    """
    Add code to insert missing class declarations.

    :param basename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param classes:         The classes to add.
    """
    feature = sip["name"].replace(".", "_") + "_" + os.path.splitext(basename)[0]
    tmp = ""
    for key in classes:
        tmp += "class " + key + ";\n"
    trace = rules_engine.trace_generated_for(sip["name"], rule["code"], "missing classes")
    tmp = trace + "%If (!" + feature + ")\n" + tmp + "%End\n"
    sip["code"] += tmp


def code_add_imports(basename, sip, rule, *modules):
    """
    Add code to insert missing class declarations.

    :param basename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param modules:         The modules to add.
    """
    feature = sip["name"].replace(".", "_") + "_" + os.path.splitext(basename)[0]
    tmp = ""
    for key in modules:
        tmp += "%Import(name=" + key + ")\n"
    trace = rules_engine.trace_generated_for(sip["name"], rule["code"], "missing imports")
    tmp = trace + "%If (!" + feature + ")\n" + tmp + "%End\n"
    sip["code"] += tmp
