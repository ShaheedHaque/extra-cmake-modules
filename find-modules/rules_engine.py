#!/usr/bin/env python
#
# Copyright 2016 by Shaheed Haque (srhaque@theiet.org)
# Copyright 2016 Stephen Kelly <steveire@gmail.com>
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

"""SIP file generation rules engine."""

from __future__ import print_function
from abc import ABCMeta, abstractmethod
import argparse
import gettext
import inspect
import logging
import os
import re
import sys
import textwrap
import traceback
from copy import deepcopy

from clang.cindex import CursorKind

class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


logger = logging.getLogger(__name__)
gettext.install(__name__)
_SEPARATOR = "\x00"

# Keep PyCharm happy.
_ = _


def _parents(container):
    parents = []
    parent = container.semantic_parent
    while parent and parent.kind != CursorKind.TRANSLATION_UNIT:
        parents.append(parent.spelling)
        parent = parent.semantic_parent
    if parents:
        parents = "::".join(reversed(parents))
    else:
        parents = os.path.basename(container.translation_unit.spelling)
    return parents


_mapped_type_re = re.compile("^%(ConvertToTypeCode|ConvertFromTypeCode)", re.MULTILINE)


def handle_mapped_types(cursor, sip):
    #
    # Is the resulting code a %MappedType? TODO: Handle combinations of mapped and non-mapped code.
    #
    mapped_type = _mapped_type_re.search(sip["code"])
    if mapped_type:
        name = "{}:{}[{}]".format(cursor.spelling, os.path.basename(cursor.extent.start.file.name),
                                  cursor.extent.start.line)
        sip["module_code"][name] = "%MappedType " + sip["decl"] + "\n{" + sip["code"] + "};\n"
        sip["code"] = ""


class Rule(object):
    def __init__(self, rule_name, fn, pattern_zip):
        self.name =  "{},{}".format(rule_name, fn.__name__)
        self.fn = fn
        self.usage = 0
        try:
            groups = ["(?P<{}>{})".format(name, pattern) for pattern, name in pattern_zip]
            groups = _SEPARATOR.join(groups)
            #
            # We'll use re.match to anchor the start of the match, and so need a $ to anchor the end.
            #
            self.matcher = re.compile(groups + "$")
        except Exception as e:
            groups = ["{} '{}'".format(name, pattern) for pattern, name in pattern_zip]
            groups = ", ".join(groups)
            raise RuntimeError(_("Bad {}: {}: {}").format(self, groups, e))

    def match(self, candidate):
        return self.matcher.match(candidate)

    def trace_result(self, parents, item, original, modified):
        """
        Record any modification both in the log and the returned result. If a rule fired, but
        caused no modification, that is logged.

        :return: Modifying rule or None.
        """
        fqn = parents + "::" + original["name"] + "[" + str(item.extent.start.line) + "]"
        return self._trace_result(fqn, original, modified)

    def _trace_result(self, fqn, original, modified):
        """
        Record any modification both in the log and the returned result. If a rule fired, but
        caused no modification, that is logged.

        :return: Modifying rule or None.
        """
        if not modified["name"]:
            logger.debug(_("Rule {} suppressed {}, {}").format(self, fqn, original))
        else:
            delta = False
            for k, v in original.iteritems():
                if v != modified[k]:
                    delta = True
                    break
            if delta:
                logger.debug(_("Rule {} modified {}, {}->{}").format(self, fqn, original, modified))
            else:
                if self.fn is not noop:
                    logger.warn(_("Rule {} did not modify {}, {}").format(self, fqn, original))
                return None
        return self

    def __str__(self):
        return self.name


class AbstractCompiledRuleDb(object):
    __metaclass__ = ABCMeta

    def __init__(self, raw_rules, parameter_names):
        """
        Create a database of compiled rules.

        :param raw_rules:   A function which returns an ordered list of raw rules. The point of
                            using a function is that a function has a name which can be used for
                            diagnostics.
        :parameter_names:   The name of each field in the raw rules.
        """
        self.compiled_rules = []
        self.parameter_names = parameter_names
        self.candidate_formatter = _SEPARATOR.join(["{}"] * len(parameter_names))
        #
        # Backwards compatibility.
        #
        # TODO: Remove when Steve and Shaheed are agreed/ready.
        #
        if not callable(raw_rules):
            tmp = lambda: raw_rules
            self.add_rules(tmp)
        else:
            self.add_rules(raw_rules)

    def _match(self, *args):
        candidate = self.candidate_formatter.format(*args)
        for rule in self.compiled_rules:
            matcher = rule.match(candidate)
            if matcher:
                #
                # Only use the first matching rule.
                #
                rule.usage += 1
                return matcher, rule
        return None, None

    def add_rules(self, raw_rules):
        """
        Add to the existing set of rules. The new rules have precedence over existing rules.

        :param raw_rules:   A function which returns an ordered list of raw rules. The point of
                            using a function is that a function has a name which can be used for
                            diagnostics. May be None.
        """
        if raw_rules is None or raw_rules() is None:
            return
        file_ = inspect.getfile(raw_rules)
        if file_ in [__file__, __file__[:-1]]:
            #
            # We must have come through the backwards compatibility in __init__.
            #
            # TODO: Remove when Steve and Shaheed are agreed/ready.
            #
            file_ = inspect.stack()[4][1]
            name_ = str(inspect.stack()[4][2])
        else:
            name_ = raw_rules.__name__
        file_ = os.path.basename(file_)
        tmp = []
        for i, raw_rule in enumerate(raw_rules()):
            #
            # Derive a useful name for diagnostic purposes.
            #
            rule_name = "{}:{}[{}]".format(file_, name_, i)
            #
            # Backwards compatibility. Older rule databases will be missing entries for (fn_result, decl) and
            # (prefix, suffix) for TypedefRuleDb and FunctionRuleDb respectively.
            #
            # TODO: Remove when Steve and Shaheed are agreed/ready.
            #
            if len(raw_rule) == len(self.parameter_names) - 1 and isinstance(self, (TypedefRuleDb, FunctionRuleDb)):
                raw_rule = raw_rule[:-1] + [".*", ".*"] + [raw_rule[-1]]
            if len(raw_rule) != len(self.parameter_names) + 1:
                raise RuntimeError(_("Bad raw rule {}: {}: {}").format(rule_name, raw_rule, self.parameter_names))
            z = zip(raw_rule[:-1], self.parameter_names)
            tmp.append(Rule(rule_name, raw_rule[-1], z))
        self.compiled_rules = tmp + self.compiled_rules

    @abstractmethod
    def apply(self, *args):
        raise NotImplemented(_("Missing subclass"))

    def dump_usage(self, fn):
        """ Dump the usage counts."""
        for rule in self.compiled_rules:
            fn(str(rule), rule.usage)


