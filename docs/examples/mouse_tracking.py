#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from smile.common import *

# set up an experiment
exp = Experiment()

Wait(1.0)

with Parallel():
    rect = Rectangle(bottom=exp.screen.center_bottom,
                     color='white')
    r2 = Rectangle(bottom=rect.top, color='purple')
with UntilDone():
    Wait(until=MouseWithin(rect))
    with Meanwhile():
        r2.animate(center_x=lambda t, initial: MousePos()[0])

with Parallel():
    choice_A = Rectangle(left_top=(exp.screen.left + 100, exp.screen.top - 100))
    choice_B = Rectangle(right_top=(exp.screen.right - 100, exp.screen.top - 100))
    mrec = Record(mouse_pos=MousePos())
with UntilDone():
    mwa = MouseWithin(choice_A)
    mwb = MouseWithin(choice_B)
    w = Wait(until= mwa | mwb)
    with If(mwa):
        Debug(choice='A',
              rt=w.event_time['time'] - choice_A.appear_time['time'])
    with Else():
        Debug(choice='B',
              rt=w.event_time['time'] - choice_B.appear_time['time'])


if __name__ == '__main__':

    exp.run()
