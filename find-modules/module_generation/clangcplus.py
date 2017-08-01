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

"""A Clang-C wrapper with stronger typing and a more OO API than Clang-C."""
import gettext
import logging

import clang.cindex

logger = logging.getLogger(__name__)
gettext.install(__name__)

# Keep PyCharm happy.
_ = _
CursorKind = clang.cindex.CursorKind
TypeKind = clang.cindex.TypeKind


class MetaProxy(type):
    def __new__(mcs, name, bases, dct):
        """
        Install all proxy handlers listed as PROXIES in the class, and its base classes.
        """
        #
        # The function gives us eager bindng.
        #
        def named_property(name):
            @property
            def getter(self):
                return getattr(self.proxied_object, name)

            return getter

        #
        # The function gives us eager bindng.
        #
        def named_getter(name):
            return lambda self: getattr(self.proxied_object, name)()

        result = super(MetaProxy, mcs).__new__(mcs, name, bases, dct)
        #
        # MRO ordering provides for subclasses to override base classes.
        #
        for o in result.mro():
            proxy_type, proxy_attributes = getattr(o, "PROXIES", (None, []))
            for proxy_attribute in proxy_attributes:
                #
                #  If not present as an override in the subclass, implement the proxy.
                #
                if hasattr(result, proxy_attribute):
                    continue
                target = getattr(proxy_type, proxy_attribute)
                if isinstance(target, property):
                    setattr(result, proxy_attribute, named_property(proxy_attribute))
                else:
                    setattr(result, proxy_attribute, named_getter(proxy_attribute))
        return result


class _Proxy(object):
    __metaclass__ = MetaProxy

    def __init__(self, proxied_object):
        """
        Initialise with the default object to be proxied.
        """
        self.proxied_object = proxied_object

    def _add_proxy(self, proxied_object, proxy_attribute):
        """
        For each item in proxy_attributes, add a proxy from self to a proxied_object.
        """
        #
        #  If not present as an override in the subclass, implement the proxy.
        #
        if not hasattr(self, proxy_attribute):
            setattr(self, proxy_attribute, getattr(proxied_object, proxy_attribute))


class Diagnostic(_Proxy):
    """
    The same as a cindex.Diagnostic, but with Pythonic severity.
    """
    PROXIES = (
        clang.cindex.Diagnostic,
        #
        # All attributes except severity.
        #
        [
            "category_name", "category_number", "children", "disable_option", "fixits", "location", "option", "ranges", "spelling"
        ]
    )
    CLANG_TO_LOGGING = (logging.NOTSET, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)

    def __init__(self, diagnostic):
        super(Diagnostic, self).__init__(diagnostic)

    @property
    def severity(self):
        """
        The diagnostic levels in cindex.py are

            Ignored = 0
            Note    = 1
            Warning = 2
            Error   = 3
            Fatal   = 4

        and the levels in the python logging module are

            NOTSET      0
            DEBUG       10
            INFO        20
            WARNING     30
            ERROR       40
            CRITICAL    50

        """
        return self.CLANG_TO_LOGGING[self.proxied_object.severity]


class MetaCursor(MetaProxy):
    def __new__(mcs, name, bases, dct):
        """
        Register the class against the cindex.CursorKinds it is a proxy for.
        Custom parsers can be built by:

            1. Provide a base class derived from Cursor with its own CLASS_MAP:

                class MyCursor(Cursor):
                    CLASS_MAP = {}

            2. Override ALL the CLASS_MAP entries registered to the base
            Cursor, such as TranslationUnitCursor, by adding MyCursor as a right-most
            base class:

                class MyTranslationUnit(TranslationUnitCursor, MyCursor):
                    '''
                    The MRO ensures we pick up MyCursor->CLASS_MAP (and not
                    TranslationUnitCursor->Cursor->CLASS_MAP).
                    '''
                    pass

            3. Adding any new wrappers by subclassing MyCursor and specifying
            the CURSOR_KINDS it wraps, and any attributes to be proxied:

                class MyStruct(MyCursor):
                    CURSOR_KINDS = [CursorKind.STRUCT_DECL]

                    def __init__(self, container):
                        proxy_attributes = ["item_to_proxy", ...]
                        super(MyStruct, self).__init__(container, proxy_attributes)
        """
        result = super(MetaCursor, mcs).__new__(mcs, name, bases, dct)
        #
        # Register the class type against the kinds it proxies.
        #
        for kind in getattr(result, "CURSOR_KINDS"):
            result.CLASS_MAP[kind] = result
        return result


