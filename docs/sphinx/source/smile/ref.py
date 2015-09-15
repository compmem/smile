#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import random
import operator

def pass_thru(obj):
    return obj

class Ref(object):
    def __init__(self, func, *pargs, **kwargs):
        self.func = func
        self.pargs = pargs
        self.use_cache = kwargs.pop("use_cache", True)
        self.kwargs = kwargs
        self.cache_value = None
        self.cache_valid = False
        self.change_callbacks = []
        for dep in iter_deps((pargs, kwargs)):
            if not dep.use_cache:
                self.use_cache = False
                break

    @staticmethod
    def getattr(obj, name):
        return Ref(getattr, obj, name)

    @staticmethod
    def getitem(obj, index):
        return Ref(operator.getitem, obj, index)

    @staticmethod
    def object(obj):
        return Ref(pass_thru, obj, use_cache=False)

    @staticmethod
    def cond(cond, true_val, false_val):
        return Ref(lambda : (true_val if cond else false_val))

    @staticmethod
    def not_(obj):
        return Ref(operator.not_, obj)

    def eval(self):
        if self.cache_valid and len(self.change_callbacks):
            return self.cache_value

        value = val(self.func(*val(self.pargs), **val(self.kwargs)))

        if self.use_cache:
            self.cache_value = value
            self.cache_valid = True

        return value

    def add_change_callback(self, func, *pargs, **kwargs):
        #print "add_change_callback %s, %r, %r, %r" % (self, func, pargs, kwargs)
        if not len(self.change_callbacks):
            self.setup_dep_callbacks()
            self.cache_valid = False
        self.change_callbacks.append((func, pargs, kwargs))

    def remove_change_callback(self, func, *pargs, **kwargs):
        #print "remove_change_callback %s, %r, %r, %r" % (self, func, pargs, kwargs)
        try:
            self.change_callbacks.remove((func, pargs, kwargs))
        except ValueError:
            pass
        if not len(self.change_callbacks):
            self.teardown_dep_callbacks()

    def setup_dep_callbacks(self):
        for dep in iter_deps((self.pargs, self.kwargs)):
            dep.add_change_callback(self.dep_changed)

    def teardown_dep_callbacks(self):
        for dep in iter_deps((self.pargs, self.kwargs)):
            dep.remove_change_callback(self.dep_changed)

    def dep_changed(self):
        #print "dep_changed %r, %r" % (self, self.change_callbacks)
        self.cache_valid = False
        for func, pargs, kwargs in self.change_callbacks:
            func(*pargs, **kwargs)

    # delayed operators...
    def __call__(self, *pargs, **kwargs):
        return Ref(apply, self, pargs, kwargs)
    def __getitem__(self, index):
        return Ref(operator.getitem, self, index)
    def __getattr__(self, attr):
        return Ref(getattr, self, attr)
    def __lt__(self, other):
        return Ref(operator.lt, self, other)
    def __le__(self, other):
        return Ref(operator.le, self, other)
    def __gt__(self, other):
        return Ref(operator.gt, self, other)
    def __ge__(self, other):
        return Ref(operator.ge, self, other)
    def __eq__(self, other):
        return Ref(operator.eq, self, other)
    def __ne__(self, other):
        return Ref(operator.ne, self, other)
    def __and__(self, other):
        return Ref(operator.and_, self, other)
    def __rand__(self, other):
        return Ref(operator.and_, other, self)
    def __or__(self, other):
        return Ref(operator.or_, self, other)
    def __ror__(self, other):
        return Ref(operator.or_, other, self)
    def __xor__(self, other):
        return Ref(operator.xor, self. other)
    def __rxor__(self, other):
        return Ref(operator.xor, other, self)
    def __invert__(self):
        return Ref(operator.invert, self)
    def __add__(self, other):
        return Ref(operator.add, self, other)
    def __radd__(self, other):
        return Ref(operator.add, other, self)
    def __sub__(self, other):
        return Ref(operator.sub, self, other)
    def __rsub__(self, other):
        return Ref(operator.sub, other, self)
    def __pow__(self, other, modulo=None):
        return Ref(pow, self, other, modulo)
    def __rpow__(self, other):
        return Ref(operator.pow, other, self)
    def __mul__(self, other):
        return Ref(operator.mul, self, other)
    def __rmul__(self, other):
        return Ref(operator.mul, other, self)
    def __div__(self, other):
        #NOTE: using lambda to be sensitive to __future__.division
        return Ref(lambda a, b: a / b, self, other)
    def __rdiv__(self, other):
        #NOTE: using lambda to be sensitive to __future__.division
        return Ref(lambda a, b: a / b, other, self)
    def __floordiv__(self, other):
        return Ref(operator.floordiv, self, other)
    def __rfloordiv__(self, other):
        return Ref(operator.floordiv, other, self)
    def __mod__(self, other):
        return Ref(operator.mod, self, other)
    def __rmod__(self, other):
        return Ref(operator.mod, other, self)
    def __divmod__(self, other):
        return Ref(divmod, self,other)
    def __rdivmod__(self, other):
        return Ref(divmod, other, self)
    def __pos__(self):
        return Ref(operator.pos, self)
    def __neg__(self):
        return Ref(operator.neg, self)
    def __contains__(self, key):
        return Ref(operator.contains, self, key)
    def __lshift(self, other):
        return Ref(operator.lshift, self, other)
    def __rlshift(self, other):
        return Ref(operator.lshift, other, self)
    def __rshift(self, other):
        return Ref(operator.rshift, self, other)
    def __rrshift(self, other):
        return Ref(operator.rshift, other, self)
    def __abs__(self):
        return Ref(abs, self)


