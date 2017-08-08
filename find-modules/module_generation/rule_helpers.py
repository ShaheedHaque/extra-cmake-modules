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

"""Some common rule actions, as a convenience for rule writers.

Here are some handy hints for rule writers, FAQ form...

0. My rule is not firing, how I can debug this?
===============================================

Try the following steps:

- Review the help text output by running "./rule_engine.py --help". Did you
  get the fields in your entry in the right order?

- The first field can be a bit tricky to get right. For the exact name that
  should be used, run "./module_generator.py" with the "--dump-items" option.

- Review the documentation on Python regular expressions. Note that when rule
  matching is done, multi-line entries are converted into a single line with
  any line separators turned into a single space (so a function with arguments
  wrapped across multipel lines is all on one line formatching purposes).

1. I want to keep a given forward declaration
=============================================

By default, built-in rules discard forward declarations because SIP does not
support a forward declaration followed by a real declaration is the same
module.

(See https://www.riverbankcomputing.com/pipermail/pyqt/2017-April/039094.html).

Override the default using a ForwardDeclarationDb rule with the noop() action.

20. I see a compilation error of the following type...
======================================================

    20.1. error: expected type-specifier before 'sipMyClass'
    ========================================================

    For a C++ class 'MyClass', SIP sometimes creates a subclass called
    'sipMyClass', but not always. This cannot easily be detected, and
    can result in this error in generated code.

    (See https://www.riverbankcomputing.com/pipermail/pyqt/2017-June/039309.html)

    This can be fixed using container_fake_derived_class().

    20.2. error: use of deleted function 'SomeClass& SomeClass::operator=(const SomeClass&)'
    ========================================================================================

    For a C++ class 'SomeClass', SIP creates a function called 'assign_SomeClass'
    but this relies on the operator= being present. C++ causes the default
    operator= to be suppressed resulting in this error if a base class
    cannot be so assigned.

    This can be fixed using container_make_unassignable().
"""
import os
import re

from clangcparser import CursorKind, TypeKind


ANNOTATIONS_RE = re.compile(" /.*/")

#
# By default, rules return None. This causes the rule-firing logic to emit
# diagnostics recording what, if anything, changed. Rules which want to
# suppress "nothing changed" messages should return SILENT_NOOP.
#
SILENT_NOOP = "do-not-report-lack-of-changes"


def fqn(cursor, alternate_spelling=None):
    """
    A handy helper to return the fully-qualified name for something.
    """
    parents = ""
    parent = cursor.semantic_parent
    while parent and parent.kind != CursorKind.TRANSLATION_UNIT:
        parents = parent.spelling + "::" + parents
        parent = parent.semantic_parent
    if alternate_spelling is None:
        text = cursor.spelling
    else:
        text = alternate_spelling
    return parents + text


def cursor_parents(cursor):
    """
    A helper function which returns the parents of a cursor in the forms:

        - A::B::C::...N for non-top level entities.
        - filename.h    for top level entities.
        - ""            in exceptional cases of having no parents.
    """
    parents = ""
    parent = cursor.semantic_parent
    while parent and parent.kind != CursorKind.TRANSLATION_UNIT:
        parents = parent.spelling + "::" + parents
        parent = parent.semantic_parent
    if parent and not parents:
        return os.path.basename(parent.spelling)
    return parents[:-2]


