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

# Create the experiment
exp = Experiment()

# Prepare them
Label(text="Get Ready...", font_size=40, duration=1.0)

# Pause a moment
Wait(.5)

# Collect responses for 10 seconds
fk = FreeKey(Label(text='??????', font_size=40),
             max_duration=10.0)

# Show one way to log responses
Log(fk.responses, name='free_key_test')

# Debug the output to screen, too
Debug(responses=fk.responses)

# Wait sec
Wait(1.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