def jitter(lower, jitter_mag):
    return Ref(random.uniform, lower, lower + jitter_mag, use_cache=False)

def _shuffle(iterable):
    lst = list(iterable)
    random.shuffle(lst)
    return lst
def shuffle(iterable):
    return Ref(_shuffle, iterable, use_cache=False)

def val(obj):
    if isinstance(obj, Ref):
        return obj.eval()
    elif isinstance(obj, list):
        return [val(value) for value in obj]
    elif isinstance(obj, tuple):
        return tuple(val(value) for value in obj)
    elif isinstance(obj, dict):
        return {val(key) : val(value) for key, value in obj.iteritems()}
    elif isinstance(obj, slice):
        return slice(val(obj.start), val(obj.stop), val(obj.step))
    else:
        return obj

def iter_deps(obj):
    if isinstance(obj, Ref):
        yield obj
    elif isinstance(obj, list) or isinstance(obj, tuple):
        for value in obj:
            for dep in iter_deps(value):
                yield dep
    elif isinstance(obj, dict):
        for key, value in obj.iteritems():
            for dep in iter_deps(key):
                yield dep
            for dep in iter_deps(value):
                yield dep
    elif isinstance(obj, slice):
        for dep in iter_deps(obj.start):
            yield dep
        for dep in iter_deps(obj.stop):
            yield dep
        for dep in iter_deps(obj.step):
            yield dep


if __name__ == '__main__':

    import math
    x = [0.0]
    r = Ref(math.cos, Ref.getitem(x, 0))
    print x[0], val(r)
    x[0] += .5
    print x[0], val(r)

    r = Ref.object(str)(Ref.object(x)[0])
    x[0] += .75
    print x[0], val(r)

    r = (Ref.object(x)[0] > 0) & (Ref.object(x)[0] < 0)
    print x[0], val(r)
    r = (Ref.object(x)[0] > 0) & (Ref.object(x)[0] >= 0)
    x[0] -= 10.0
    print x[0], val(r)

    y = [7]
    ry = Ref.object(y)
    print y[0], val(ry[0] % 2), val(2 % ry[0])
    y[0] = 8
    print y[0], val(ry[0] % 2), val(2 % ry[0])

    class Jubba(object):     
        def __init__(self, val):
            self.x = val
            
        def __getitem__(self, index):  
            return Ref.getattr(self, index)

    a = Jubba(5)
    b = Ref.getattr(a, 'x')
    br = Ref.object(a).x
    print val(b), val(br)
    a.x += 42.0
    print val(b), val(br)
    
    c = {'y': 6}
    d = Ref.getitem(c, 'y')

    e = [4, 3, 2]
    f = Ref.getitem(e, 2)

    g = b+d+f
    print val(g)

    a.x = 6
    print val(g)

    c['y'] = 7
    print val(g)

    e[2] = 3
    print val(g)

    x = Jubba([])
    y = Ref.getitem(x, 'x')
    print val(y)
    y = y + [b]
    print val(y)
    y = y + [d]
    y = y + [f]
    print val(y)