def item_describe(item, alternate_spelling=None):
    """
    A helper function providing a standardised description for an item,
    which may be a cursor.
    """
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
    There are many cases of types which SIP cannot handle, but where adding a C++ typedef is a useful workaround.

    :param container:       The container in question.
    :param sip:             The sip.
    :param rule:            The rule.
    """
    clazz = fqn(container)
    tmp = "    private:\n        {} &operator=(const {} &);\n".format(clazz, clazz)
    trace = trace_generated_for(sip["name"], rule, "dummy assignment")
    tmp = trace + tmp
    sip["body"] = tmp + sip["body"]


class HeldAs(object):
    """
    Items are held either as integral values, pointer values or objects. The
    Python interchange logic depends on this.

    TODO: In the case of pointers, we also need to know whether a specialised
    pointer type is in use (or just "*").
    """
    VOID = "void"
    BYTE = "BYTE"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    POINTER = "POINTER"
    OBJECT = "OBJECT"
    RE_BYTE = re.compile("^char\W|\Wchar\W|\Wchar$|^char$")
    RE_INTEGER = re.compile("^(short|int|long)\W|\W(short|int|long)\W|\W(short|int|long)$|^(short|int|long)$|^bool$")
    RE_FLOAT = re.compile("^(float|double)\W|\W(float|double)\W|\W(float|double)$|^(float|double)$")
    #
    # Clang primitive classifications corresponding to Python types.
    #
    _fwd_map = {
        BYTE: [TypeKind.CHAR_S, TypeKind.CHAR_U, TypeKind.SCHAR, TypeKind.UCHAR],
        INTEGER: [TypeKind.BOOL, TypeKind.CHAR16, TypeKind.CHAR32,
                  TypeKind.USHORT, TypeKind.UINT, TypeKind.ULONG, TypeKind.ULONGLONG, TypeKind.UINT128,
                  TypeKind.SHORT, TypeKind.INT, TypeKind.LONG, TypeKind.LONGLONG, TypeKind.INT128,
                  TypeKind.ENUM],
        FLOAT: [TypeKind.FLOAT, TypeKind.DOUBLE, TypeKind.FLOAT128, TypeKind.LONGDOUBLE],
        POINTER: [TypeKind.POINTER, TypeKind.MEMBERPOINTER],
        OBJECT: [TypeKind.RECORD],
    }
    _rev_map = None

    def __init__(self, cxx_t, clang_t, base_cxx_t=None):
        """
        :param cxx_t:                       The declaration text from the source code.
        :param clang_t:                     The Clang type or None.
        :param base_cxx_t:                  The base type, can be manually overridden.
        """
        self.cxx_t = cxx_t
        if base_cxx_t is None:
            base_cxx_t = self.base_type(cxx_t)
        #
        # This may be a mapped type.
        #
        self.is_mapped_type = ("<" in base_cxx_t)
        if self.is_mapped_type:
            self.sip_t = "sipFindType(cxx{name}S)"
        else:
            #
            # Primitive types don't need help from a sipType_xxx.
            #
            base_held_as = HeldAs.categorise(base_cxx_t, None)
            if base_held_as in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
                self.sip_t = base_held_as
            else:
                self.sip_t = "sipType_" + base_cxx_t.replace("::", "_")
        self.category = HeldAs.categorise(cxx_t, clang_t)

    def cxx_to_py_template(self):
        raise NotImplementedError()

    def py_to_cxx_template(self):
        raise NotImplementedError()

    @staticmethod
    def actual_type(parameter_text):
        """
        :param parameter_text:              The text from the source code.
        :return: the type of the parameter.
        """
        return parameter_text

    @staticmethod
    def base_type(parameter_text):
        """
        :param parameter_text:              The text from the source code.
        :return: the base_type of the parameter, e.g. without a pointer suffix.
        """
        if parameter_text.endswith(("*", "&")):
            parameter_text = parameter_text[:-1].strip()
        if parameter_text.startswith("const "):
            parameter_text = parameter_text[6:]
        return parameter_text

    @staticmethod
    def categorise(cxx_t, clang_t):
        """
        We would like to be able to use clang type system to determine the
        HELD_AS, but this is not always possible. For example, in a templated
        typedef, any int types are not even included in the children of the
        typedef. Similarly, in a variable declaration, a templated type might
        appear simply as TypeKind.UNEXPOSED.

        TODO: When we figure this out, get rid of the horrid heuristics.

        :param cxx_t:                       The text from the source code.
        :param clang_t:                     The Clang type or None.
        :return: the storage type of the object.
        """
        if cxx_t.endswith("*"):
            return HeldAs.POINTER
        elif cxx_t.endswith("&"):
            return HeldAs.categorise(cxx_t[:-1].strip(), clang_t)
        elif cxx_t == HeldAs.VOID:
            return HeldAs.VOID
        elif cxx_t.startswith("type-parameter-"):
            return HeldAs.OBJECT
        #
        # The clang type should be authoritative.
        #
        if clang_t is not None:
            #
            # One-time init of lookup map.
            #
            if not HeldAs._rev_map:
                HeldAs._rev_map = {}
                for key, values in HeldAs._fwd_map.items():
                    for value in values:
                        HeldAs._rev_map[value] = key
            #
            # Lookup.
            #
            try:
                return HeldAs._rev_map[clang_t.kind]
            except KeyError:
                if clang_t.kind == TypeKind.LVALUEREFERENCE:
                    return HeldAs.categorise(cxx_t, clang_t.underlying_type.get_canonical())
                elif clang_t.kind == TypeKind.VOID:
                    return HeldAs.VOID
                #
                # We we already know it did not seem to be a pointer, so check for a templated object:
                #
                #   TypeKind.ELABORATED: 'WTF::Vector<RegDescriptor *>'
                #   TypeKind.UNEXPOSED: 'HashMap<KJS::Interpreter *, ProtectedPtr<KJS::JSValue> >'
                #
                if "<" in cxx_t and clang_t.kind in [TypeKind.ELABORATED, TypeKind.UNEXPOSED]:
                    return HeldAs.OBJECT
                return HeldAs.OBJECT
        if "<" in cxx_t:
            return HeldAs.OBJECT
        if HeldAs.RE_BYTE.search(cxx_t):
            return HeldAs.BYTE
        #
        # Must check for FLOAT before INTEGER in case of "long double" etc.
        #
        if HeldAs.RE_FLOAT.search(cxx_t):
            return HeldAs.FLOAT
        if HeldAs.RE_INTEGER.search(cxx_t):
            return HeldAs.INTEGER
        return HeldAs.OBJECT

    def declare_type_helpers(self, name, error, need_string=False, need_cxx_t=True):
        """
        Make it easier to track changes in generated output.

        By creating local definitions at the top of each section of emitted output, the rest of the expanded template
        is a constant. This makes it easier to see the effect of any changes using "diff".
        """
        code = ""
        if self.is_mapped_type or need_string:
            code += """    const char *cxx{name}S = "{cxx_t}";