class ContainerRuleDb(AbstractCompiledRuleDb):
    """
    THE RULES FOR CONTAINERS.

    These are used to customise the behaviour of the SIP generator by allowing
    the declaration for any container (class, namespace, struct, union) to be
    customised, for example to add SIP compiler annotations.

    Each entry in the raw rule database must be a list with members as follows:

        0. A regular expression which matches the fully-qualified name of the
        "container" enclosing the container.

        1. A regular expression which matches the container name.

        2. A regular expression which matches any template parameters.

        3. A regular expression which matches the container declaration.

        4. A regular expression which matches any base specifiers.

        5. A function.

    In use, the database is walked in order from the first entry. If the regular
    expressions are matched, the function is called, and no further entries are
    walked. The function is called with the following contract:

        def container_xxx(container, sip, matcher):
            '''
            Return a modified declaration for the given container.

            :param container:   The clang.cindex.Cursor for the container.
            :param sip:         A dict with the following keys:

                                    name                The name of the container.
                                    template_parameters Any template parameters.
                                    decl                The declaration.
                                    base_specifiers     Any base specifiers.
                                    body                The body, less the outer
                                                        pair of braces.
                                    annotations         Any SIP annotations.

            :param matcher:         The re.Match object. This contains named
                                    groups corresponding to the key names above
                                    EXCEPT body and annotations.

            :return: An updated set of sip.xxx values. Setting sip.name to the
                     empty string will cause the container to be suppressed.
            '''

    :return: The compiled form of the rules.
    """
    def __init__(self, db):
        super(ContainerRuleDb, self).__init__(db, ["parents", "container", "template_parameters", "decl", "base_specifiers"])

    def apply(self, container, sip):
        """
        Walk over the rules database for containers, applying the first matching transformation.

        :param container:           The clang.cindex.Cursor for the container.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        parents = _parents(container)
        matcher, rule = self._match(parents, sip["name"],
                                    ", ".join(sip["template_parameters"]),
                                    sip["decl"],
                                    ", ".join(sip["base_specifiers"]))
        sip.setdefault("code", "")
        sip.setdefault("module_code", {})
        if matcher:
            before = deepcopy(sip)
            rule.fn(container, sip, matcher)
            return rule.trace_result(parents, container, before, sip)
        return None


class ForwardDeclarationRuleDb(AbstractCompiledRuleDb):
    """
    THE RULES FOR FORWARD DECLARATIONS.

    These are used to customise the behaviour of the SIP generator by allowing
    the forward declaration for any container (class, struct, union) to be
    customised, for example to add SIP compiler annotations.

    Each entry in the raw rule database must be a list with members as follows:

        0. A regular expression which matches the fully-qualified name of the
        "container" enclosing the container.

        1. A regular expression which matches the container name.

        2. A regular expression which matches any template parameters.

        3. A function.

    In use, the database is walked in order from the first entry. If the regular
    expressions are matched, the function is called, and no further entries are
    walked. The function is called with the following contract:

        def declaration_xxx(container, sip, matcher):
            '''
            Return a modified declaration for the given container.

            :param container:   The clang.cindex.Cursor for the container.
            :param sip:         A dict with the following keys:

                                    name                The name of the container.
                                    template_parameters Any template parameters.
                                    annotations         Any SIP annotations.

            :param matcher:         The re.Match object. This contains named
                                    groups corresponding to the key names above
                                    EXCEPT body and annotations.

            :return: An updated set of sip.xxx values. Setting sip.name to the
                     empty string will cause the container to be suppressed.
            '''

    :return: The compiled form of the rules.
    """
    def __init__(self, db):
        super(ForwardDeclarationRuleDb, self).__init__(db, ["parents", "container", "template_parameters"])

    def apply(self, container, sip):
        """
        Walk over the rules database for containers, applying the first matching transformation.

        :param container:           The clang.cindex.Cursor for the container.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        parents = _parents(container)
        matcher, rule = self._match(parents, sip["name"],
                                    ", ".join(sip["template_parameters"]))
        sip.setdefault("code", "")
        sip.setdefault("module_code", {})
        if matcher:
            before = deepcopy(sip)
            rule.fn(container, sip, matcher)
            handle_mapped_types(container, sip)
            return rule.trace_result(parents, container, before, sip)
        return None


