#!/usr/bin/env python

"""memoize.py
Module providing memoize decorators for regular functions and instance methods

Adapted from
http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/
http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/

"""

from functools import partial


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
    class Obj(object):
        @memoize_function
        def add(self, arg):
            return self + arg
    Obj.add(1)  # not enough arguments
    Obj.add(1, 2)  # returns 3, result is not cached

    This decorator has been adapted from
    http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/
    with mostly minor aesthetic modifications, plus the support for unhashable
    argument lists and a method for clearing the cahce on an instance.


    Parameters
    ----------
    f : method
        Method to decorate.

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
        self.f = f

    def __get__(self, obj, otype=None):
        if obj is None:
            return self.f
        return partial(self, obj)

    def __call__(self, *args, **kwargs):
        obj = args[0]
        try:
            cache = obj._cache
        except AttributeError:
            cache = obj._cache = {}
        try:
            key = (self.f, args[1:], frozenset(kwargs.items()))
            res = cache[key]
        except KeyError:
            cache[key] = res = self.f(*args, **kwargs)
        except TypeError:
            res = self.f(*args, **kwargs)
        return res

    @staticmethod
    def clear_cache(obj):
        obj._cache.clear()
