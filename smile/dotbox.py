#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from .video import WidgetState, BlockingFlips, NonBlockingFlips
from .state import Wait, Meanwhile, Parallel, Loop, Subroutine
from .state import If, Else
from .ref import jitter

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics import Point, Color, Rectangle

import random


@WidgetState.wrap
class DotBox(Widget):
    """Display a box filled with random square dots.

    Parameters
    ----------
    num_dots : integer
        Number of dots to draw
    pointsize : integer
        Radius of dot (see `Point`)
    color : tuple or string
        Color of dots
    backcolor : tuple or string
        Color of background rectangle

    """
    color = ListProperty([1, 1, 1, 1])
    backcolor = ListProperty([0, 0, 0, 0])
    #num_dots = NumericProperty(10, force_dispatch=True)
    num_dots = NumericProperty(10)
    pointsize = NumericProperty(5)

    def __init__(self, **kwargs):
        super(type(self), self).__init__()

        self._color = None
        self._backcolor = None
        self._points = None

        self.bind(color=self._update_color,
                  backcolor=self._update_backcolor,
                  pos=self._update,
                  size=self._update,
                  num_dots=self._update_locs)
        self._update_locs()

    def _update_color(self, *pargs):
        self._color.rgba = self.color

    def _update_backcolor(self, *pargs):
        self._backcolor.rgba = self.backcolor

    def _update_locs(self, *pargs):
        self._locs = [random.random()
                      for i in range(int(self.num_dots)*2)]
        self._update()

    def _update_pointsize(self, *pargs):
        self._points.pointsize = self.pointsize

    def _update(self, *pargs):
        # calc new point locations
        bases = (self.x+self.pointsize, self.y+self.pointsize)
        scales = (self.width-(self.pointsize*2),
                  self.height-(self.pointsize*2))
        points = [bases[i % 2]+scales[i % 2]*loc
                  for i, loc in enumerate(self._locs)]

        # draw them
        self.canvas.clear()
        with self.canvas:
            # set the back color
            self._backcolor = Color(*self.backcolor)

            # draw the background
            Rectangle(size=self.size,
                      pos=self.pos)

            # set the color
            self._color = Color(*self.color)

            # draw the points
            self._points = Point(points=points, pointsize=self.pointsize)


@Subroutine
def DynamicDotBox(self, duration=None,
                  update_interval=jitter(1/20., (1/10.)-(1/20.)),
                  **dotbox_args):
    """Display random dots that update at an interval.

    Parameters
    ----------
    duration : float or None
        Duration to show the random dots.
    update_interval : float
        How often to update the random dots. Default is to jitter
        between 10 and 20 Hz.
    dotbox_args : kwargs
        See the DotBox for any kwargs options to control the DotBox

    Note: You can access the dotbox via the `db` attribute of the
    subroutine.

    Examples
    --------
    Display a dynamic dot box with 40 dots for 3 seconds:

    ::
        DynamicDotBox(size=(500, 500), num_dots=40, duration=3.0)


    Display two dynamic dot boxes side-by-side until a key press:
    ::

        with Parallel():
            ddb1 = DynamicDotBox(center_x=exp.screen.center_x-200,
                                 num_dots=40, size=(400, 400))
            ddb2 = DynamicDotBox(center_x=exp.screen.center_x+200,
                                 num_dots=80, size=(400, 400))
        with UntilDone():
            kp = KeyPress()

        Log(appear_time=ddb1.db.appear_time)

    """
    # show the dotbox
    with Parallel():
        db = DotBox(duration=duration, **dotbox_args)
        self.db = db
    with Meanwhile():
        # redraw the dots
        self.start_dots = db.num_dots
        with Loop() as l:
            Wait(duration=update_interval)
            # hack to make 1.8 work
            with If((l.i % 2)==0):
                self.ndots = self.start_dots + .01
            with Else():
                self.ndots = self.start_dots
            #db.update(save_log=False, **dotbox_args)
            db.update(save_log=False, num_dots=self.ndots)


if __name__ == '__main__':

    from .experiment import Experiment
    from .state import UntilDone, Serial

    exp = Experiment(background_color="#330000")

    Wait(1.0)

    DotBox(duration=2.0, backcolor='blue')

    db = DotBox(color='red')
    with UntilDone():
        db.slide(center=exp.screen.right_top, duration=2.0)
        db.slide(center=exp.screen.left_top, duration=2.0)
        db.slide(center=exp.screen.center, duration=1.0)

    db2 = DotBox(color='red', backcolor=(.1, .1, .1, .5))
    with UntilDone():
        with Parallel():
            with Serial():
                db2.slide(color='blue', duration=1.0)
                db2.slide(color='olive', duration=1.0)
                db2.slide(color='orange', duration=1.0)
                db2.slide(pointsize=20, duration=1.0)
            db2.slide(size=(400, 400), duration=4.0)

    db3 = DotBox(color='green', backcolor='purple', size=(400, 400))
    with UntilDone():
        db3.slide(num_dots=50, duration=3.0)

    Wait(2.0)
    exp.run(trace=False)

