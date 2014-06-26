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
    def __init__(self, obj=None, attr=None, gfunc=None, gfunc_args=None):
        self.gfunc = gfunc
        self.gfunc_args = gfunc_args
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
                
    def __call__(self):
        if self.gfunc:
            if self.gfunc_args is None:
                return self.gfunc()
            else:
                # process the args and pass them in
                return self.gfunc(val(self.gfunc_args))
        else:
            # try and define it based on the obj and attr
            if not self.obj is None and not self.attr is None:
                # get the values of the obj and attr
                obj = val(self.obj)
                attr = val(self.attr)
                if isinstance(attr,str) and hasattr(obj, attr):
                    # treat as attr
                    return getattr(obj, attr)
                else:
                    # access with getitem
                    return obj[attr]
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
    def __pos__(self):
        return self
    def __neg__(self):
        return Ref(gfunc=lambda : -val(self))
    def append(self,o):
        return Ref(gfunc=lambda : val(self)+[val(o)])
        
def val(x, recurse=True):
    # possibly put this in a for loop if we run into infinite recursion issues
    while isinstance(x,Ref) or inspect.isfunction(x) or inspect.isbuiltin(x):
        x = x()
    if recurse:
        if isinstance(x,list):
            # make sure we get value of all the items
            x = [val(x[i]) for i in xrange(len(x))]
        elif isinstance(x,dict):
            x = {k:val(x[k]) for k in x}        
    return x


if __name__ == '__main__':

    class Jubba(object):     
        def __init__(self, val):
            self.x = val
            
        def __getitem__(self, index):  
            return Ref(self, index)
            #return Ref(lambda : getattr(self,index))

    a = Jubba(5)
    b = Ref(a,'x')
    
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
