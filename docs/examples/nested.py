################################################################################
#
# nested.py
#
# This experiment shows an example of how nested Flow States can change the way
# your experiment can run.
#
#
################################################################################


# load all the states
from smile.common import *

# create an experiment
exp = Experiment()

# initial wait
Wait(1.0)

# Present two stim with embedded If
with Loop(range(10)) as trial:
    # Show a Label with X or O depending on
    # which iteration of the loop it is.
    # In Parallel, display a : and then a !
    # at the same time as the X and O.
    with Parallel():
        with If((trial.current % 2) == 0):
            Label(text='      X', duration=2.0)
        with Else():
            Label(text='O      ', duration=2.0)
        with Serial():
            Label(text='   :   ', duration=1.0)
            Label(text='   !   ', duration=1.0)

Wait(1.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
