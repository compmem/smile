#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


# Load all the states
from smile.common import *

# Create an experiment
exp = Experiment()

# Load this code
code = open(__file__, 'r').read()
code = code[code.find('# load'):]

# Show the image and code
with Parallel():
    # Pass in a source image, and
    # display it on the right side of
    # the screen
    Image(source='face-smile.png',
          center_x=exp.screen.center_x+exp.screen.width/4)

    # Pass in text, display the code on the left side
    # of the screen.
    CodeInput(left_top=exp.screen.left_top,
              width=exp.screen.width/2,
              height=exp.screen.height,
              text=code)

with UntilDone():
    # Take a screenshot after a keypress
    kp = KeyPress()
    Screenshot(filename='meta_exp.png')
    Wait(1.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
