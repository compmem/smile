################################################################################
# Dynamic Cirlces Example
#
# This example will show you how to use Parallel.insert(), a function that
# Parallels have that allow you to add states during Experimental Runtime. It
# also shows you how to use MousePress() and some other Flow States.
#
#
################################################################################

# load all the states
from smile.common import *

# create an experiment
exp = Experiment()

# Initial wait
Wait(1.0)

# Placeholder for saving inserted circs
exp.circs = []

# Accept input for 5 seconds
Wait(5.)
with Meanwhile():
    # Put it all in a parallel so we can keep adding stuff
    with Parallel() as p:
        # show the cursor
        MouseCursor()
        with Loop() as l:
            # Wait for a mouse press
            mp = MousePress()
            # Insert everything within to the Parallel above
            with p.insert() as ins:
                # Add a circle with random color
                circ = Ellipse(center=mp.pos, color=(jitter(0, 1),
                                                     jitter(0, 1),
                                                     jitter(0, 1)))
            # Add a reference to the last MousePress that happened
            # to the list of MousePress References
            exp.circs = exp.circs + [ins.first]

# Print out the locs we saved
with Loop(exp.circs, save_log=False) as c:
    Debug(i=c.i,
          center=c.current.center,
          color=c.current.color)
Wait(1.0)


# If this is being run from the command line, run this experiment
if __name__ == '__main__':
    exp.run()
