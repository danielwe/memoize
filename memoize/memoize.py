#!/usr/bin/env python

"""memoize.py
Module providing memoize decorators for instance methods and ordinary functions

Adapted from
http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/  # noqa

"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from collections import Hashable, Mapping
from functools import partial, update_wrapper
from inspect import getcallargs  # Python >= 2.7
try:
    # Python 3
    from inspect import getfullargspec
except ImportError:
    # Python 2
    from inspect import getargspec as getfullargspec


class memoize_function(object):
    """Cache the return value of a function

    This class is meant to be used as a decorator of functions. The return
    value from a given function invocation will be cached on the decorated
    function. All arguments passed to a method decorated with memoize must be
    hashable.

    If the argument list is not hashable, the result is returned as usual, but
    the result is not cached.

    This decorator has been adapted from
    http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/  # noqa
    and adapted to work on functions instead of methods.

    Parameters
    ----------
    f : callable
        Function to memoize.

    Examples
    --------
    >>> @memoize_function
    >>> def types(*args, **kwargs):
    >>>     argtypes = [type(arg) for arg in args]
    >>>     kwargtypes = {key: type(val) for (key, val) in kwargs.items()}
    >>>     return argtypes, kwargtypes
    >>>
    >>> types((1,), key='value')  # result will be cached
    ([tuple], {'key': str})
    >>> types([1], key=set('value'))  # result will not be cached
    ([list], {'key': set})

    """
    # Copyright (c) 2012 Daniel Miller
    # Copyright (c) 2015 Daniel Wennberg
    #
    # Permission is hereby granted, free of charge, to any person obtaining
    # a copy of this software and associated documentation files (the
    # "Software"), to deal in the Software without restriction, including
    # without limitation the rights to use, copy, modify, merge, publish,
    # distribute, sublicense, and/or sell copies of the Software, and to permit
    # persons to whom the Software is furnished to do so, subject to the
    # following conditions:
    #
    # The above copyright notice and this permission notice shall be included
    # in all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    # OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    # MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
    # NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    # DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    # OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
    # USE OR OTHER DEALINGS IN THE SOFTWARE.

    cache_name = '_memoize_function_cache'

    def __init__(self, f):
        self.f = f
        setattr(self, self.cache_name, {})
        update_wrapper(self, f)

    def __call__(self, *args, **kwargs):
        # Get internal state from argument list
        f = self.f
        callargs = getcallargs(f, *args, **kwargs)
        varkw = getfullargspec(f)[2]

        # Make callargs a _HashableDict and create cache key
        if varkw is not None:
            callargs[varkw] = _HashableDict(callargs[varkw])
        key = _HashableDict(callargs)

        # Get cache dict
        cache = getattr(self, self.cache_name)

        # Lookup/compute result
        try:
            if key in cache:
                return cache[key]
            else:
                cache[key] = res = f(*args, **kwargs)
                return res
        except TypeError:
            return f(*args, **kwargs)

    def clear_cache(self):
        """
        Clear the memoize function's cache

        Examples
        --------
        >>> @memoize_function
        >>> def types(*args, **kwargs):
        >>>     argtypes = [type(arg) for arg in args]
        >>>     kwargtypes = {key: type(val) for (key, val) in kwargs.items()}
        >>>     return argtypes, kwargtypes
        >>>
        >>> types((1,), key='value')  # result will be cached
        ([tuple], {'key': str})
        >>> types.clear_cache()  # cache on 'types' cleared

        """
        getattr(self, self.cache_name).clear()


class memoize_method(object):
    """Cache the return value of a method

    This class is meant to be used as a decorator of methods. The return value
    from a given method invocation will be cached on the instance whose method
    was invoked. All arguments passed to a method decorated with memoize must
    be hashable.

    If the argument list is not hashable, the result is returned as usual, but
    the result is not cached.

    If a memoized method is invoked directly on its class the result will not
    be cached.

    This decorator has been adapted from
    http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/  # noqa
    with mostly minor aesthetic modifications, plus the support for unhashable
    argument lists and a method for clearing the cahce on an instance.

    ..note:: due to the reliance on circular references, this memoizer can not
    be used on methods of classes with custom `__hash__()` methods when support
    for pickling and unpickling is required.

    Parameters
    ----------
    f : method
        Method to memoize.

    Examples
    --------
    >>> class AddToThree(object):
    >>>     base = 3
    >>>     @memoize_method
    >>>     def add(self, addend):
    >>>         return self.base + addend
    >>>
    >>> adder = AddToThree()
    >>> adder.add(4)  # result will be cached
    7
    >>> AddToThree.add(adder, 4)  # result will not be cached
    7

    """
    # Copyright (c) 2012 Daniel Miller
    # Copyright (c) 2015 Daniel Wennberg
    #
    # Permission is hereby granted, free of charge, to any person obtaining
    # a copy of this software and associated documentation files (the
    # "Software"), to deal in the Software without restriction, including
    # without limitation the rights to use, copy, modify, merge, publish,
    # distribute, sublicense, and/or sell copies of the Software, and to permit
    # persons to whom the Software is furnished to do so, subject to the
    # following conditions:
    #
    # The above copyright notice and this permission notice shall be included
    # in all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    # OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    # MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
    # NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    # DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    # OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
    # USE OR OTHER DEALINGS IN THE SOFTWARE.

    cache_name = '_memoize_method_cache'
    friend_list_name = 'memoize_friends'

    def __init__(self, f):
        self.f = f
        update_wrapper(self, f)

    def __get__(self, obj, otype=None):
        if obj is None:
            return self.f
        return partial(self, obj)

    def __call__(self, *args, **kwargs):
        # Get internal state from argument list
        f = self.f
        callargs = getcallargs(f, *args, **kwargs)
        varkw = getfullargspec(f)[2]

        # Remove calling instance (the 'self' parameter) from callargs.
        # This is crucial: we don't want to rely on the calling instance being
        # hashable.
        obj = args[0]
        for (key, value) in callargs.items():
            if value is obj:
                del callargs[key]
                break

        # Make callargs a _HashableDict and create cache key
        if varkw is not None:
            callargs[varkw] = _HashableDict(callargs[varkw])
        key = (f.__name__, _HashableDict(callargs))

        # Get/set cache dict
        if hasattr(obj, self.cache_name):
            cache = getattr(obj, self.cache_name)
        else:
            cache = {}
            setattr(obj, self.cache_name, cache)

        # Lookup or compute result
        try:
            if key in cache:
                return cache[key]
            else:
                cache[key] = res = f(*args, **kwargs)
                return res
        except TypeError:
            return f(*args, **kwargs)

    @classmethod
    def clear_cache(cls, obj):
        """
        Clear the memoizer's cache on an object

        The cache can optionally be cleared recursively on a graph of related
        objects by storing a sequence of objects related to `obj` at
        `getattr(obj, memoize_method.friend_list_name)`.

        Parameters
        ----------
        obj : object
              The cache for all memoized methods on `obj` will be cleared.

        Examples
        --------
        >>> class AddToThree(object):
        >>>     base = 3
        >>>     @memoize_method
        >>>     def add(self, addend):
        >>>         return self.base + addend
        >>>
        >>> adder = AddToThree()
        >>> adder.add(4)  # result will be cached
        7
        >>> memoize_method.clear_cache(adder)  # cache on 'adder' cleared

        """
        # For debugging:
        #print("Clearing cache on {}".format(obj))
        if hasattr(obj, cls.cache_name):
            getattr(obj, cls.cache_name).clear()

        if hasattr(obj, cls.friend_list_name):
            for friend in getattr(obj, cls.friend_list_name):
                if friend is not obj:
                    cls.clear_cache(friend)

    @classmethod
    def register_friend(cls, host, friend):
        """
        Register a new friend to an object for cache clearance

        Whenever cache is cleared on `host`, it will also be cleared on
        `friend`.

        Parameters
        ----------
        host : object
            The object on which to register a cache clearance friend.
        friend : object
            The new cache clearance friend to register.

        """
        if friend is not host:
            if hasattr(host, cls.friend_list_name):
                getattr(host, cls.friend_list_name).add(friend)
            else:
                setattr(host, cls.friend_list_name, set([friend]))

    @classmethod
    def unregister_friend(cls, host, friend):
        """
        Unregister a friend to an object for cache clearance

        Cache is cleared on `friend` will not be automatically executed after
        cache clearance on `host` anymore.

        Parameters
        ----------
        host : object
            The object on which to unregister a cache clearance friend.
        friend : object
            The cache clearance friend to unregister.

        """
        if friend is not host:
            if hasattr(host, cls.friend_list_name):
                getattr(host, cls.friend_list_name).remove(friend)


class _HashableDict(Hashable, Mapping):
    """
    An immutable, hashable mapping type. The hash is computed using both keys
    and values.

    Inspired by Raymond Hettinger's contribution at
    http://stackoverflow.com/questions/1151658/python-hashable-dicts

    Parameters
    ----------
    *args, **kwargs
        Any argument list that can initialize a regular dict with only hashable
        entries.

    """
    # Copyright (c) 2015 Daniel Wennberg
    #
    # Permission is hereby granted, free of charge, to any person obtaining
    # a copy of this software and associated documentation files (the
    # "Software"), to deal in the Software without restriction, including
    # without limitation the rights to use, copy, modify, merge, publish,
    # distribute, sublicense, and/or sell copies of the Software, and to permit
    # persons to whom the Software is furnished to do so, subject to the
    # following conditions:
    #
    # The above copyright notice and this permission notice shall be included
    # in all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    # OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    # MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
    # NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    # DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    # OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
    # USE OR OTHER DEALINGS IN THE SOFTWARE.

    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()

    def __hash__(self):
        return hash((frozenset(self._dict.keys()),
                     frozenset(self._dict.values())))
