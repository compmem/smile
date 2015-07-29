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

import kivy_overrides
from state import State
from ref import val, Ref
from clock import clock
import kivy.graphics
import kivy.uix.image
import kivy.uix.label
import kivy.uix.widget
from kivy.properties import StringProperty, ListProperty, NumericProperty  #???


class RectangleWidget(kivy.uix.widget.Widget):
    color = ListProperty([1.0, 1.0, 1.0, 1.0])

    def __init__(self, *pargs, **kwargs):
        super(RectangleWidget, self).__init__(*pargs, **kwargs)
        with self.canvas:
            self._color = kivy.graphics.Color(*self.color)
            self._rectangle = kivy.graphics.Rectangle(pos=self.pos,
                                                      size=self.size)
        self.bind(pos=self.redraw, size=self.redraw, color=self.redraw)

    def redraw(self, *pargs):
        self._color.rgba = self.color
        self._rectangle.pos = self.pos
        self._rectangle.size = self.size


class EllipseWidget(kivy.uix.widget.Widget):
    color = ListProperty([1.0, 1.0, 1.0, 1.0])
    segments = NumericProperty(180)
    angle_start = NumericProperty(0)
    angle_end = NumericProperty(360)

    def __init__(self, *pargs, **kwargs):
        super(EllipseWidget, self).__init__(*pargs, **kwargs)
        with self.canvas:
            self._color = kivy.graphics.Color(*self.color)
            self._rectangle = kivy.graphics.Ellipse(
                pos=self.pos, size=self.size, segments=self.segments,
                angle_start=self.angle_start, angle_end=self.angle_end)
        self.bind(pos=self.redraw, size=self.redraw, color=self.redraw,
                  segments=self.redraw, angle_start=self.redraw,
                  angle_end=self.redraw)

    def redraw(self, *pargs):
        self._color.rgba = self.color
        self._rectangle.pos = self.pos
        self._rectangle.size = self.size
        self._rectangle.segments = self.segments
        self._rectangle.angle_start = self.angle_start
        self._rectangle.angle_end = self.angle_end


class Widget(State):
    @staticmethod
    def factory(widget_class):
        def new_factory(*pargs, **kwargs):
            widget = Widget(widget_class, *pargs, **kwargs)
            widget.override_instantiation_context()
            return widget
        return new_factory

    def __init__(self, widget_class, duration=None, parent=None, save_log=True,
                 name=None, index=0, **params):
        if name is None:
            name = widget_class.__name__
        super(Widget, self).__init__(parent=parent, 
                                     duration=duration, 
                                     save_log=save_log,
                                     name=name)

        self.appear_time = None
        self.disappear_time = None
        self.appear_video = None
        self.disappear_video = None
        self.widget_class = widget_class
        self.index = index
        self.widget = None
        self.param_names = params.keys()
        self.params = None
        for name, value in params.items():
            setattr(self, name, value)

        # set the log attrs
        self.log_attrs.extend(['appear_time',
                               'disappear_time'])
        self.log_attrs.extend(self.param_names)

    def get_updated_param(self, name):
        return getattr(self.widget, name)

    def get_updated_param_ref(self, name):
        return Ref(gfunc=self.get_updated_param, gfunc_args=(name,))

    def set_appear_time(self, appear_time):
        self.appear_time = appear_time

    def set_disappear_time(self, disappear_time):
        self.disappear_time = disappear_time

    def _enter(self):
        self.appear_time = None
        self.disappear_time = None
        self.appear_video = None
        self.disappear_video = None
        self.on_screen = False

        self.params = {name : val(getattr(self, name)) for
                       name in self.param_names}

        self.appear_video = self.exp.app.schedule_video(
            self.appear, self.start_time, self.set_appear_time)
        #clock.schedule(self.appear, event_time=self.start_time)
        if self.end_time is not None:
            self.disappear_video = self.exp.app.schedule_video(
                self.disappear, self.end_time, self.set_disappear_time)

    def appear(self):
        self.claim_exceptions()
        self.appear_video = None
        self.on_screen = True
        self.widget = self.widget_class(**self.params)
        self.exp.app.wid.add_widget(self.widget, index=self.index)
        clock.schedule(self.leave)

    def disappear(self):
        self.claim_exceptions()
        self.disappear_video = None
        self.on_screen = False
        self.exp.app.wid.remove_widget(self.widget)
        self.widget = None
        clock.schedule(self.finalize)

    def cancel(self, cancel_time):
        if self.active:
            clock.schedule(self.leave)
            if cancel_time <= self.start_time:
                if self.appear_video is not None:
                    self.exp.app.cancel_video(self.appear_video)
                self.appear_video = None
                if self.disappear_video is not None:
                    self.exp.app.cancel_video(self.disappear_video)
                if self.on_screen:
                    self.disappear_video = self.exp.app.schedule_video(
                        self.disappear, clock.now(), self.set_disappear_time)
                else:
                    self.disappear_video = None
                    clock.schedule(self.finalize)
                self.end_time = self.start_time
            elif self.end_time is None or cancel_time < self.end_time:
                if self.disappear_video is not None:
                    self.exp.app.cancel_video(self.disappear_video)
                self.disappear_video = self.exp.app.schedule_video(
                    self.disappear, cancel_time, self.set_disappear_time)
                self.end_time = cancel_time

    def live_change(self, **params):
        if self.on_screen:
            for name, value in params.items():
                setattr(self.widget, name, val(value))

    def animate(self, duration=None, parent=None, save_log=True, name=None,
                **anim_params):
        anim = Animate(self, duration=duration, parent=parent, name=name,
                       save_log=save_log, **anim_params)
        anim.override_instantiation_context()
        return anim

    def slide(self, duration=None, speed=None, accel=None, parent=None,
              save_log=True, name=None, **params):
        def interp(a, b, w):
            if hasattr(a, "__iter__"):
                return [interp(a_prime, b_prime, w) for
                        a_prime, b_prime in
                        zip(a, b)]
            else:
                return a * (1.0 - w) + b * w
        condition = duration is None, speed is None, accel is None
        if condition == (False, True, True):  # simple, linear interpolation
            anim_params = {}
            for param_name, value in params.items():
                def func(t, initial, value=value):
                    return interp(initial, value, t / duration)
                anim_params[param_name] = func
        #TODO: fancier interpolation modes!!!
        else:
            raise ValueError("Invalid combination of parameters.")  #...
        anim = self.animate(duration=duration, parent=parent,
                            save_log=save_log, name=name, **anim_params)
        anim.override_instantiation_context()
        return anim


