from smile.ref import Ref, val, shuffle
import math
x = [0.0]
r = Ref(math.cos, Ref.getitem(x, 0))
a = Ref.object(7.)
print(7//3,  val(a // 3.), 7/3, val(a / 3.))
print(x[0], val(r))
x[0] += .5
print(x[0], val(r))

r = Ref.object(str)(Ref.object(x)[0])
x[0] += .75
print(x[0], val(r))

r = (Ref.object(x)[0] > 0) & (Ref.object(x)[0] < 0)
print(x[0], val(r))
r = (Ref.object(x)[0] > 0) & (Ref.object(x)[0] >= 0)
x[0] -= 10.0
print(x[0], val(r))

y = [7]
ry = Ref.object(y)
print(y[0], val(ry[0] % 2), val(2 % ry[0]))
y[0] = 8
print(y[0], val(ry[0] % 2), val(2 % ry[0]))

class Jubba(object):
    def __init__(self, val):
        self.x = val

    def __getitem__(self, index):
        return Ref.getattr(self, index)

a = Jubba(5)
b = Ref.getattr(a, 'x')
br = Ref.object(a).x
print(val(b), val(br))
a.x += 42.0
print(val(b), val(br))

c = {'y': 6}
d = Ref.getitem(c, 'y')

e = [4, 3, 2]
f = Ref.getitem(e, 2)

g = b+d+f
print(val(g))

a.x = 6
print(val(g))

c['y'] = 7
print(val(g))

e[2] = 3
print(val(g))

x = Jubba([])
y = Ref.getitem(x, 'x')
print(val(y))
y = y + [b]
print(val(y))
y = y + [d]
y = y + [f]
print(val(y))
