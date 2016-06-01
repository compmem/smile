################################################################################
#
# dynamic_dot_box.py
#
# This experiment was to show how to test the DynamicDotBox WidgetState. A
# DynamicDotBox will show the same number of dots every time, but will randomly
# generate the position of each dot every screen interval.
#
#
################################################################################


# Load all the states
from smile.common import *

# Create an experiment
exp = Experiment()

with Loop(['cyan', 'blue', 'pink', 'green']) as col:

    with Parallel():
        # Display some DynamicDotBoxes
        ddb1 = DynamicDotBox(color=col.current,
                             center_x=exp.screen.center_x-200,
                             num_dots=40, size=(400, 400))
        ddb2 = DynamicDotBox(color=col.current,
                             center_x=exp.screen.center_x+200,
                             num_dots=80, size=(400, 400))

    # Run the above state until a keypress happens.
    with UntilDone():
        kp = KeyPress()

    Done(ddb1)
    # Show all the info about the states in the command line
    Debug(appear_time_1=ddb1.db.appear_time,
          appear_time_2=ddb2.db.appear_time,
          disappear_time_1=ddb1.db.disappear_time,
          disappear_time_2=ddb2.db.disappear_time,
          num_dots1=ddb1.db.num_dots,
          num_dots2=ddb2.db.num_dots,
          press_time = kp.press_time,
          dis_diff = ddb1.db.disappear_time['time'] - kp.press_time['time'])

    Wait(1.0)


# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run(trace=False)
