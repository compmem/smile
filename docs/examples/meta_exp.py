#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# load all the states
from smile.common import *

# create an experiment
exp = Experiment()

# load this code
code = open(__file__, 'r').read()
code = code[code.find('# load'):]

# Show the image and code
with Parallel():
    Image(source='face-smile.png',
          center_x=exp.screen.center_x+exp.screen.width/4)
    CodeInput(left_top=exp.screen.left_top,
              width=exp.screen.width/2,
              height=exp.screen.height,
              text=code)
with UntilDone():
    # Take a screenshot after a keypress
    kp = KeyPress()
    Screenshot(filename='meta_exp.png')
    Wait(1.0)

if __name__ == '__main__':
    exp.run()