class FunctionRuleDb(AbstractCompiledRuleDb):
    """
    THE RULES FOR FUNCTIONS.

    These are used to customise the behaviour of the SIP generator by allowing
    the declaration for any function to be customised, for example to add SIP
    compiler annotations.

    Each entry in the raw rule database must be a list with members as follows:

        0. A regular expression which matches the fully-qualified name of the
        "container" enclosing the function.

        1. A regular expression which matches the function name.

        2. A regular expression which matches any template parameters.

        3. A regular expression which matches the function result.

        4. A regular expression which matches the function parameters (e.g.
        "int a, void *b" for "int foo(int a, void *b)").

        5. A function.

    In use, the database is walked in order from the first entry. If the regular
    expressions are matched, the function is called, and no further entries are
    walked. The function is called with the following contract:

        def function_xxx(container, function, sip, matcher):
            '''
            Return a modified declaration for the given function.

            :param container:   The clang.cindex.Cursor for the container.
            :param function:    The clang.cindex.Cursor for the function.
            :param sip:         A dict with the following keys:

                                    name                The name of the function.
                                    template_parameters Any template parameters.
                                    fn_result           Result, if not a constructor.
                                    parameters          The parameters.
                                    prefix              Leading keyworks ("static"). Separated by space,
                                                        ends with a space.
                                    suffix              Trailing keywords ("const"). Separated by space, starts with
                                                        space.
                                    annotations         Any SIP annotations.

            :param matcher:         The re.Match object. This contains named
                                    groups corresponding to the key names above
                                    EXCEPT annotations.

            :return: An updated set of sip.xxx values. Setting sip.name to the
                     empty string will cause the container to be suppressed.
            '''

    :return: The compiled form of the rules.
    """
    def __init__(self, db):
        super(FunctionRuleDb, self).__init__(db, ["container", "function", "template_parameters", "fn_result",
                                                  "parameters", "prefix", "suffix"])

    def apply(self, container, function, sip):
        """
        Walk over the rules database for functions, applying the first matching transformation.

        :param container:           The clang.cindex.Cursor for the container.
        :param function:            The clang.cindex.Cursor for the function.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        parents = _parents(function)
        matcher, rule = self._match(parents, sip["name"], ", ".join(sip["template_parameters"]), sip["fn_result"],
                                    ", ".join(sip["parameters"]), sip["prefix"], sip["suffix"])
        sip.setdefault("code", "")
        sip.setdefault("module_code", {})
        if matcher:
            before = deepcopy(sip)
            rule.fn(container, function, sip, matcher)
            handle_mapped_types(function, sip)
            return rule.trace_result(parents, function, before, sip)
        return None


class ParameterRuleDb(AbstractCompiledRuleDb):
    """
    THE RULES FOR FUNCTION PARAMETERS.

    These are used to customise the behaviour of the SIP generator by allowing
    the declaration for any parameter in any function to be customised, for
    example to add SIP compiler annotations.

    Each entry in the raw rule database must be a list with members as follows:

        0. A regular expression which matches the fully-qualified name of the
        "container" enclosing the function enclosing the parameter.

        1. A regular expression which matches the function name enclosing the
        parameter.

        2. A regular expression which matches the parameter name.

        3. A regular expression which matches the parameter declaration (e.g.
        "int foo").

        4. A regular expression which matches the parameter initialiser (e.g.
        "Xyz:MYCONST + 42").

        5. A function.

    In use, the database is walked in order from the first entry. If the regular
    expressions are matched, the function is called, and no further entries are
    walked. The function is called with the following contract:

        def parameter_xxx(container, function, parameter, sip, init, matcher):
            '''
            Return a modified declaration and initialiser for the given parameter.

            :param container:   The clang.cindex.Cursor for the container.
            :param function:    The clang.cindex.Cursor for the function.
            :param parameter:   The clang.cindex.Cursor for the parameter.
            :param sip:         A dict with the following keys:

                                    name                The name of the function.
                                    decl                The declaration.
                                    init                Any initialiser.
                                    annotations         Any SIP annotations.

            :param matcher:         The re.Match object. This contains named
                                    groups corresponding to the key names above
                                    EXCEPT annotations.

            :return: An updated set of sip.xxx values.
        '''

    :return: The compiled form of the rules.
    """
    def __init__(self, db):
        super(ParameterRuleDb, self).__init__(db, ["container", "function", "parameter", "decl", "init"])

    def apply(self, container, function, parameter, sip):
        """
        Walk over the rules database for parameters, applying the first matching transformation.

        :param container:           The clang.cindex.Cursor for the container.
        :param function:            The clang.cindex.Cursor for the function.
        :param parameter:           The clang.cindex.Cursor for the parameter.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        parents = _parents(function)
        matcher, rule = self._match(parents, function.spelling, sip["name"], sip["decl"], sip["init"])
        sip.setdefault("code", "")
        sip.setdefault("module_code", {})
        if matcher:
            before = deepcopy(sip)
            rule.fn(container, function, parameter, sip, matcher)
            handle_mapped_types(parameter, sip)
            return rule.trace_result(parents, parameter, before, sip)
        return None


