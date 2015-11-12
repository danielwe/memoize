#!/usr/bin/env python

"""parameters.py
Module providing a data descriptor for use with `memoize_method`

"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from .memoize import memoize_method, memoize_function
from collections import Callable


class Memparams(object):
    """
    Data descriptor that triggers memoize cache clearance on containing object
    when set, mutated or deleted

    Parameters
    ----------
    base : type
        Base class to derive data storage from. The only thing required of this
        class is that it supports copy constructor syntax: `base(instance)`
        should return a copy of `instance` if `instance` is an object of type
        `base` (preferably with support for the usual duck typing
        generalizations of this behavior).
    name : hashable
        Name to use internally, in addition to the base, for storing the
        descriptor data on objects.  ..note:: If multiple instances of
        Memparams are assoicated members of the same class and have identical
        base and name, they will end up pointing to the same data.

    """
    _storage_name = "_memparams_storage"

    def __init__(self, base, name):
        self.base = base
        self.name = name
        self.key = (base, name)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if hasattr(obj, self._storage_name):
            storage = getattr(obj, self._storage_name)
            if self.key in storage:
                return storage[self.key]
        raise AttributeError("Attribute not set on {}".format(obj))

    def __set__(self, obj, value):
        value = memparamstorage(self.base, obj, value)
        storage_name = self._storage_name
        if hasattr(obj, storage_name):
            storage = getattr(obj, storage_name)
            storage[self.key] = value
        else:
            setattr(obj, storage_name, {self.key: value})
        memoize_method.clear_cache(obj)

    def __delete__(self, obj):
        storage_name = self._storage_name
        if hasattr(obj, storage_name):
            storage = getattr(obj, storage_name)
            del storage[self]
            if not storage:
                delattr(obj, storage_name)
        memoize_method.clear_cache(obj)


def memparamstorage(base, obj, *args, **kwargs):
    return _memparamstorage(base)(obj, *args, **kwargs)


@memoize_function
def _memparamstorage(base):
    """
    Return an instance of a _MemparamStorage class derived from `base`

    Parameters
    ----------
    base : type
        Base class to derive data storage from. Must support copy constructor
        syntax: `base(instance)` should return a copy of `instance` if
        `instance` is an object of type `base` (preferably with support for the
        usual duck typing generalizations of this behavior).

    Returns
    -------
    _MemparamStorage : type
        Data storage class for Memparams

    """
    class _MSInitializer(base):
        """
        New version of `base` that is guaranteed to be mutable and under our
        control in every respect. Used in the initalization of
        _MemparamStorage.

        """
        pass

    class _MemparamStorage(_MSInitializer):
        """
        Container class that stores a reference to an object and clears memoize
        cache on that object when mutated.

        This class intercepts all methods on `base` with attribute name equal
        to the name of a mutating method on one of the standard python types
        and container classes. Each time such a method is invoked, the memoize
        cache on the referenced object is cleared.

        Parameters
        ----------
        obj : object
            Object to manage memoize cache on.
        *args, **kwargs
            A valid argument list to `base()`.

        """
        def __new__(cls, obj, *args, **kwargs):
            new = _MSInitializer.__new__(_MSInitializer, *args, **kwargs)

            # Once 'new' has acquired its final type, no attributes can be
            # assigned to it without clearing the cache on 'obj', and we don't
            # need that to happen during initialization. Therefore, 'obj' and
            # 'base' is be stored while 'new' is in a temporary state of being
            # the parent type.
            new.obj = obj
            new.base = base

            new.__class__ = cls
            return new

        def __init__(self, obj, *args, **kwargs):
            baseinit = base.__init__
            if baseinit is not object.__init__:
                baseinit(self, *args, **kwargs)

        # Since this class is defined in a local scope, it will not be
        # picklable unless we define a __reduce__ method whose return tuple
        # only contains picklable elements (and is otherwise consistent with
        # the __reduce__ syntax). This relies on copy constructor support.
        def __reduce__(self):
            return memparamstorage, (self.base, self.obj, self.base(self))

    class Mutators():
        names = (
            '__setattr__',
            '__delattr__',
            '__setitem__',
            '__delitem__',
            '__setslice__',
            '__delslice__',
            '__iadd__',
            '__isub__',
            '__imul__',
            '__imatmul__',
            '__idiv__',
            '__itruediv__',
            '__ifloordiv__',
            '__imod__',
            '__ipow__',
            '__ilshift__',
            '__irshift__',
            '__iand__',
            '__ixor__',
            '__ior__',
            'append',
            'appendleft',
            'clear',
            'discard',
            'extend',
            'extendleft',
            'insert',
            'pop',
            'popleft',
            'popitem',
            'remove',
            'reverse',
            'rotate',
            'setdefault',
            'sort',
            'subtract',
            'update',
        )

    def _make_new_mutator(mutator):
        def new_mutator(self, *args, **kwargs):
            res = mutator(self, *args, **kwargs)
            # A particular edge case: if the action of mutator is to change
            # self.obj (this should really never be done, but no one will stop
            # anyone), the cache on the old self.obj is left intact, while the
            # cache on the new self.obj is cleared.
            memoize_method.clear_cache(self.obj)
            return res
        return new_mutator

    for mutator_name in Mutators.names:
        if hasattr(_MemparamStorage, mutator_name):
            mutator = getattr(_MemparamStorage, mutator_name)
            if isinstance(mutator, Callable):
                setattr(_MemparamStorage, mutator_name,
                        _make_new_mutator(mutator))

    return _MemparamStorage
