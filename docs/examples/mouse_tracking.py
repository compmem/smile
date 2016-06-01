################################################################################
#
# mouse_tracking.py
#
# This experiment will show you how to use MouseWithin and MousePos
# and MouseCursor.
#
#
################################################################################


# Load all the states
from smile.common import *

# Set up an experiment
exp = Experiment()


# Initial Wait
Wait(1.0)


# This Parallel will show 2 rectangles and wait until
# your cursor is in the one that is on the bottom
with Parallel():
    # Place a rectangle in the bottom-middle of the screen
    rect = Rectangle(bottom=exp.screen.center_bottom,
                     color='white')
    # Place a rectangle in the top of the screen
    r2 = Rectangle(bottom=rect.top, color='purple')
    # Show the Mouse, required to show the mouse during
    # any experiment
    MouseCursor()
# Do the above state Until the below states leave
with UntilDone():
    # Wait UNTIL the mouse is within the rect
    Wait(until=MouseWithin(rect))
    # While we are waiting for the mouse, animate the other rectangle
    with Meanwhile():
        r2.animate(center_x=lambda t, initial: MousePos()[0])


# This Parallel will show 2 rectangles, choice_A and chioce_B,
# one at the top left and one at the top right. It will also show and
# record the mouse position.
with Parallel():
    choice_A = Rectangle(left_top=(exp.screen.left + 100, exp.screen.top - 100))
    choice_B = Rectangle(right_top=(exp.screen.right - 100, exp.screen.top - 100))
    mrec = Record(mouse_pos=MousePos())
    MouseCursor()
# The above state will run until the mouse goes within either rectangle
# and display which rectangle it was in.
with UntilDone():
    # Create MouseWithin Ref A
    mwa = MouseWithin(choice_A)
    # Create MouseWithin Ref B
    mwb = MouseWithin(choice_B)
    # Wait Until wither Ref is true
    w = Wait(until= mwa | mwb)
    # If the first mouse within is true
    with If(mwa):
        Debug(choice='A',
              rt=w.event_time['time'] - choice_A.appear_time['time'])
    # Else the second mouse within is true
    with Else():
        Debug(choice='B',
              rt=w.event_time['time'] - choice_B.appear_time['time'])


# If this was run in a command line, run the experiment
if __name__ == '__main__':

    exp.run()