"""
        if need_cxx_t:
            code += """    typedef {cxx_t} Cxx{name}T;
"""
        if self.category in [HeldAs.POINTER, HeldAs.OBJECT]:
            #
            # If the sipTypeDef needs a run-time lookup using sipFindMappedType, can convert that into a one-off cost
            # using a static.
            #
            if self.is_mapped_type:
                code += """    static const sipTypeDef *gen{name}T = NULL;
    if (gen{name}T == NULL) {
        gen{name}T = {sip_t};
        if (gen{name}T == NULL) {
            PyErr_Format(PyExc_TypeError, "cannot find SIP type for '%s'", cxx{name}S);
            {error}
        }
    }
"""
            elif self.sip_t in [HeldAs.BYTE, HeldAs.INTEGER, HeldAs.FLOAT]:
                #
                # Primitive types don't need help from a sipType_xxx.
                #
                pass
            else:
                code += """    const sipTypeDef *gen{name}T = {sip_t};
"""
        code = code.replace("{sip_t}", self.sip_t)
        code = code.replace("{name}", name)
        code = code.replace("{error}", error)
        code = code.replace("{cxx_t}", self.cxx_t)
        return code

    def cxx_to_py(self, name, needs_reference, cxx_i, cxx_po=None):
        code = self.cxx_to_py_template()
        code = code.replace("{name}", name)
        code = code.replace("{cxx_i}", cxx_i)
        code = code.replace("{cxx_po}", cxx_po if cxx_po else cxx_i)
        code = code.replace("{transfer}", "sipTransferObj" if needs_reference else "NULL")
        return code

    def py_to_cxx(self, name, needs_reference, py_v):
        code = self.py_to_cxx_template()
        code = code.replace("{name}", name)
        code = code.replace("{py_v}", py_v)
        code = code.replace("{transfer}", "sipTransferObj" if needs_reference else "NULL")
        return code
