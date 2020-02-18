from smile.experiment import Experiment
from smile.state import Wait, Loop, Parallel, Meanwhile, UntilDone, Serial, \
                        Done, Debug
from smile.video import ProgressBar, Image, RstDocument, ButtonPress, Button, \
                        Slider, Rectangle, TextInput, Label, Ellipse,\
                        BackgroundColor, Video, Triangle, Bezier, BoxLayout

from smile.mouse import MouseCursor
from math import sin, cos

exp = Experiment(background_color="#330000")
Wait(2.0)

pb = ProgressBar(max=100)
with UntilDone():
    pb.slide(value=100, duration=2.0)

Image(source="face-smile.png", duration=5.0)

text = """
.. _top:

Hello world
===========

This is an **emphasized text**, some ``interpreted text``.
And this is a reference to top_::

$ print("Hello world")

"""
RstDocument(text=text, duration=5.0, size=exp.screen.size)

with ButtonPress():
    button = Button(text="Click to continue", size=(exp.screen.width / 4,
                                                    exp.screen.height / 8))
    slider = Slider(min=exp.screen.left, max=exp.screen.right,
                    top=button.bottom, blocking=False)
    rect = Rectangle(color="purple", width=50, height=50,
                     center_top=exp.screen.left_top, blocking=False)
    rect.animate(center_x=lambda t, initial: slider.value, blocking=False)
    ti = TextInput(text="EDIT!", top=slider.bottom, blocking=False)
    MouseCursor()
label = Label(text=ti.text, duration=5.0, font_size=50, color="white")
Done(label)
Debug(label_disappear_time=label.disappear_time)

Ellipse(color="white", width=100, height=100)
with UntilDone():
    with Parallel():
        BackgroundColor("blue", duration=6.0)
        with Serial():
            Wait(1.0)
            BackgroundColor("green", duration=2.0)
        with Serial():
            Wait(2.0)
            BackgroundColor("red", duration=2.0)
        with Serial():
            Wait(3.0)
            BackgroundColor("yellow", duration=2.0)

rect = Rectangle(color="purple", width=50, height=50)
with UntilDone():
    Wait(1.0)
    rect.center = exp.screen.right_top
    Wait(1.0)
    rect.center = exp.screen.right_bottom
    Wait(1.0)
    rect.center = exp.screen.left_top
    #Screenshot()
    Wait(1.0)
    #rect.center = exp.screen.left_bottom
    rect.update(center=exp.screen.left_bottom, color="yellow")
    Wait(1.0)
    #rect.center = exp.screen.center
    rect.update(center=exp.screen.center, color="purple")
    Wait(1.0)
    rect.slide(center=exp.screen.right_top, duration=2.0)
    rect.slide(center=exp.screen.right_bottom, duration=2.0)
    rect.slide(center=exp.screen.left_top, duration=2.0)
    rect.slide(center=exp.screen.left_bottom, duration=2.0)
    rect.slide(center=exp.screen.center, duration=2.0)



with ButtonPress():
    Button(text="Click to continue", size=(exp.screen.width / 4,
                                           exp.screen.height / 4))
    MouseCursor()
with Meanwhile():
    Triangle(points=[0, 0, 500, 500, 0, 500],
             color=(1.0, 1.0, 0.0, 0.5))

bez = Bezier(segments=200, color="yellow", loop=True,
             points=[0, 0, 200, 200, 200, 100, 100, 200, 500, 500])
with UntilDone():
    bez.slide(points=[200, 200, 0, 0, 500, 500, 200, 100, 100, 200],
              color="blue", duration=5.0)
    bez.slide(points=[500, 0, 0, 500, 600, 200, 100, 600, 300, 300],
              color="white", duration=5.0)

ellipse = Ellipse(right=exp.screen.left,
                  center_y=exp.screen.center_y, width=25, height=25,
                  angle_start=90.0, angle_end=460.0,
                  color=(1.0, 1.0, 0.0), name="Pacman")
