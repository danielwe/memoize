#!/usr/bin/env python

"""memoize.py
Module providing memoize decorators for regular functions and instance methods

Adapted from
http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/
http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/

"""

from functools import partial, update_wrapper


def memoize_function(f):
    """Memoization decorator for a function taking one or more arguments.

    This decorator has been adapted from the suggested approaches in the
    discussion at
    http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/

    This version also supports keyword arguments.

    Parameters
    ----------
    f : callable
        Function to memoize.

    """
    # Copyright (c) 2012 Martin Miller
    # Copyright (c) 2012 Oren Tirosh
    # Copyright (c) 2014 Isaac Levy
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
    # The above copyright notice and this permission notice shall be included in
    # all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    # THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    # DEALINGS IN THE SOFTWARE.
    class memodict(dict):
        __slots__ = ()

        def __getitem__(self, *args, **kwargs):
            key = (args, frozenset(kwargs.items()))
            return dict.__getitem__(self, key)

        def __missing__(self, key):
            args, kwargs = key[0], dict(key[1])
            self[key] = ret = f(*args, **kwargs)
            return ret

    return memodict().__getitem__


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
    http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/
    with mostly minor aesthetic modifications, plus the support for unhashable
    argument lists and a method for clearing the cahce on an instance.

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
    # The above copyright notice and this permission notice shall be included in
    # all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    # THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    # DEALINGS IN THE SOFTWARE.

    def __init__(self, f):
        self._f = f

    def __get__(self, obj, otype=None):
        f = self._f
        if obj is None:
            return f

        try:
            methods = obj._memoize_method_instance_methods
        except AttributeError:
            methods = obj._memoize_method_instance_methods = {}

        try:
            obj_f = methods[f]
        except KeyError:
            obj_f = partial(self, obj)
            update_wrapper(obj_f, f)
            methods[f] = obj_f
        return obj_f

    def __call__(self, *args, **kwargs):
        f = self._f
        obj = args[0]

        try:
            cache = obj._memoize_method_cache
        except AttributeError:
            cache = obj._memoize_method_cache = {}

        try:
            key = (f, args[1:], frozenset(kwargs.items()))
            res = cache[key]
        except KeyError:
            cache[key] = res = f(*args, **kwargs)
        except TypeError:
            res = f(*args, **kwargs)
        return res

    @staticmethod
    def clear_cache(obj):
        """
        Clear the memoizer's cache on an object

        Parameters
        ----------
        obj : object
              The cache for all memoized methods on 'obj' will be cleared.

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
        try:
            cache = obj._memoize_method_cache
        except AttributeError:
            pass
        else:
            cache.clear()
