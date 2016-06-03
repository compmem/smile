#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


# Load the common states
from smile.common import *

# create an experiment
exp = Experiment()

# initial wait
Wait(1.0)

# show above and below center
Wait(2.)
with Meanwhile():
    with Parallel():
        a = Label(text='Above', center_bottom=exp.screen.center)
        b = Label(text='Below', center_top=exp.screen.center)
        c = Label(text='Way Below', center_top=(b.center_x, b.bottom-100))

# Show Labels next to each other
Wait(3.)
with Meanwhile():
    with Parallel():
        a = Label(text='Middle', center_x=exp.screen.center_x)
        b = Label(text='Right', left=a.right+10 )
        c = Label(text='Left', right=a.left-10)

# Use a Layout to plot things in the layout,
# not the experiment window
Wait(3.)
with Meanwhile():
    with FloatLayout(center_x=exp.screen.center_x + 50, width=300, height=200) as fl:
        with Parallel():
            a = Label(text='Above', center_bottom=fl.center)
            b = Label(text='Below', center_top=fl.center)
            c = Label(text='Way Below',center_x=fl.center_x bottom=fl.bottom)


Wait(1.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
