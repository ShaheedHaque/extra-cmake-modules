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

from utils import decompose_template, fqn, trace_inserted_for, trace_discarded_by, trace_generated_for

ANNOTATIONS_RE = re.compile(" /.*/")

#
# By default, rules return None. This causes the rule-firing logic to emit
# diagnostics recording what, if anything, changed. Rules which want to
# suppress "nothing changed" messages should return SILENT_NOOP.
#
SILENT_NOOP = "do-not-report-lack-of-changes"


def initialise_cxx_decl(sip):
    """
    Initialise a C++ declaration.

    :param sip:
    :return: Any annotations we found.
    """
    annotations = []
    sip["cxx_parameters"] = []
    for p in sip["parameters"]:
        a = ANNOTATIONS_RE.search(p)
        if a:
            a = a.group()
            p = ANNOTATIONS_RE.sub("", p)
        else:
            a = ""
        annotations.append(a)
        sip["cxx_parameters"].append(p)
    sip["cxx_fn_result"] = sip["fn_result"]
    return annotations


def noop(*args):
    """
    This action function "does nothing" but without causing a warning.
    For example, using this as the action in an ForwardDeclarationDb entry can
    be used to override the default "drop forward declarations" rule.
    """
    return SILENT_NOOP


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


def modulecode_delete(filename, sip, rule, *keys):
    """
    Delete duplicate modulecode entries from the current module.
    This prevents clashes when the current module A, imports B and both define
    the same thing.

    :param filename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param keys:            The keys to the entries.
    """
    for key in keys:
        trace = trace_discarded_by(key, rule)
        del sip["modulecode"][key]
        sip["modulecode"][key] = trace


def modulecode_make_local(filename, sip, rule, *keys):
    """
    Make modulecode entries local to the current module using the feature name.
    This prevents clashes when the current module A, and another module B both:

        - define the same thing
        - are imported by a third module C

    :param filename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param keys:            The keys to the entries.
    """
    feature = os.path.splitext(filename)[0].replace(os.path.sep, "_")
    for key in keys:
        tmp = sip["modulecode"][key]
        trace = trace_inserted_for(key, rule)
        tmp = trace + "%If (!" + feature + ")\n" + tmp + "%End\n"
        sip["modulecode"][key] = tmp


def module_add_classes(filename, sip, rule, *classes):
    """
    Add missing class declarations to a module.

    :param filename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param classes:         The classes to add.
    """
    feature = os.path.splitext(filename)[0].replace(os.path.sep, "_")
    tmp = ""
    for key in classes:
        tmp += "class " + key + ";\n"
    trace = trace_generated_for(sip["name"], rule, "missing classes")
    tmp = trace + "%If (!" + feature + ")\n" + tmp + "%End\n"
    sip["code"] += tmp


def module_add_imports(filename, sip, rule, *modules):
    """
    Add missing imports to a module.

    :param filename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param modules:         The modules to add.
    """
    feature = os.path.splitext(filename)[0].replace(os.path.sep, "_")
    tmp = ""
    for key in modules:
        tmp += "%Import(name=" + key + ")\n"
    trace = trace_generated_for(sip["name"], rule, "missing imports")
    tmp = trace + "%If (!" + feature + ")\n" + tmp + "%End\n"
    sip["code"] += tmp


def module_delete_imports(filename, sip, rule, *modules):
    """
    Remove unwanted imports from a module.

    :param filename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param modules:         The modules to remove.
    """
    trace = trace_generated_for(sip["name"], rule, "delete imports")
    lines = []
    for l in sip["decl"].split("\n"):
        l = l.strip()
        if l.startswith("%Import"):
            m = l[:-1].split("=", 1)[1]
            if m in modules:
                lines.append(trace)
                lines.append("// " + l)
                continue
        lines.append(l)
    sip["decl"] = "\n".join(lines)


def module_yank_scoped_class(filename, sip, rule):
    """
    SIP does not support classes defined with a scoped name, such as A::B.
    We physically yank things into place.
    """
    child = "^    class " + sip["ctx"]["child"] + "\\b[^\n]*\n    {.*?(^    };)$"
    parent = "^    class " + sip["ctx"]["parent"] + "\\b[^\n]*\n    {.*?(^    };)$"
    trace_from = trace_generated_for(sip["name"], rule, "yanking '{}' into '{}'".format(sip["ctx"]["child"], sip["ctx"]["parent"]))
    trace_to = trace_generated_for(sip["name"], rule, "yanked '{}' into '{}'".format(sip["ctx"]["child"], sip["ctx"]["parent"]))
    #
    #
    #
    child = re.search(child, sip["decl"], re.DOTALL | re.MULTILINE)
    tmp = sip["decl"][:child.start(0)] + trace_from[:-1] + sip["decl"][child.end(0):]
    parent = re.search(parent, tmp, re.DOTALL | re.MULTILINE)
    sip["decl"] = tmp[:parent.start(1)] + trace_to + "    public:\n" + child.group(0) + "\n" + tmp[parent.start(1):]