class Cursor(_Proxy):
    """
    This is the base class for all objects we wrap (unwrapped objects are still
    exposed as cindex.Cursor).
    """
    __metaclass__ = MetaCursor
    PROXIES = (
        clang.cindex.Cursor,
        #
        # All Cursors proxy some standard attributes for baseline compatibility with cindex.Cursor.
        #
        [
            "access_specifier", "displayname", "extent", "kind", "location", "referenced", "spelling",
        ]
    )
    CLASS_MAP = {}
    CURSOR_KINDS = []

    def get_children(self):
        """
        Get the children of this Cursor either as Cursors, or as clang.cindex.Cursor.
        """
        for child in self.proxied_object.get_children():
            yield self._wrapped(child)

    @property
    def semantic_parent(self):
        return self._wrapped(self.proxied_object.semantic_parent)

    @property
    def translation_unit(self):
        return self._wrapped(self.proxied_object.translation_unit.cursor)

    @classmethod
    def _wrapped(cls, cursor):
        """
        Wrap a cindex.cursor if possible.

        :param cursor:           The cindex.Cursor to wrap.
        :return: If possible, return the wrapped cindex_cursor, else just return the cindex_cursor.
        """
        try:
            #
            # A CursorKind.TRANSLATION_UNIT is not a clang.cindex.Cursor,
            # and as such is the only thing without a "kind".
            #
            kind = getattr(cursor, "kind", CursorKind.TRANSLATION_UNIT)
        except ValueError as e:
            #
            # Some kinds result in a Clang error.
            #
            logger.debug(_("Unknown _kind_id {} for {}".format(e, cursor.spelling)))
        else:
            try:
                clazz = cls.CLASS_MAP[kind]
            except KeyError:
                #
                # Some kinds don't have wrappers.
                #
                pass
            else:
                cursor = clazz(cursor)
        return cursor


class TranslationUnitCursor(Cursor):
    """
    Surprise: a translation unit is also a Cursor!
    """
    CURSOR_KINDS = [CursorKind.TRANSLATION_UNIT]
    CHECKED = False

    def __init__(self, tu):
        super(TranslationUnitCursor, self).__init__(tu)
        #
        # Check that the user fully overrode the CLASS_MAP. Doing this check
        # here makes sense as this is normally the first Cursor instantiated.
        #
        if not TranslationUnitCursor.CHECKED:
            for base_class in self.__class__.mro():
                base_class_map = getattr(base_class, "CLASS_MAP", self.CLASS_MAP)
                if self.CLASS_MAP is not base_class_map:
                    tmp = [base_class_map[k] for k in base_class_map if k not in self.CLASS_MAP]
                    if tmp:
                        tmp = list(set(tmp))
                        #
                        # The user forgot to override something.
                        #
                        raise AssertionError(_("CLASS_MAP items from {} not overridden by {}: {}").format(
                            base_class, self.__class__, tmp))
            TranslationUnitCursor.CHECKED = True
        #
        # In clang.cindex, a translation unit is not a cursor. So here, we need
        # merge a couple of attributes "manually".
        #
        proxy_attributes = ["get_includes", "get_tokens", "source_processor"]
        for attr in proxy_attributes:
            self._add_proxy(tu.translation_unit, attr)

    @property
    def diagnostics(self):
        for d in self.proxied_object.translation_unit.diagnostics:
            yield Diagnostic(d)

    @property
    def translation_unit(self):
        return self


class ContainerCursor(Cursor):
    CURSOR_KINDS = [CursorKind.NAMESPACE, CursorKind.CLASS_DECL]


