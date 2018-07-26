from smile.common import *
from kivy.metrics import sp, dp
from kivy import platform
from smile.ref import NotAvailable
from smile.scale import scale as s


# This is an example on how to use the scale function in smile. If you want
# all of your sizing to be the same on every machine, you can set scale_box
# to None. Using scale with no bounding box will change your numbers depending
# on the pixel density of your screen using kivy's built in dp function. You
# will want to wrap every number that has anything to do with sizing,
# positioning, or moving in scale(x).

# Sometimes you might want to scale down only if the screen is too small to fit
# your stimulus. In this case you set a *scale_box* and the scale_up/down flags.
# If scale_down is True, **scale** will scale your numbers such that the dp on
# your scale box is able to fit within the screen. If the screen is bigger than
# the scale box, then your sizing numbers will only be scaled by **dp**, meaning
# your stimulus will look the same on all monitors that are bigger than the
# scale box.



RADIUS = 100

exp = Experiment(scale_box=[600,500], scale_up=True, scale_down=True)

Debug(s=s(10), b=10)


Label(text="These are some instructions", font_size=s(20))
with UntilDone():
    if platform == "android":
        with ButtonPress():
            Button(size=exp.screen.size, background_color=(0, 0, 0, 0))
    else:
        KeyPress()
Wait(1.)
with Parallel():
    md1 = MovingDots(scale=s(50), radius=s(RADIUS), speed=s(100))
    Label(text="50: "+Ref(str,s(50)), y=md1.top + s(50), font_size=s(40))
with UntilDone():
    if platform == "android":
        with ButtonPress():
            Button(size=exp.screen.size, background_color=(0, 0, 0, 0))
    else:
        KeyPress()
Wait(1.)
with Parallel():
    md2 = MovingDots(scale=s(10), radius=s(RADIUS), speed=s(100))
    Label(text="10: "+Ref(str,s(10)), y=md2.top + s(50), font_size=s(40))
with UntilDone():
    if platform == "android":
        with ButtonPress():
            Button(size=exp.screen.size, background_color=(0, 0, 0, 0))
    else:
        KeyPress()
Wait(1.)
with Parallel():
    md3 = MovingDots(scale=s(5), radius=s(RADIUS), speed=s(100))
    Label(text="5: "+Ref(str,s(5)), y=md3.top + s(50), font_size=s(40))
with UntilDone():
    if platform == "android":
        with ButtonPress():
            Button(size=exp.screen.size, background_color=(0, 0, 0, 0))
    else:
        KeyPress()
Wait(1.)
with Parallel():
    md4 = MovingDots(scale=s(1), radius=s(RADIUS), speed=s(100))
    Label(text="1: "+Ref(str,s(1)), y=md4.top + s(50), font_size=s(40))
with UntilDone():
    if platform == "android":
        with ButtonPress():
            Button(size=exp.screen.size, background_color=(0, 0, 0, 0))
    else:
        KeyPress()
Wait(1.)
exp.run()