class TypedefRuleDb(AbstractCompiledRuleDb):
    """
    THE RULES FOR TYPEDEFS.

    These are used to customise the behaviour of the SIP generator by allowing
    the declaration for any typedef to be customised, for example to add SIP
    compiler annotations.

    Each entry in the raw rule database must be a list with members as follows:

        0. A regular expression which matches the fully-qualified name of the
        "container" enclosing the typedef.

        1. A regular expression which matches the typedef name.

        2. A regular expression which matches the function result for a function
        pointer typedef.

        3. A regular expression which matches the typedef declaration (e.g.
        "typedef int foo").

        4. A function.

    In use, the database is walked in order from the first entry. If the regular
    expressions are matched, the function is called, and no further entries are
    walked. The function is called with the following contract:

        def typedef_xxx(container, typedef, sip, matcher):
            '''
            Return a modified declaration for the given function.

            :param container:   The clang.cindex.Cursor for the container.
            :param typedef:     The clang.cindex.Cursor for the typedef.
            :param sip:         A dict with the following keys:

                                    name                The name of the typedef.
                                    fn_result           Result, for a function pointer.
                                    decl                The declaration.
                                    annotations         Any SIP annotations.

            :param matcher:         The re.Match object. This contains named
                                    groups corresponding to the key names above
                                    EXCEPT annotations.

            :return: An updated set of sip.xxx values. Setting sip.name to the
                     empty string will cause the container to be suppressed.
            '''

    :return: The compiled form of the rules.
    """
    def __init__(self, db):
        super(TypedefRuleDb, self).__init__(db, ["container", "typedef", "fn_result", "decl"])

    def apply(self, container, typedef, sip):
        """
        Walk over the rules database for typedefs, applying the first matching transformation.

        :param container:           The clang.cindex.Cursor for the container.
        :param typedef:             The clang.cindex.Cursor for the typedef.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        parents = _parents(typedef)
        matcher, rule = self._match(parents, sip["name"], sip["fn_result"], sip["decl"])
        sip.setdefault("code", "")
        sip.setdefault("module_code", {})
        if matcher:
            before = deepcopy(sip)
            rule.fn(container, typedef, sip, matcher)
            handle_mapped_types(typedef, sip)
            return rule.trace_result(parents, typedef, before, sip)
        return None


class UnexposedRuleDb(AbstractCompiledRuleDb):
    """
    THE RULES FOR UNEXPOSED ITEMS.

    These are used to customise the behaviour of the SIP generator by allowing
    the declaration for any unexposed item to be customised, for example to
    add SIP compiler annotations.

    Each entry in the raw rule database must be a list with members as follows:

        0. A regular expression which matches the fully-qualified name of the
        "container" enclosing the unexposed item.

        1. A regular expression which matches the unexposed item name.

        2. A regular expression which matches the unexposed item declaration.

        3. A function.

    In use, the database is walked in order from the first entry. If the regular
    expressions are matched, the function is called, and no further entries are
    walked. The function is called with the following contract:

        def unexposed_xxx(container, unexposed, sip, matcher):
            '''
            Return a modified declaration for the given container.

            :param container:   The clang.cindex.Cursor for the container.
            :param unexposed:   The clang.cindex.Cursor for the unexposed item.
            :param sip:         A dict with the following keys:

                                    name                The name of the unexposed item.
                                    decl                The declaration.
                                    annotations         Any SIP annotations.

            :param matcher:         The re.Match object. This contains named
                                    groups corresponding to the key names above
                                    EXCEPT annotations.

            :return: An updated set of sip.xxx values. Setting sip.name to the
                     empty string will cause the unexposed item to be suppressed.
            '''

    :return: The compiled form of the rules.
    """
    def __init__(self, db):
        super(UnexposedRuleDb, self).__init__(db, ["container", "unexposed", "decl"])

    def apply(self, container, unexposed, sip):
        """
        Walk over the rules database for unexposed items, applying the first matching transformation.

        :param container:           The clang.cindex.Cursor for the container.
        :param unexposed:           The clang.cindex.Cursor for the unexposed item.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        parents = _parents(unexposed)
        matcher, rule = self._match(parents, sip["name"], sip["decl"])
        sip.setdefault("code", "")
        sip.setdefault("module_code", {})
        if matcher:
            before = deepcopy(sip)
            rule.fn(container, unexposed, sip, matcher)
            handle_mapped_types(unexposed, sip)
            return rule.trace_result(parents, unexposed, before, sip)
        return None


