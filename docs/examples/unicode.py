################################################################################
#
# unicode.py
#
# Shows how to handle displaying unicode with a Label.
#
#
################################################################################

# Load all the states
from smile.common import *

# Create an experiment
exp = Experiment()

# Initial wait
Wait(1.0)

# Show a label
Label(text=chr(10025) + u" Unicode " + u"\u2729",
      font_size=64, font_name='DejaVuSans')
with UntilDone():
    KeyPress()

Wait(1.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
