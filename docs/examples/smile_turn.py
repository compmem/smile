################################################################################
#
# smile_turn.py
#
# In this experiment we show you a different way to spin things in
# rotation_test.py You are able to spin a whole Scatter layout, and anything
# inside it aswell.
#
# NOTE : If you put a button inside a scatter layout, or if you are trying to
# idenfity weather or not a mouse is within a rotated widget inside a scatter
# plot, it will not work correctly. ScatterLayout will rotate the image before
# it is drawn to the buffer, but not change the postion or rotation of the
# widgets themselves.
#
################################################################################

# Load all the states
from smile.common import *

# Create an experiment
exp = Experiment()


with Parallel():
    # Set initially to white (need to use Rectangle b/c it can "slide"
    bg = Rectangle(color='white', size=exp.screen.size)

    # Put items in a scatter for rotation
    with ScatterLayout(do_rotation=False,
                       do_translation=False,
                       do_scale=False,
                       center=exp.screen.center,
                       rotation=17) as sl:
        # Must put at 0,0 in the scatter
        img = Image(source='face-smile.png',
                    color=(1, 1, 1, 0),
                    x=0, y=0)

        # Must put at 0,0
        rect = Rectangle(color=('red', .2),
                         size=sl.size,
                         x=0, y=0)

    lbl = Label(text='SMILE!', font_size=12, color=('white', 0.0))


# Run the above state until that which is within the UntilDone leaves
with UntilDone():
    Wait(1.0)
    # Change the size of the ScatterLayout to the same
    # size as the Image
    sl.size = img.size
    # Change the size of the rectangle to the same size of
    # the ScatterLayout over 1 second
    rect.slide(size=sl.size, duration=1.0)
    Debug(width=sl.width, x=sl.x, center1=exp.screen.center,
          center2=sl.center, isize=img.size, itop=img.top)
    # Change the color of the background rectangle,
    # the color of the Image, the color and position of
    # the Label, and rotate the ScatterLayout using the
    # rotation parameter
    with Parallel():
        bg.slide(color='black', duration=4.0)
        img.slide(color=(1., 1., 1., 1.), duration=4.0)
        lbl.slide(color=('white', 1.0),
                  bottom=exp.screen.top-100,
                  font_size=64,
                  duration=5.0)
        sl.slide(rotation=360,
                 duration=6.0)
    Wait(2.0)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