class MetaType(MetaProxy):
    def __new__(mcs, name, bases, dct):
        """
        Register the class against the cindex.TypeKinds it is a proxy for.
        Custom parsers can be built by:

            1. Provide a base class derived from Type with its own CLASS_MAP:

                class MyType(Type):
                    CLASS_MAP = {}

            2. Override ALL the CLASS_MAP entries registered to the base
            Type, such as TranslationUnitCursor, by adding MyType as a right-most
            base class:

                class MyArray(Array, MyType):
                    '''
                    The MRO ensures we pick up MyType->CLASS_MAP (and not
                    Array->Type->CLASS_MAP).
                    '''
                    pass

            3. Adding any new wrappers by subclassing MyType and specifying
            the TYPE_KINDS it wraps, and any attributes to be proxied:

                class MyVector(MyType):
                    TYPE_KINDS = [TypeKind.VECTOR]

                    def __init__(self, vector):
                        proxy_attributes = ["item_to_proxy", ...]
                        super(MyVector, self).__init__(vector, proxy_attributes)
        """
        result = super(MetaType, mcs).__new__(mcs, name, bases, dct)
        #
        # Register the class type against the kinds it proxies.
        #
        for kind in getattr(result, "TYPE_KINDS"):
            result.CLASS_MAP[kind] = result
        return result


class Type(_Proxy):
    """
    This is the base class for all objects we wrap (unwrapped objects are still
    exposed as cindex.Type).
    """
    __metaclass__ = MetaType
    PROXIES = (
        clang.cindex.Type,
        #
        # All Types proxy some standard attributes for baseline compatibility with cindex.Type.
        #
        [
            "is_const_qualified", "kind", "spelling",
        ]
    )
    CLASS_MAP = {}
    TYPE_KINDS = [""]

    @classmethod
    def _wrapped(cls, type_):
        """
        Wrap a cindex.type if possible.

        :param type_:           The cindex.Type to wrap.
        :return: If possible, return the wrapped cindex_type, else just return the cindex_type.
        """
        try:
            if type_.kind == TypeKind.POINTER and \
                            type_.get_pointee().get_canonical().kind in FunctionType.TYPE_KINDS:
                #
                # FunctionCursor pointer case.
                #
                clazz = cls.CLASS_MAP[type_.get_pointee().get_canonical().kind]
            else:
                clazz = cls.CLASS_MAP[type_.kind]
        except KeyError:
            #
            # Some kinds don't have wrappers. For them, in order to provide a
            # wrapped version of get_canonical(), we act as the wrapper.
            #
            return cls.CLASS_MAP[""](type_)
        else:
            type_ = clazz(type_)
        return type_

    def get_canonical(self):
        return self._wrapped(self.proxied_object.get_canonical())


class FunctionType(Type):
    """
    For a function or function pointer.

    NOTE: In the function pointer case, self.kind == TypeKind.POINTER.
    """
    TYPE_KINDS = [TypeKind.MEMBERPOINTER, TypeKind.FUNCTIONPROTO]

    @property
    def is_pointer(self):
        """
        Is this a pointer-to-function?
        """
        return self.kind == TypeKind.POINTER

    @property
    def is_member_of(self):
        """
        Return the class if this is a (pointer-to-)member function, or None.
        """
        type_ = self.proxied_object.get_canonical()
        if self.is_pointer:
            type_ = type_.get_pointee().get_canonical()
        if type_.kind == TypeKind.MEMBERPOINTER:
            return type_.get_class_type()
        return None

    @property
    def argument_types(self):
        type_ = self.proxied_object.get_canonical()
        if self.is_pointer:
            type_ = type_.get_pointee().get_canonical()
        if type_.kind == TypeKind.MEMBERPOINTER:
            type_ = type_.get_pointee().get_canonical()
        return type_.argument_types() if type_.kind != TypeKind.POINTER else []

    @property
    def result_type(self):
        type_ = self.proxied_object.get_canonical()
        if self.is_pointer:
            type_ = type_.get_pointee().get_canonical()
        if type_.kind == TypeKind.MEMBERPOINTER:
            type_ = type_.get_pointee().get_canonical()
        return type_.get_result() if type_.kind != TypeKind.POINTER else type_


class PointerType(Type):
    """
    For a pointer which is not a function pointer.

    NOTE: In the pointer case, self.kind == TypeKind.POINTER, but see also FunctionType.
    """
    TYPE_KINDS = [TypeKind.POINTER, TypeKind.LVALUEREFERENCE]

    @property
    def underlying_type(self):
        return self._wrapped(self.proxied_object.get_pointee())