def module_add_includes(filename, sip, rule, *includes):
    """
    There are many cases where adding a #include is a useful workaround.

    :param filename:        The filename of the module, e.g. KCoreAddonsmod.sip.
    :param sip:             The sip.
    :param rule:            The rule.
    :param includes:        The includes to add.
    """
    tmp = ""
    for key in includes:
        tmp += "#include " + key + "\n"
    trace = trace_generated_for(sip["name"], rule, "missing includes")
    tmp = trace + "%ModuleHeaderCode\n" + tmp + "%End\n"
    sip["code"] += tmp


def container_add_typedefs(container, sip, rule, *typedefs):
    """
    There are many cases of types which SIP cannot handle, but where adding a C++ typedef is a useful workaround.

    :param container:       The container in question.
    :param sip:             The sip.
    :param rule:            The rule.
    :param typedefs:        The typedefs to add.
    """
    def get_template(typedef, parent):
        """
        Any template parameters from the parent in "typedef" must be extracted,
        and presented as template parameters for the typedef, so for

            template<A, B, C, D>
            class Foo
            {
            public:
                typedef DoesNotUseBorC<A, D> Bar;
            }

        we need to extract <B, C> to enable:

            template<B, C>
            typedef Foo::Bar;

        TODO: this actually needs to take the templating_stack into account.
        """
        if parent.template_parameters is None:
            return None
        name, args = decompose_template(typedef)
        ids = []
        if args:
            for arg in args:
                ids.extend([a.strip() for a in re.split(",| |::|<|>|\*|&", arg) if a])
        ids.extend(name.split("::"))
        ids = [a for a in ids if a in parent.template_parameters]
        return ", ".join(ids)

    typeheadercode = ""
    trace = trace_generated_for(sip["name"], rule, "supplementary typedefs")
    for new_typedef, original_type in enumerate(typedefs):
        new_typedef = "__{}{}_t".format(container.spelling, new_typedef)
        typedef_template = get_template(original_type, container)
        #
        # Generate a C++ typedef in %TypeHeaderCode.
        #
        if typedef_template:
            typeheadercode += "    template<" + typedef_template + ">\n"
        typeheadercode += "    typedef " + original_type + " " + new_typedef + ";\n"
        sip["body"] = sip["body"].replace(original_type, new_typedef)
        sip["modulecode"][new_typedef] = "class " + new_typedef + ";\n"
    sip["code"] += trace + "%TypeHeaderCode\n" + typeheadercode + "%End\n"


def container_fake_derived_class(container, sip, rule):
    """
    There are many cases where SIP does not generate a derived class, and
    having a #define to fake one makes writing manual code easier. See

    https://www.riverbankcomputing.com/pipermail/pyqt/2017-June/039309.html

    :param container:       The container in question.
    :param sip:             The sip.
    :param rule:            The rule.
    :param includes:        The includes to add.
    """
    clazz = fqn(container)
    tmp = "#define sip{} {}\n".format(clazz.replace("::", "_"), clazz)
    trace = trace_generated_for(sip["name"], rule, "fake derived class")
    tmp = trace + "%TypeHeaderCode\n" + tmp + "%End\n"
    sip["code"] += tmp


def container_discard_templated_bases(container, sip, rule):
    """
    SIP cannot handle base templates like "class Foo: Bar<Baz>" without an
    intermediate typedef. For now, delete the base class. See

    https://www.riverbankcomputing.com/pipermail/pyqt/2017-August/039476.html

    :param container:       The container in question.
    :param sip:             The sip.
    :param rule:            The rule.
    :param includes:        The includes to add.
    """
    sip["base_specifiers"] = [b for b in sip["base_specifiers"] if "<" not in b]


def container_make_unassignable(container, sip, rule):
    """
    There are cases where the built-in logic cannot detect the need to make a class unassignable.

    :param container:       The container in question.
    :param sip:             The sip.
    :param rule:            The rule.
    """
    clazz = fqn(container)
    tmp = "    private:\n        {} &operator=(const {} &);\n".format(clazz, clazz)
    trace = trace_generated_for(sip["name"], rule, "dummy assignment")
    tmp = trace + tmp
    sip["body"] = tmp + sip["body"]


def container_make_uncopyable(container, sip, rule):
    """
    There are cases where the built-in logic cannot detect the need to make a class uncopyable.

    :param container:       The container in question.
    :param sip:             The sip.
    :param rule:            The rule.
    """
    clazz = fqn(container)
    tmp = "    private:\n        {}(const {} &);\n".format(clazz, clazz)
    trace = trace_generated_for(sip["name"], rule, "dummy copy constructor")
    tmp = trace + tmp
    sip["body"] = tmp + sip["body"]
