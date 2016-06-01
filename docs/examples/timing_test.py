################################################################################
#
# timing_test.py
#
# This is what was used to show that SMILE's timing was showing up correctly in
# the logs. We showed flashes on the screen at varrying speeds, anything below
# the framerate in duration would be shown at the framerate.
#
#
################################################################################


# Load all the states
from smile.common import *
import random

# Create an experiment
exp = Experiment(background_color='black')

# Set the dur and isi for each trial
trials = [{'dur':d,'isi':i}
          for d,i in zip([.005,.010,1.0/60.0,.020,.050,.100,.200,.500,1.0],
                         [.005,.010,1.0/60.0,.020,.050,.100,.200,.500,1.0])]

# Add in a bunch of fast switches
trials = [{'dur':.005,'isi':.005}]*10 + trials

# Double length, reverse, and repeat 50 times
trials = trials*2
trials_copy = trials[:]
trials_copy.reverse()
trials.extend(trials_copy)
trials = trials*50

# Initial Wait
Wait(1.0)

# Main Loop to loop through all the trials created above
with Loop(trials) as trial:
    # Wait the isi
    reset = Wait(trial.current['isi'])

    # Turn it on
    bg = BackgroundColor(color=(1,1,1,1.0))
    with UntilDone():
        Wait(until=bg.on_screen)

        # Reset clock to ensure flip-level timing
        ResetClock(bg.appear_time['time'])

        # Wait the dur
        Wait(trial.current['dur'])

    # Log the on and off times
    Wait(until=bg.disappear_time)
    ResetClock(bg.disappear_time['time'])
    Log(name="flipping",
        on=bg.appear_time,
        off=bg.disappear_time,
        dur=trial.current['dur'],
        isi=trial.current['isi'])

Wait(1.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
