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

# Create an experiment
exp = Experiment()

# Initial wait
Wait(1.0)

# Define some items
block = [str(i) for i in range(5)]

with Parallel():
    # Show placement and bounding boxes
    txt = Label(text='+', font_size=48)
    img = Image(source='face-smile.png',
                bottom=txt.top)
    rect = Rectangle(size=txt.size,
                     color=('cyan', .3))
    rect_img = Rectangle(size=img.size, center=img.center,
                         color=('red', .3))
with UntilDone():
    # Loop over items
    with Loop(block) as trial:
        # Show the label
        num = Label(text=trial.current,
                    top=txt.bottom,
                    duration=1.0, font_size=48)

        # Debug to show placement locations
        Debug(txt_size=txt.size,
              txt_bottom=txt.bottom,
              txt_top=txt.top,
              num_size=num.size,
              num_top=num.top,
              img_size=img.size,
              img_bottom=img.bottom)
        Wait(.5)

Wait(2.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
