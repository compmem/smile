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

# Create an experiment
exp = Experiment()

with Parallel():
    # Add the Image and Rectangle
    # (with zero alpha so they are not visible)
    # and start the Image rotated at 359 degrees
    img = Image(source='face-smile.png',
                color=(1, 1, 1, 0),
                rotate=359)
    rect = Rectangle(color=('red', 0.0),
                     size=img.size)

    # Create some circles on top of each other,
    # this shows that you can use pythonic syntax
    # to create states
    circs = [Ellipse(color=col, size=(50, 50))
             for col in ['red', 'green', 'blue', 'purple']]

# Do the above state until the below states are finished
with UntilDone():
    Wait(.5)
    with Parallel():
        # Move the circles out to the side
        [circs[i].slide(center_x=img.right+offset, duration=2.0)
         for i, offset in enumerate([0, 50, 100, 150])]
    with Parallel():
        # Spin the circles
        [circs[i].slide(rotate=360, duration=dur)
         for i, dur in enumerate([2.0, 2.5, 3.0, 3.5])]

        # have the smile image fade in
        img.slide(rotate=0, duration=4.0, color=(1, 1, 1, 1))
    with Parallel():
        # Fade out and spin back the circles
        [circs[i].slide(rotate=0, duration=dur, color=(0, 0, 0, 0))
         for i, dur in enumerate([3.5, 3.0, 2.5, 2.0])]

        # Fade in the rectangle
        rect.slide(color=('red', .3), duration=2)

    # Show that you can simply set the rotate_origin
    rect.rotate_origin = rect.left_bottom
    img.rotate_origin = img.center

    # And slide the origin
    rect.slide(rotate_origin=rect.center, duration=2.0, rotate=90)

    # Rotate the image and rect
    with Parallel():
        img.slide(rotate=360, duration=4.0, center=rect.left_bottom)
        with Serial():
            rect.slide(rotate=45, duration=2.0, bottom=exp.screen.bottom)
            rect.slide(rotate=45, duration=2.0, center=exp.screen.center)

    # Show you can rotate the image by setting a value
    Wait(1.0)
    img.rotate = 270
    Wait(.5)
    img.rotate = 180
    Wait(.5)
    img.rotate = 90
    Wait(.5)
    img.rotate = 0
    Wait(2.0)

# Show two rectangles with different rotation props
with Parallel():
    r1 = Rectangle(left_bottom=exp.screen.center,
                   rotate=45,
                   rotate_origin=exp.screen.center,
                   size=(200, 100),
                   color=('yellow', .5))
    r2 = Rectangle(left_bottom=exp.screen.center,
                   rotate=45,
                   rotate_origin=r1.right_top,
                   size=(200, 100),
                   color=('blue', .5))
with UntilDone():
    # Show where we're heading
    Wait(.5)
    r1.rotate_origin = r1.right_top
    Wait(1.)
    r1.rotate_origin = r1.left_bottom
    Wait(1.0)
    Debug(lb=r1.left_bottom, rt=r1.right_top, ro=r1.rotate_origin)
    # slide there
    r1.slide(rotate_origin=r1.right_top,
             duration=2.0)
    Wait(1.0)
    Debug(lb=r1.left_bottom, rt=r1.right_top, ro=r1.rotate_origin)

# If this was run in a command line, run the experiment
if __name__ == '__main__':
    exp.run()
