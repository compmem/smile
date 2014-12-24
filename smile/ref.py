#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import inspect

class Ref(object):
    """
    Reference to an object to delay evaluation.

    Most logical, mathematical, and indexing operations are implemented 
    for Ref objects allowing for delayed operations. It is 
    also possible to wrap functions for subsequent evaluation.

    Parameters
    ----------
    obj : object
        Object to be referenced.
    attr : string
        Attribute of the object to be referenced.
    gfunc : function
        Function to be called at evaluation.
    gfunc_args : list
        List of arguments evaluated and passed to the gfunc.
    gfunc_kwargs : dict
        Dictionary of keyword arguments evaluated and passed to gfunc.

    Example
    -------
    d = {'x':10, 'y':20}
    x = Ref(d,'x')
    y = Ref(d,'y')
    print val(x+y) # should be 30
    z = x + y
    print val(z) # should be 30
    d['x'] += 10
    print val(z) # should be 40
    str_sum = Ref(str)(x+y)
    ss = val(str_sum) # should be '40'
    print type(ss),ss
    
    """
    def __init__(self, obj=None, attr=None, 
                 gfunc=None, gfunc_args=None, gfunc_kwargs=None):
        self.gfunc = gfunc
        self.gfunc_args = gfunc_args
        self.gfunc_kwargs = gfunc_kwargs
        self.obj = obj
        self.attr = attr
        # if self.gfunc is None:
        #     # try and define it based on the obj and attr
        #     if not obj is None and not attr is None:
        #         if isinstance(attr,str) and hasattr(obj, attr):
        #             # treat as attr
        #             self.gfunc = lambda : getattr(obj, attr)
        #         else:
        #             # access with getitem
        #             self.gfunc = lambda : obj[attr]

    def set(self, value):
        if not self.obj is None and not self.attr is None:
            if isinstance(self.attr,str) and hasattr(self.obj, self.attr):
                # treat as attr
                setattr(self.obj, self.attr, value)
            else:
                # access with getitem
                self.obj[self.attr] = value
        else:
            raise ValueError('You can only set a reference with a known obj and attr')
                
    def __call__(self, *args, **kwargs):
        if self.gfunc:
            gfunc = self.gfunc
        elif inspect.isfunction(self.obj) or \
             inspect.isbuiltin(self.obj) or \
             hasattr(self.obj, '__call__'):
            gfunc = self.obj
        else:
            raise ValueError('You must specify a function as the obj or gfunc.')
        return Ref(gfunc=gfunc, gfunc_args=args, gfunc_kwargs=kwargs)

    def eval(self):
        if self.gfunc:
            # eval the args to the func if necessary
            if self.gfunc_args is None:
                args = []
            else:
                args = val(self.gfunc_args)

            if self.gfunc_kwargs is None:
                kwargs = {}
            else:
                kwargs = val(self.gfunc_kwargs)
            
            # eval the function
            return self.gfunc(*args, **kwargs)
        else:
            # try and define it based on the obj and attr
            if not self.obj is None:
                # get the values of the obj and attr
                obj = val(self.obj)
            else:
                raise ValueError("Ref must either have obj or gfunc defined.")
            if not self.attr is None:
                attr = val(self.attr)
                if isinstance(attr,str) and hasattr(obj, attr):
                    # treat as attr
                    return getattr(obj, attr)
                else:
                    # access with getitem
                    return obj[attr]
            else:
                return obj
        #return self.obj #getattr(self.obj, self.attr)
        
    def __getitem__(self, index):
        return Ref(gfunc=lambda : val(self)[val(index)])

    #def __getattribute__(self, attr):
    def __getattr__(self, attr):
        #return Ref(gfunc=lambda : getattr(val(self),val(attr)))
        return Ref(gfunc=lambda : object.__getattribute__(val(self), val(attr)))
        
    def __lt__(self, o):
        return Ref(gfunc=lambda : val(self)<val(o))
    def __le__(self, o):
        return Ref(gfunc=lambda : val(self)<=val(o))
    def __gt__(self, o):
        return Ref(gfunc=lambda : val(self)>val(o))
    def __ge__(self, o):
        return Ref(gfunc=lambda : val(self)>=val(o))
    def __eq__(self, o):
        return Ref(gfunc=lambda : val(self)==val(o))
    def __ne__(self, o):
        return Ref(gfunc=lambda : val(self)<>val(o))
    def __and__(self, o):
        return Ref(gfunc=lambda : val(self)&val(o))
    def __rand__(self, o):
        return Ref(gfunc=lambda : val(o)&val(self))
    def __or__(self, o):
        return Ref(gfunc=lambda : val(self)|val(o))
    def __ror__(self, o):
        return Ref(gfunc=lambda : val(o)|val(self))
    def __xor__(self, o):
        return Ref(gfunc=lambda : val(self)^val(o))
    def __rxor__(self, o):
        return Ref(gfunc=lambda : val(o)^val(self))
    def __add__(self, o):
        return Ref(gfunc=lambda : val(self)+val(o))
    def __radd__(self, o):
        return Ref(gfunc=lambda : val(o)+val(self))
    def __sub__(self, o):
        return Ref(gfunc=lambda : val(self)-val(o))
    def __rsub__(self, o):
        return Ref(gfunc=lambda : val(o)-val(self))
    def __pow__(self, o):
        return Ref(gfunc=lambda : val(self)**val(o))
    def __rpow__(self, o):
        return Ref(gfunc=lambda : val(o)**val(self))
    def __mul__(self, o):
        return Ref(gfunc=lambda : val(self)*val(o))
    def __rmul__(self, o):
        return Ref(gfunc=lambda : val(o)*val(self))
    def __div__(self, o):
        return Ref(gfunc=lambda : val(self)/val(o))
    def __floordiv__(self, o):
        return Ref(gfunc=lambda : val(self)//val(o))
    def __rdiv__(self, o):
        return Ref(gfunc=lambda : val(o)/val(self))
    def __rfloordiv__(self, o):
        return Ref(gfunc=lambda : val(o)//val(self))
    def __mod__(self, o):
        return Ref(gfunc=lambda : val(self)%val(o))
    def __rmod__(self, o):
        return Ref(gfunc=lambda : val(o)%val(self))
    def __pos__(self):
        return self
    def __neg__(self):
        return Ref(gfunc=lambda : -val(self))
    def append(self,o):
        return Ref(gfunc=lambda : val(self)+[val(o)])
    def __contains__(self, key):
        return Ref(gfunc=lambda : key in val(self))
        
def val(x, recurse=True):
    """
    Evaluate a Ref object.

    Call this when you need to evaluate a reference to get the current value.

    This method will (optionally) recursively evaluate lists and dictionaries 
    to ensure all Refs are evaluated. It is safe to call this on non-Ref objects,
    and it will simply return what is passed in.
    
    Parameters
    ----------
    x : {Ref object, list, dict}
        Ref object to evaluate.
    recurse : Boolean
        Whether to recurse lists and dicts.
    
    """
    # possibly put this in a for loop if we run into infinite recursion issues
    while isinstance(x,Ref): #or inspect.isfunction(x) or inspect.isbuiltin(x):
        x = x.eval()
    if recurse:
        if isinstance(x,list):
            # make sure we get value of all the items
            x = [val(x[i]) for i in xrange(len(x))]
        elif isinstance(x,tuple):
            # make sure we get value of all the items
            x = tuple([val(x[i]) for i in xrange(len(x))])
        elif isinstance(x,dict):
            x = {k:val(x[k]) for k in x}        
    return x


if __name__ == '__main__':

    import math
    x = [0.0]
    r = Ref(math.cos)(Ref(x,0))
    print x[0], val(r)
    x[0] += .5
    print x[0], val(r)

    r = Ref(str)(Ref(x)[0])
    x[0] += .75
    print x[0], val(r)

    r = Ref((Ref(x)[0]>0)&(Ref(x)[0]<0))
    print x[0],val(r)
    r = Ref((Ref(x)[0]>0)&(Ref(x)[0]>=0))
    x[0] -= 10.0
    print x[0],val(r)

    y = [7]
    ry = Ref(y)
    print y[0],val(ry[0]%2), val(2%ry[0])
    y[0] = 8
    print y[0],val(ry[0]%2), val(2%ry[0])

    class Jubba(object):     
        def __init__(self, val):
            self.x = val
            
        def __getitem__(self, index):  
            return Ref(self, index)
            #return Ref(lambda : getattr(self,index))

    a = Jubba(5)
    b = Ref(a,'x')
    br = Ref(a).x
    print val(b), val(br)
    a.x += 42.
    print val(b), val(br)
    
    c = {'y':6}
    d = Ref(c,'y')

    e = [4, 3, 2]
    f = Ref(e,2)

    g = b+d+f
    print val(g)

    a.x = 6
    print val(g)

    c['y'] = 7
    print val(g)

    e[2] = 3
    print val(g)

    x = Jubba([])
    y = Ref(x,'x')
    print val(y)
    y = y + [b]
    print val(y)
    y = y + [d]
    y = y + [f]
    print val(y)