class VariableRuleDb(AbstractCompiledRuleDb):
    """
    THE RULES FOR VARIABLES.

    These are used to customise the behaviour of the SIP generator by allowing
    the declaration for any variable to be customised, for example to add SIP
    compiler annotations.

    Each entry in the raw rule database must be a list with members as follows:

        0. A regular expression which matches the fully-qualified name of the
        "container" enclosing the variable.

        1. A regular expression which matches the variable name.

        2. A regular expression which matches the variable declaration (e.g.
        "int foo").

        3. A function.

    In use, the database is walked in order from the first entry. If the regular
    expressions are matched, the function is called, and no further entries are
    walked. The function is called with the following contract:

        def variable_xxx(container, variable, sip, matcher):
            '''
            Return a modified declaration for the given variable.

            :param container:   The clang.cindex.Cursor for the container.
            :param variable:    The clang.cindex.Cursor for the variable.
            :param sip:         A dict with the following keys:

                                    name                The name of the variable.
                                    decl                The declaration.
                                    annotations         Any SIP annotations.

            :param matcher:         The re.Match object. This contains named
                                    groups corresponding to the key names above
                                    EXCEPT annotations.

            :return: An updated set of sip.xxx values. Setting sip.name to the
                     empty string will cause the container to be suppressed.
            '''

    :return: The compiled form of the rules.
    """
    def __init__(self, db):
        super(VariableRuleDb, self).__init__(db, ["container", "variable", "decl"])

    def apply(self, container, variable, sip):
        """
        Walk over the rules database for variables, applying the first matching transformation.

        :param container:           The clang.cindex.Cursor for the container.
        :param variable:            The clang.cindex.Cursor for the variable.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        parents = _parents(variable)
        matcher, rule = self._match(parents, sip["name"], sip["decl"])
        sip.setdefault("code", "")
        sip.setdefault("module_code", {})
        if matcher:
            before = deepcopy(sip)
            rule.fn(container, variable, sip, matcher)
            handle_mapped_types(variable, sip)
            return rule.trace_result(parents, variable, before, sip)
        return None


class AbstractCompiledCodeDb(object):
    __metaclass__ = ABCMeta

    def __init__(self, raw_rules):
        """
        Create a database of compiled rules.

        :param raw_rules:   A dict of raw rules, or a function which returns a dict of raw rules.
                            The point of using a function is that a function has a name which can
                            be used for diagnostics.
        """
        self.compiled_rules = {}
        self.names = []
        #
        # Backwards compatibility.
        #
        # TODO: Remove when Steve and Shaheed are agreed/ready.
        #
        if not callable(raw_rules):
            tmp = lambda: raw_rules
            self.add_rules(tmp)
        else:
            self.add_rules(raw_rules)

    def add_rules(self, raw_rules):
        """
        Add to the existing set of rules. The new rules have precedence over existing rules.

        :param raw_rules:   A function which returns a dict of raw rules. The point of using a
                            function is that a function has a name which can be used for
                            diagnostics. May be None.
        """
        if raw_rules is None or raw_rules() is None:
            return
        file_ = inspect.getfile(raw_rules)
        if file_ in [__file__, __file__[:-1]]:
            #
            # We must have come through the backwards compatibility in __init__.
            #
            # TODO: Remove when Steve and Shaheed are agreed/ready.
            #
            file_ = inspect.stack()[4][1]
            name_ = str(inspect.stack()[4][2])
        else:
            name_ = raw_rules.__name__
        file_ = os.path.basename(file_)
        #
        # Derive a useful name for diagnostic purposes.
        #
        self.names.append("{}:{}".format(file_, name_))
        for k, v in raw_rules().items():
            if k in self.compiled_rules:
                logger.debug(_("Updating raw rule {}").format(k))
            self.compiled_rules[k] = v

    @abstractmethod
    def apply(self, function, sip):
        raise NotImplemented(_("Missing subclass"))

    def trace_result(self, rule, parents, item, original, modified):
        """
        Record any modification both in the log and the returned result. If a rule fired, but
        caused no modification, that is logged.

        :return: Modifying rule or None.
        """
        fqn = parents + "::" + original["name"] + "[" + str(item.extent.start.line) + "]"
        return self._trace_result(rule, fqn, original, modified)

    def _trace_result(self, rule, fqn, original, modified):
        """
        Record any modification both in the log and the returned result. If a rule fired, but
        caused no modification, that is logged.

        :return: Modifying rule or None.
        """
        ruleset = self.names[rule["ruleset"]]
        if not modified["name"]:
            logger.debug(_("Rule {} discarded {}, {}").format(ruleset, fqn, original))
        else:
            delta = False
            for k, v in original.iteritems():
                if v != modified[k]:
                    delta = True
                    break
            if delta:
                logger.debug(_("Rule {} modified {}, {}->{}").format(ruleset, fqn, original, modified))
            else:
                logger.warn(_("Rule {} did not modify {}, {}").format(ruleset, fqn, original))
                return None
        return ruleset

    @abstractmethod
    def dump_usage(self, fn):
        raise NotImplemented(_("Missing subclass"))


class MethodCodeDb(AbstractCompiledCodeDb):
    """
    THE RULES FOR INJECTING METHOD-RELATED CODE (such as %MethodCode, 
    %VirtualCatcherCode, %VirtualCallCode and other method-level directives).

    These are used to customise the behaviour of the SIP generator by allowing
    method-level code injection.

    The raw rule database must be an outer dictionary as follows:

        0. Each key is the fully-qualified name of a "container" enclosing
        methods.

        1. Each value is an inner dictionary, each of whose keys is the name
        of a method.

    Each inner dictionary has entries which update the declaration as follows:

        "name":         Optional string. If present, overrides the name of the
                        method.
        "parameters":   Optional string. If present, update the argument list.

        "fn_result":    Optional string. If present, update the return type.

        "cxx_decl", "cxx_fn_result"
                        Both optional. If either is present, the SIP method's
                        optional C++ declaration is added (if only one is
                        present, "cxx_decl" is defaulted from "parameters" and
                        "cxx_fn_result" is defaulted from "fn_result").

        "code":         Required. Either a string, with the %XXXCode content,
                        or a callable.

    In use, the database is directly indexed by "container" and then method
    name. If "code" entry is a string, then the other optional keys are
    interpreted as above. If "code" is a callable, it is called with the
    following contract:

        def methodcode_xxx(function, sip, entry):
            '''
            Return a modified declaration for the given function.

            :param function:    The clang.cindex.Cursor for the function.
            :param sip:         A dict with keys as for function rules
                                plus the "cxx_decl", "cxx_fn_result" and (string)
                                "code" keys described above.
            :param entry:       The inner dictionary entry.

            :return: An updated set of sip.xxx values.
            '''

    :return: The compiled form of the rules.
    """
    __metaclass__ = ABCMeta

    def __init__(self, raw_rules):
        super(MethodCodeDb, self).__init__(raw_rules)

    def add_rules(self, raw_rules):
        if raw_rules is None or raw_rules() is None:
            return
        super(MethodCodeDb, self).add_rules(raw_rules)
        #
        # Add a usage count and other diagnostic support for each item in the database.
        #
        ruleset = len(self.names) - 1
        for k, v in raw_rules().items():
            for l in v.keys():
                self.compiled_rules[k][l]["usage"] = 0
                self.compiled_rules[k][l]["ruleset"] = ruleset

    def _get(self, item, name):
        #
        # Lookup any parent-level entries.
        #
        parents = _parents(item)
        entries = self.compiled_rules.get(parents, None)
        if not entries:
            return None
        #
        # Now look for an actual hit.
        #
        entry = entries.get(name, None)
        if not entry:
            return None
        entry["usage"] += 1
        return entry

    def apply(self, function, sip):
        """
        Walk over the code database for functions, applying the first matching transformation.

        :param function:            The clang.cindex.Cursor for the function.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        entry = self._get(function, sip["name"])
        #
        # SIP supports the notion of a second C++ signature as well as the normal signature. By default, this
        # is not present.
        #
        sip.setdefault("cxx_decl", "")
        sip.setdefault("cxx_fn_result", "")
        sip.setdefault("code", "")
        sip.setdefault("module_code", {})
        if entry:
            before = deepcopy(sip)
            if callable(entry["code"]):
                fn = entry["code"]
                fn_file = os.path.basename(inspect.getfile(fn))
                trace = "// Generated for '{}:{}' (by {},{}:{}):\n".format(_parents(function), function.spelling, self.names[entry["ruleset"]], fn_file, fn.__name__)
                fn(function, sip, entry)
            else:
                trace = "// Inserted for '{}:{}' (by {}):\n".format(_parents(function), function.spelling, self.names[entry["ruleset"]])
                sip["name"] = entry.get("name", sip["name"])
                sip["code"] = entry["code"]
                sip["parameters"] = entry.get("parameters", sip["parameters"])
                sip["fn_result"] = entry.get("fn_result", sip["fn_result"])
                #
                # The user might provide one or other or both of cxx_decl and cxx_fn_result to signify a C++ signature. If
                # needed, default a missing value from decl/fn_result.
                #
                if "cxx_decl" in entry or "cxx_fn_result" in entry:
                    sip["cxx_decl"] = entry.get("cxx_decl", sip["parameters"])
                    sip["cxx_fn_result"] = entry.get("cxx_fn_result", sip["cxx_fn_result"])
            #
            # Fetch/format the code.
            #
            sip["code"] = textwrap.dedent(sip["code"]).strip() + "\n"
            sip["code"] = trace + sip["code"]
            handle_mapped_types(function, sip)
            return self.trace_result(entry, _parents(function), function, before, sip)
        return None

    def dump_usage(self, fn):
        """ Dump the usage counts."""
        for k in sorted(self.compiled_rules.keys()):
            vk = self.compiled_rules[k]
            for l in sorted(vk.keys()):
                vl = vk[l]
                fn(self.names[vl["ruleset"]] + " for " + k + "," + l, vl["usage"])


