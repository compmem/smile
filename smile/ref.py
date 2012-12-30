#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import inspect

class Ref():
    def __init__(self, obj=None, attr=None, gfunc=None):
        self.gfunc = gfunc
        if self.gfunc is None:
            # try and define it based on the obj and attr
            if not obj is None and not attr is None:
                if isinstance(attr,str) and hasattr(obj, attr):
                    # treat as attr
                    self.gfunc = lambda : getattr(obj, attr)
                else:
                    # access with getitem
                    self.gfunc = lambda : obj[attr]

    def __call__(self):
        if self.gfunc:
            return self.gfunc()
        #return self.obj #getattr(self.obj, self.attr)
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
    def __rdiv__(self, o):
        return Ref(gfunc=lambda : val(o)/val(self))
    def __pos__(self):
        return self
    def __neg__(self):
        return Ref(gfunc=lambda : -val(self))
        
def val(x):
    # possibly put this in a for loop if we run into infinite recursion issues
    while isinstance(x,Ref) or inspect.isfunction(x) or inspect.isbuiltin(x):
        x = x()
    if isinstance(x,list):
        # make sure we get value of all the items
        for i in xrange(len(x)):
            x[i] = val(x[i])
    elif isinstance(x,dict):
        for k in x:
            x[k] = val(x[k])
        
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