Image = Widget.factory(kivy.uix.image.Image)  #???
Label = Widget.factory(kivy.uix.label.Label)  #???
Rectangle = Widget.factory(RectangleWidget)
Ellipse = Widget.factory(EllipseWidget)
#...


class Animate(State):
    def __init__(self, target, duration=None, parent=None, save_log=True,
                 name=None, **anim_params):
        super(Animate, self).__init__(duration=duration, parent=parent,
                                      save_log=save_log, name=name)
        self.target = target
        self.anim_params = anim_params
        self.initial_params = None

    def _enter(self):
        self.initial_params = None
        first_update_time = self.start_time + self.exp.app.flip_interval
        clock.schedule(self.update, event_time=first_update_time,
                       repeat_interval=self.exp.app.flip_interval)
        clock.schedule(self.leave)

    def update(self):
        self.claim_exceptions()
        now = clock.now()
        if self.initial_params is None:
            self.initial_params = {
                name : self.target.get_updated_param(name) for
                name in self.anim_params.keys()}
        if self.end_time is not None and now >= self.end_time:
            clock.unschedule(self.update)
            clock.schedule(self.finalize)
            now = self.end_time
        t = now - self.start_time
        params = {name : val(func(t, self.initial_params[name])) for
                  name, func in
                  self.anim_params.items()}
        self.target.live_change(**params)

    def cancel(self, cancel_time):
        if self.active and (self.end_time is None or
                            cancel_time < self.end_time):
            self.end_time = cancel_time



#TODO: Text, DotBox, Image, Movie, Background?

if __name__ == '__main__':
    from experiment import Experiment
    from state import Wait, Loop, Parallel, Meanwhile, UntilDone
    from math import sin

    exp = Experiment()

    Wait(5.0)

    with Loop(range(3)):
        Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 0.0, 0.0, 1.0),
                  duration=1.0)
        Rectangle(x=50, y=50, width=50, height=50, color=(0.0, 1.0, 0.0, 1.0),
                  duration=1.0)
        Rectangle(x=100, y=100, width=50, height=50, color=(0.0, 0.0, 1.0, 1.0),
                  duration=1.0)

    #Wait(1.0)
    #Image(source="face-smile.png", duration=3.0)
    #Label(text="SMILE!", duration=3.0, center_x=100, center_y=100)

    with Parallel():
        Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 0.0, 0.0, 1.0),
                  duration=3.0)
        Rectangle(x=50, y=50, width=50, height=50, color=(0.0, 1.0, 0.0, 1.0),
                  duration=2.0)
        Rectangle(x=100, y=100, width=50, height=50, color=(0.0, 0.0, 1.0, 1.0),
                  duration=1.0)
        Image(source="face-smile.png", duration=4.0, name="Smiling Face")

    with Loop(range(3)):
        Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 1.0, 1.0, 1.0),
                  duration=1.0)
        #NOTE: This will flip between iterations, but the rectangle should remain on screen continuously.

    Wait(1.0)
    Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 1.0, 1.0, 1.0),
              duration=0.0)  #NOTE: This should flip once but display nothing
    Wait(1.0)

    Wait(1.0)
    with Meanwhile():
        Rectangle(x=50, y=50, width=50, height=50, color=(0.0, 1.0, 0.0, 1.0))

    rect = Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 1.0, 0.0, 1.0))
    with UntilDone():
        rect.animate(x=lambda t, initial: t * 50, y=lambda t, initial: t * 25,
                     duration=5.0)
        with Meanwhile():
            Rectangle(x=50, y=50, width=50, height=50, color=(0.5, 0.5, 0.5, 1.0))
        with Parallel():
            rect.animate(color=lambda t, initial: (1.0, 1.0 - t / 5.0, t / 5.0, 1.0),
                         duration=5.0)
            rect.animate(height=lambda t, initial: 50.0 + t * 25, duration=5.0)
        Wait(1.0)
        rect.animate(
            height=lambda t, initial: (initial * (1.0 - t / 5.0) +
                                       25 * (t / 5.0)),
            duration=5.0, name="shrink vertically")
        rect.slide(color=(0.0, 1.0, 1.0, 1.0), duration=10.0, name="color fade")
        with Meanwhile():
            rect.animate(x=lambda t, initial: initial + sin(t * 4) * 100,
                         name="oscillate")
        ellipse = Ellipse(x=75, y=50, width=50, height=50,
                          color=(1.0, 0.5, 0.0, 1.0))
        with UntilDone():
            rect.slide(color=(1.0, 1.0, 1.0, 1.0), x=0, y=0,
                       width=100, height=100, duration=5.0)
            ellipse.slide(color=(0.0, 0.0, 1.0, 0.0), duration=5.0)
            rect.slide(color=(1.0, 1.0, 1.0, 0.0), duration=5.0)

    Wait(5.0)
    exp.run(trace=False)