with UntilDone():
    with Parallel(name="Pacman motion"):
        ellipse.slide(left=exp.screen.right, duration=8.0, name="Pacman travel")
        ellipse.animate(
            angle_start=lambda t, initial: initial + (cos(t * 8) + 1) * 22.5,
            angle_end=lambda t, initial: initial - (cos(t * 8) + 1) * 22.5,
            duration=8.0, name="Pacman gobble")

with BoxLayout(width=500, height=500, top=exp.screen.top, duration=4.0):
    rect = Rectangle(color=(1.0, 0.0, 0.0, 1.0), pos=(0, 0), size_hint=(1, 1), duration=3.0)
    Rectangle(color="#00FF00", pos=(0, 0), size_hint=(1, 1), duration=2.0)
    Rectangle(color=(0.0, 0.0, 1.0, 1.0), pos=(0, 0), size_hint=(1, 1), duration=1.0)
    rect.slide(color=(1.0, 1.0, 1.0, 1.0), duration=3.0)

with Loop(range(3)):
    Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 0.0, 0.0, 1.0),
              duration=1.0)
    Rectangle(x=50, y=50, width=50, height=50, color=(0.0, 1.0, 0.0, 1.0),
              duration=1.0)
    Rectangle(x=100, y=100, width=50, height=50, color=(0.0, 0.0, 1.0, 1.0),
              duration=1.0)

with Parallel():
    label = Label(text="SMILE!", duration=4.0, center_x=100, center_y=100,
                  font_size=50)
    label.slide(center_x=400, center_y=400, font_size=100, duration=4.0)
    Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 0.0, 0.0, 1.0),
              duration=3.0)
    Rectangle(x=50, y=50, width=50, height=50, color="lime",
              duration=2.0)
    Rectangle(x=100, y=100, width=50, height=50, color=(0.0, 0.0, 1.0, 1.0),
              duration=1.0)

with Loop(range(3)):
    Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 1.0, 1.0, 1.0),
              duration=1.0)
    #NOTE: This will flip between iterations, but the rectangle should remain on screen continuously.

Wait(1.0)
Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 1.0, 1.0, 1.0),
          duration=0.0)  #NOTE: This should flip once but display nothing
Wait(1.0)

Wait(1.0)
with Meanwhile():
    Rectangle(x=50, y=50, width=50, height=50, color=(0.0, 1.0, 0.0, 1.0))

rect = Rectangle(x=0, y=0, width=50, height=50, color="brown")
with UntilDone():
    rect.animate(x=lambda t, initial: t * 50, y=lambda t, initial: t * 25,
                 duration=5.0)
    with Meanwhile():
        Rectangle(x=50, y=50, width=50, height=50, color=(0.5, 0.5, 0.5, 1.0))
    with Parallel():
        rect.animate(color=lambda t, initial: (1.0, 1.0 - t / 5.0, t / 5.0, 1.0),
                     duration=5.0)
        rect.animate(height=lambda t, initial: 50.0 + t * 25, duration=5.0)
    Wait(1.0)
    rect.animate(
        height=lambda t, initial: (initial * (1.0 - t / 5.0) +
                                   25 * (t / 5.0)),
        duration=5.0, name="shrink vertically")
    rect.slide(color=(0.0, 1.0, 1.0, 1.0), duration=10.0, name="color fade")
    with Meanwhile():
        rect.animate(x=lambda t, initial: initial + sin(t * 4) * 100,
                     name="oscillate")
    ellipse = Ellipse(x=75, y=50, width=50, height=50,
                      color="orange")
    with UntilDone():
        rect.slide(color="pink", x=0, y=0,
                   width=100, height=100, duration=5.0)
        ellipse.slide(color=("orange", 0.0), duration=5.0)
        rect.slide(color=("pink", 0.0), duration=5.0)
img = Image(source="face-smile.png", size=(10, 10), allow_stretch=True,
            keep_ratio=False, mipmap=True)
with UntilDone():
    img.slide(size=(100, 200), duration=5.0)

Wait(2.0)
exp.run(trace=False)
