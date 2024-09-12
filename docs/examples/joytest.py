#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from smile.common import *
from smile.joystick import JoyPress, JoyAxesToPolar, JoyAxis, JoyButton
import math


# set up an experiment
exp = Experiment()

Wait(0.5)

# Create references to the joystick vals
radius0, theta0 = JoyAxesToPolar(0, 1, scaled=True)
radius1, theta1 = JoyAxesToPolar(3, 4, scaled=True)

# button info
base_color = (.1, .1, .1, 1.0)
pressed_color = (.1, .1, .8, 1.0)

with Parallel():
    buttons = {}
    buttons[0] = Rectangle(color=base_color,
                           left_bottom=(exp.screen.center_x-100*2,
                                         exp.screen.center_y))
    buttons[1] = Rectangle(color=base_color,
                           left_bottom=buttons[0].right_bottom)
    buttons[2] = Rectangle(color=base_color,
                           left_bottom=buttons[1].right_bottom)
    buttons[3] = Rectangle(color=base_color,
                           left_bottom=buttons[2].right_bottom)
    buttons[4] = Rectangle(color=base_color,
                           left_top=buttons[0].left_bottom)
    buttons[5] = Rectangle(color=base_color,
                           left_bottom=buttons[4].right_bottom)
    buttons[6] = Rectangle(color=base_color,
                           left_bottom=buttons[5].right_bottom)
    buttons[7] = Rectangle(color=base_color,
                           left_bottom=buttons[6].right_bottom)
    for i in buttons.keys():
        Label(text=str(i), center=buttons[i].center)
            
    el = Ellipse(width=200, height=200, color='green', bottom=buttons[0].top)
    pnt = Ellipse(width=50, height=50, color='white', center=el.center)
    lbl_radius0 = Label(bottom=el.top, text='0.0')
    lbl_theta0 = Label(bottom=lbl_radius0.top, text='0.0')
with UntilDone():
    KeyPress()
    with Meanwhile():
        with Parallel():
        # I'm not sure why this won't work in a loop
        #for i in buttons.keys():
        #    buttons[i].animate(color=lambda t, initial:
        #                       Ref.cond(JoyButton(i), pressed_color, base_color))
            buttons[0].animate(color=lambda t, initial:
                               Ref.cond(JoyButton(0), pressed_color, base_color))
            buttons[1].animate(color=lambda t, initial:
                               Ref.cond(JoyButton(1), pressed_color, base_color))
            buttons[2].animate(color=lambda t, initial:
                               Ref.cond(JoyButton(2), pressed_color, base_color))
            buttons[3].animate(color=lambda t, initial:
                               Ref.cond(JoyButton(3), pressed_color, base_color))
            buttons[4].animate(color=lambda t, initial:
                               Ref.cond(JoyButton(4), pressed_color, base_color))
            buttons[5].animate(color=lambda t, initial:
                               Ref.cond(JoyButton(5), pressed_color, base_color))
            buttons[6].animate(color=lambda t, initial:
                               Ref.cond(JoyButton(6), pressed_color, base_color))
            buttons[7].animate(color=lambda t, initial:
                               Ref.cond(JoyButton(7), pressed_color, base_color))

            # axis tracking
            lbl_radius0.animate(text=lambda t, initial: Ref(str, radius0))
            lbl_theta0.animate(text=lambda t, initial: Ref(str, theta0))

            pnt.animate(center=lambda t, initial:
                        (el.center_x + JoyAxis(0)*el.width/2,
                         el.center_y - JoyAxis(1)*el.width/2))
Wait(.5)

if __name__ == '__main__':

    exp.run()
