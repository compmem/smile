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

# NOTE If you want to test out what your code would look like on a different
# monitor (that is smaller than the one you already have up), you can run the
# following line in the command line:
#                python your_code.py -f -r **width**x**height**
# Where width and height are replaced with the resolution of the monitor you
# want to test. 

RADIUS = 100


# Set a scale_box to [600, 500] which is [width, height] and scale_up/scale_down
# to make sure that no matter what the monitor size is, everything will be scale
# to fit in side a scale_box.
exp = Experiment(scale_box=[600,500], scale_up=True, scale_down=True)

# As an example, if you run this file on one computer, and then another one
# with a different monitor size, the first number in this debug should be
# different on both machines, but the second number will be 10.
Debug(s=s(10), b=10)

# Font size is a perfect example of something you would want to scale with
# monitor size and screen density.
Label(text="These are some instructions", font_size=s(20))
with UntilDone():
    if platform == "android":
        with ButtonPress():
            Button(size=exp.screen.size, background_color=(0, 0, 0, 0))
    else:
        KeyPress()
Wait(1.)

# MovingDots allows us to to play with many different sizing and positioning
# parameters. The scale of the dots, the radius of the apature, the speed of the
# dots, all of these things are perfect for using scale.
with Parallel():
    md1 = MovingDots(scale=s(50), radius=s(RADIUS), speed=s(100))
    # Please note the md1.top + s(50). If you want to do relative positioning,
    # then you must use scale if you want the relative distance between things
    # to be equal.
    Label(text="50: "+Ref(str,s(50)), y=md1.top + s(50), font_size=s(40))
with UntilDone():
    if platform == "android":
        with ButtonPress():
            Button(size=exp.screen.size, background_color=(0, 0, 0, 0))
    else:
        KeyPress()
Wait(1.)

# The following are 3 more examples of what it would look like if we scaled
# different parameters in a moving dot stimulus.
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
