#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# load all the states
from smile import *

# create an experiment
exp = Experiment()

with Parallel():
    # set initially to white (need to use Rectangle b/c it can "slide"
    bg = Rectangle(color='white',size=exp.screen.size)

    # Put items in a scatter for rotation
    with ScatterLayout(do_rotation=False,
                       do_translation=False,
                       do_scale=False,
                       #size=(250,250),
                       center=exp.screen.center,
                       rotation=17) as sl:
        # Must put at 0,0 in the scatter
        img = Image(source='face-smile.png',
                    color=(1,1,1,0),
                    x=0,y=0)
        # Must put at 0,0
        rect = Rectangle(color=('red',.2), size=sl.size, x=0, y=0)

    lbl = Label(text='SMILE!', font_size=12, color=('white',0.0))
with UntilDone():
    Wait(2.0)
    sl.size = img.size
    rect.size = sl.size
    Debug(width=sl.width, x=sl.x, center1=exp.screen.center,
          center2=sl.center, isize=img.size, itop=img.top)
    with Parallel():
        bg.slide(color='black', duration=4.0)
        img.slide(color=(1.,1.,1.,1.), duration=4.0)
        lbl.slide(color=('white',1.0),
                  bottom=exp.screen.top-100,
                  font_size=64,
                  duration=4.0)
        sl.slide(rotation=360,
                 #right=exp.screen.right,
                 duration=6.0)
    Wait(1.0)


if __name__ == '__main__':
    exp.run()
