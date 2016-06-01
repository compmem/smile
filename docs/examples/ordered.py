################################################################################
#
# ordered.py
#
# This experiment shows how you can change the position of a Label with
# slide. slide allows you to change the value of a parameter over a duration.
#
#
################################################################################


# Load all the states
from smile.common import *

# Create an experiment
exp = Experiment()

Wait(1.0)

# Create stims
with Parallel():
    stimB = Label(text="B", x=exp.screen.center_x + 25,
                  font_size=64,
                  color='blue')
    stimF = Label(text="F", x=exp.screen.center_x - 25,
                  font_size=64,
                  color='orange')

# Do the above state until the below states leave
with UntilDone():
    Wait(1.0)
    with Parallel():
        stimB.slide(x=exp.screen.center_x - 25, duration=3.0)
        stimF.slide(x=exp.screen.center_x + 25, duration=3.0)

Wait(1.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
