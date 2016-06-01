################################################################################
#
# constant.py
#
# This experiment was used to show that when showing things one after the
# other during a loop, there is no screen flicker, or any missed frames.
# Displaying a widget will go from one instance to the next as long as there are
# no Waits telling the experiment to pause during iterations of the loop.
#
#
################################################################################


# Load all the states
from smile.common import *

# Create an experiment
exp = Experiment()

# Initial wait
Wait(1.0)

# Define some items
block = [str(i) for i in range(5)]

with Parallel():
    # Show placement and bounding boxes
    txt = Label(text='+', font_size=48)
    img = Image(source='face-smile.png',
                bottom=txt.top)
    rect = Rectangle(size=txt.size,
                     color=('cyan', .3))
    rect_img = Rectangle(size=img.size, center=img.center,
                         color=('red', .3))
with UntilDone():
    # Loop over items
    with Loop(block) as trial:
        # Show the label
        num = Label(text=trial.current,
                    top=txt.bottom,
                    duration=1.0, font_size=48)

        # Debug to show placement locations
        Debug(txt_size=txt.size,
              txt_bottom=txt.bottom,
              txt_top=txt.top,
              num_size=num.size,
              num_top=num.top,
              img_size=img.size,
              img_bottom=img.bottom)
        Wait(.5)

Wait(2.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