class TypeCodeDb(AbstractCompiledCodeDb):
    """
    THE RULES FOR INJECTING TYPE-RELATED CODE (such as %BIGetBufferCode,
    %BIGetReadBufferCode, %BIGetWriteBufferCode, %BIGetSegCountCode,
    %BIGetCharBufferCode, %BIReleaseBufferCode, %ConvertFromTypeCode,
    %ConvertToSubClassCode, %ConvertToTypeCode, %GCClearCode, %GCTraverseCode,
    %InstanceCode, %PickleCode, %TypeCode, %TypeHeaderCode or other type-level
    directives).

    These are used to customise the behaviour of the SIP generator by allowing
    type-level code injection.

    The raw rule database must be a dictionary as follows:

        0. Each key is the fully-qualified name of a "container" class,
        struct, namespace etc.

        1. Each value has entries which update the declaration as follows:

        "name":         Optional string. If present, overrides the name of the
                        typedef as the name of the %MappedType. Useful for
                        adding %MappedType entries for parameters where there
                        is no explicit typedef.
        "code":         Required. Either a string, with the %XXXCode content,
                        or a callable.

    In use, the database is directly indexed by "container". If "code" entry
    is a string, it is used directly. Note that the use of any of
    %TypeHeaderCode, %ConvertToTypeCode or %ConvertFromTypeCode will cause the
    container type to be marked as a %MappedType. If "code" is a callable,
    it is called with the following contract:

        def typecode_xxx(container, sip, entry):
            '''
            Return a modified declaration for the given function.

            :param container:   The clang.cindex.Cursor for the container.
            :param sip:         A dict with keys as for container rules
                                plus the "code" key described above.
            :param entry:       The dictionary entry.

            :return: An updated set of sip.xxx values.
            '''

    :return: The compiled form of the rules.
    """
    __metaclass__ = ABCMeta

    def __init__(self, raw_rules):
        super(TypeCodeDb, self).__init__(raw_rules)

    def add_rules(self, raw_rules):
        if raw_rules is None or raw_rules() is None:
            return
        super(TypeCodeDb, self).add_rules(raw_rules)
        #
        # Add a usage count and other diagnostic support for each item in the database.
        #
        ruleset = len(self.names) - 1
        for k, v in raw_rules().items():
            self.compiled_rules[k]["usage"] = 0
            self.compiled_rules[k]["ruleset"] = ruleset

    def _get(self, item, name):
        #
        # Lookup for an actual hit.
        #
        parents = _parents(item)
        entry = self.compiled_rules.get(parents + "::" + name, None)
        if not entry:
            return None
        entry["usage"] += 1
        return entry

    def apply(self, container, sip):
        """
        Walk over the code database for containers, applying the first matching transformation.

        :param container:           The clang.cindex.Cursor for the container.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        entry = self._get(container, sip["name"])
        sip.setdefault("code", "")
        sip.setdefault("module_code", {})
        if entry:
            before = deepcopy(sip)
            if callable(entry["code"]):
                fn = entry["code"]
                fn_file = os.path.basename(inspect.getfile(fn))
                trace = "// Generated for '{}' (by {},{}:{}):\n".format(container.spelling, self.names[entry["ruleset"]], fn_file, fn.__name__)
                fn(container, sip, entry)
            else:
                trace = "// Inserted for '{}' (by {}):\n".format(container.spelling, self.names[entry["ruleset"]])
                sip["name"] = entry.get("name", sip["name"])
                sip["code"] = entry["code"]
                sip["decl"] = entry.get("decl", sip["decl"])
            #
            # Fetch/format the code.
            #
            sip["code"] = textwrap.dedent(sip["code"]).strip() + "\n"
            sip["code"] = trace + sip["code"]
            handle_mapped_types(container, sip)
            return self.trace_result(entry, _parents(container), container, before, sip)
        return None

    def dump_usage(self, fn):
        """ Dump the usage counts."""
        for k in sorted(self.compiled_rules.keys()):
            v = self.compiled_rules[k]
            fn(self.names[v["ruleset"]] + " for " + k, v["usage"])


class ModuleCodeDb(AbstractCompiledCodeDb):
    """
    THE RULES FOR INJECTING MODULE-RELATED CODE (such as %ExportedHeaderCode,
    %ModuleCode, %ModuleHeaderCode or other module-level directives).

    These are used to customise the behaviour of the SIP generator by allowing
    module-level code injection.

    The raw rule database must be a dictionary as follows:

        0. Each key is the basename of a header file.

        1. Each value has entries which update the declaration as follows:

        "code":         Required. Either a string, with the %XXXCode content,
                        or a callable.

    If "code" is a callable, it is called with the following contract:

        def module_xxx(filename, sip, entry):
            '''
            Return a string to insert for the file.

            :param filename:    The filename.
            :param sip:         A dict with the key "name" for the filename,
                                "decl" for the module body plus the "code" key
                                described above.
            :param entry:       The dictionary entry.

            :return: A string.
            '''

    :return: The compiled form of the rules.
    """
    __metaclass__ = ABCMeta

    def __init__(self, raw_rules):
        super(ModuleCodeDb, self).__init__(raw_rules)

    def add_rules(self, raw_rules):
        if raw_rules is None or raw_rules() is None:
            return
        super(ModuleCodeDb, self).add_rules(raw_rules)
        #
        # Add a usage count and other diagnostic support for each item in the database.
        #
        ruleset = len(self.names) - 1
        for k, v in raw_rules().items():
            self.compiled_rules[k]["usage"] = 0
            self.compiled_rules[k]["ruleset"] = ruleset

    def _get(self, filename):
        #
        # Lookup for an actual hit.
        #
        entry = self.compiled_rules.get(filename, None)
        if not entry:
            return None
        entry["usage"] += 1
        return entry

    def apply(self, filename, sip):
        """
        Walk over the code database for modules, applying the first matching transformation.

        :param filename:            The file for the module.
        :param sip:                 The SIP dict (may be modified on return).
        :return:                    Modifying rule or None (even if a rule matched, it may not modify things).
        """
        entry = self._get(filename)
        sip.setdefault("code", "")
        if entry:
            before = deepcopy(sip)
            if callable(entry["code"]):
                fn = entry["code"]
                fn_file = os.path.basename(inspect.getfile(fn))
                trace = "// Generated for '{}' (by {},{}:{}):\n".format(filename, self.names[entry["ruleset"]], fn_file, fn.__name__)
                fn(filename, sip, entry)
            else:
                trace = "// Inserted for '{}' (by {}):\n".format(filename, self.names[entry["ruleset"]])
                sip["code"] = entry["code"]
                sip["decl"] = entry.get("decl", sip["decl"])
            #
            # Fetch/format the code.
            #
            sip["code"] = textwrap.dedent(sip["code"]).strip() + "\n"
            sip["code"] = trace + sip["code"]
            fqn = filename
            return self._trace_result(entry, fqn, before, sip)
        return None

    def dump_usage(self, fn):
        """ Dump the usage counts."""
        for k in sorted(self.compiled_rules.keys()):
            v = self.compiled_rules[k]
            fn(self.names[v["ruleset"]] + " for " + k, v["usage"])


class RuleSet(object):
    """
    To implement your own binding, create a subclass of RuleSet, also called
    RuleSet in your own Python module. Your subclass will expose the raw rules
    along with other ancilliary data exposed through the subclass methods.

    You then simply run the SIP generation and SIP compilation programs passing
    in the name of your rules file
    """
    def __init__(self, container_rules=None, forward_declaration_rules=None,
                 function_rules=None, parameter_rules=None, typedef_rules=None,
                 unexposed_rules=None, variable_rules=None, methodcode=None,
                 modulecode=None, typecode=None):
        self._container_db = ContainerRuleDb(container_rules)
        self._forward_declaration_db = ForwardDeclarationRuleDb(forward_declaration_rules)
        self._fn_db = FunctionRuleDb(function_rules)
        self._param_db = ParameterRuleDb(parameter_rules)
        self._typedef_db = TypedefRuleDb(typedef_rules)
        self._unexposed_db = UnexposedRuleDb(unexposed_rules)
        self._var_db = VariableRuleDb(variable_rules)
        self._methodcode = MethodCodeDb(methodcode)
        self._modulecode = ModuleCodeDb(modulecode)
        self._typecode = TypeCodeDb(typecode)

    def add_rules(self, container_rules=None, forward_declaration_rules=None,
                  function_rules=None, parameter_rules=None, typedef_rules=None,
                  unexposed_rules=None, variable_rules=None, methodcode=None,
                  modulecode=None, typecode=None):
        self._container_db.add_rules(container_rules)
        self._forward_declaration_db.add_rules(forward_declaration_rules),
        self._fn_db.add_rules(function_rules)
        self._param_db.add_rules(parameter_rules)
        self._typedef_db.add_rules(typedef_rules)
        self._unexposed_db.add_rules(unexposed_rules)
        self._var_db.add_rules(variable_rules)
        self._methodcode.add_rules(methodcode)
        self._modulecode.add_rules(modulecode)
        self._typecode.add_rules(typecode)

    def container_rules(self):
        """
        Return a compiled list of rules for containers.

        :return: A ContainerRuleDb instance
        """
        return self._container_db

    def forward_declaration_rules(self):
        """
        Return a compiled list of rules for containers.

        :return: A ForwardDeclarationRuleDb instance
        """

        return self._forward_declaration_db

    def function_rules(self):
        """
        Return a compiled list of rules for functions.

        :return: A FunctionRuleDb instance
        """
        return self._fn_db

    def parameter_rules(self):
        """
        Return a compiled list of rules for function parameters.

        :return: A ParameterRuleDb instance
        """
        return self._param_db

    def typedef_rules(self):
        """
        Return a compiled list of rules for typedefs.

        :return: A TypedefRuleDb instance
        """
        return self._typedef_db

    def unexposed_rules(self):
        """
        Return a compiled list of rules for unexposed itesm.

        :return: An UnexposedRuleDb instance
        """
        return self._unexposed_db

    def variable_rules(self):
        """
        Return a compiled list of rules for variables.

        :return: A VariableRuleDb instance
        """
        return self._var_db

    def methodcode_rules(self):
        """
        Return a compiled list of rules for method-related code.

        :return: A MethodCodeDb instance
        """
        return self._methodcode

    def modulecode_rules(self):
        """
        Return a compiled list of rules for module-related code.

        :return: A ModuleCodeDb instance
        """
        return self._modulecode

    def typecode_rules(self):
        """
        Return a compiled list of rules for type-related code.

        :return: A TypeCodeDb instance
        """
        return self._typecode

    def methodcode(self, function, sip):
        """
        Lookup %MethodCode.
        """
        return self._methodcode.apply(function, sip)

    def modulecode(self, filename, sip):
        """
        Lookup %ModuleCode and friends.
        """
        return self._modulecode.apply(filename, sip)

    def typecode(self, container, sip):
        """
        Lookup %TypeCode and friends. Return True or False depending on whether a
        %MappedType is implied.
        """
        return self._typecode.apply(container, sip)

    def dump_unused(self, fn=None):
        """
        Usage statistics, to identify unused rules.

        :param fn:                  An optional callback which takes (rule, usage_count) arguments.
                                    By default, output will be to the logger.
        """
        def dumper(rule, usage_count):
            if usage_count:
                logger.info(_("Rule {} used {} times".format(rule, usage_count)))
            else:
                logger.warn(_("Rule {} was not used".format(rule)))

        if fn == None:
            fn = dumper
        for db in [self.container_rules(), self.forward_declaration_rules(), self.function_rules(),
                    self.parameter_rules(), self.typedef_rules(), self.unexposed_rules(), self.variable_rules(),
                    self.methodcode_rules(), self.modulecode_rules(), self.typecode_rules()]:
            db.dump_usage(fn)


#
# Some common rule actions, as a convenience for rule writers.
#
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


def discard_QSharedData_base(container, sip, matcher):
    sip["base_specifiers"].remove("QSharedData")


def mark_forward_declaration_external(container, sip, matcher):
    sip["annotations"].add("External")


def container_mark_abstract(container, sip, matcher):
    sip["annotations"].add("Abstract")


def rules(project_rules):
    """
    Constructor.

    :param project_rules:       The rules file for the project.
    """
    try:
        import imp
        imp.load_source("project_rules", project_rules)
    except ImportError:
        if sys.version_info.major == 2:
            raise
        import importlib
        spec = importlib.util.spec_from_file_location("project_rules", project_rules)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    #
    # Statically prepare the rule logic. This takes the rules provided by the user and turns them into code.
    #
    return getattr(sys.modules["project_rules"], "RuleSet")()


def main(argv=None):
    """
    Rules engine for SIP file generation.

    Examples:

        rules.py
    """
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(epilog=inspect.getdoc(main),
                                     formatter_class=HelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help=_("Enable verbose output"))
    try:
        args = parser.parse_args(argv[1:])
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        #
        # Generate help!
        #
        for db in [RuleSet, ContainerRuleDb, ForwardDeclarationRuleDb, FunctionRuleDb, ParameterRuleDb, TypedefRuleDb,
                   UnexposedRuleDb, VariableRuleDb, MethodCodeDb, ModuleCodeDb, TypeCodeDb]:
            name = db.__name__
            print(name)
            print("=" * len(name))
            print()
            print(inspect.getdoc(db))
            print()
    except Exception as e:
        tbk = traceback.format_exc()
        print(tbk)
        return -1


if __name__ == "__main__":
    sys.exit(main())
