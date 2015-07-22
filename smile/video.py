#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import random  #...
import math  #...
from functools import partial

from state import State
from ref import val
from clock import clock
import kivy.graphics


class VisualState(State):
    pass

class StaticVisualState(VisualState):
    def __init__(self, duration=-1, parent=None, save_log=True, name=None):
        # init the parent class
        super(StaticVisualState, self).__init__(interval=-1,
                                                parent=parent, 
                                                duration=duration, 
                                                save_log=save_log,
                                                name=name)

        self.appear_time = None
        self.disappear_time = None
        self.appeared = False
        self.disappeared = False
        self.scheduled = []

        # set the log attrs
        self.log_attrs.extend(['appear_time',
                               'disappear_time'])

    def set_appear_time(self, appear_time):
        self.appear_time = appear_time

    def set_disappear_time(self, disappear_time):
        self.disappear_time = disappear_time
        self.leave()

    def _enter(self):
        self.appear_time = None
        self.disappear_time = None
        self.appeared = False
        self.disappeared = False
        self.scheduled = []

        self.scheduled.append(self.exp.app.schedule_video(
            self.appear, self.start_time, self.set_appear_time))
        if self.end_time is not None:
            self.scheduled.append(self.exp.app.schedule_video(
                self.disappear, self.end_time, self.set_disappear_time))

    def _appear(self):
        raise NotImplementedError

    def appear(self):
        self.claim_exceptions()
        self.appeared = True
        self._appear()

    def _disappear(self):
        raise NotImplementedError

    def disappear(self):
        self.claim_exceptions()
        self.disappeared = True
        self._disappear()

    def _leave(self):
        if not (self.appeared and self.disappeared):
            for video in self.scheduled:
                self.exp.app.cancel_video(video)
        if self.appeared and not self.disappeared:
            self.exp.app.schedule_video(
                self.disappear, clock.now(), self.set_disappear_time)

    def _live_change(self, **kwargs):
        raise NotImplementedError

    def live_change(self, **kwargs):
        self.claim_exceptions()
        self.exp.app.schedule_video(partial(self._live_change, **kwargs),
                                    clock.now())


class DynamicVisualState(VisualState):
    def __init__(self, duration=-1, parent=None, save_log=True):
        pass #...

    #...

class Rectangle(StaticVisualState):
    def __init__(self, x=None, y=None, width=100, height=100,
                 anchor_x='center', anchor_y='center',
                 color=(0.0, 0.0, 0.0, 1.0),
                 duration=-1, parent=None, save_log=True):
        super(Rectangle, self).__init__(duration=duration, parent=parent,
                                        save_log=save_log)

        # set loc to center if none supplied
        #if x is None:
        #    x = Ref(self['exp']['window'],'width')//2  #!!!!!!!!!!!!!!!!!
        self.x = x
        #if y is None:
        #    y = Ref(self['exp']['window'],'height')//2
        self.y = y
        self.anchor_x = anchor_x  #????????
        self.anchor_y = anchor_y  #????????
        self.width = width
        self.height = height
        self.color = color  #TODO: deal with color names, etc...
        #self.group = group  #?????
        self.log_attrs.extend(
            ['x','y','anchor_x','anchor_y','width','height','color'])
        self.kivy_color = None
        self.kivy_shape = None

    def _appear(self):
        with self.exp.app.wid.canvas:
            self.kivy_color = kivy.graphics.Color(*val(self.color))
            self.kivy_shape = kivy.graphics.Rectangle(
                pos=(val(self.x), val(self.y)),
                size=(val(self.width), val(self.height)))

    def _live_change(self, **kwargs):
        if self.kivy_shape is not None:
            if "color" in kwargs:
                self.kivy_color.rgba = kwargs["color"]
            pos = list(self.kivy_shape.pos)
            if "x" in kwargs:
                pos[0] = kwargs["x"]
            if "y" in kwargs:
                pos[1] = kwargs["y"]
            self.kivy_shape.pos = pos
            size = list(self.kivy_shape.size)
            if "width" in kwargs:
                size[0] = kwargs["width"]
            if "height" in kwargs:
                size[1] = kwargs["height"]
            self.kivy_shape.size = size

    def _disappear(self):
        self.exp.app.wid.canvas.remove(self.kivy_color)
        self.exp.app.wid.canvas.remove(self.kivy_shape)
        self.kivy_color = None
        self.kivy_shape = None

#TODO: Text, DotBox, Image, Movie, Background?, Animate

if __name__ == '__main__':
    from experiment import Experiment
    from state import Wait

    exp = Experiment()

    Wait(5.0)
    Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 0.0, 0.0, 1.0),
              duration=1.0)
    Rectangle(x=50, y=50, width=50, height=50, color=(0.0, 1.0, 0.0, 1.0),
              duration=1.0)
    Rectangle(x=100, y=100, width=50, height=50, color=(0.0, 0.0, 1.0, 1.0),
              duration=1.0)
    Wait(5.0, stay_active=True)
    exp.run()
