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
from state import State, get_calling_context
from ref import val, Ref
from clock import clock
import kivy.graphics


class VisualState(State):
    pass

class StaticVisualState(VisualState):
    def __init__(self, duration=None, parent=None, save_log=True, name=None,
                 **params):
        # init the parent class
        super(StaticVisualState, self).__init__(parent=parent, 
                                                duration=duration, 
                                                save_log=save_log,
                                                name=name)

        self.appear_time = None
        self.disappear_time = None
        self.appear_video = None
        self.disappear_video = None
        self.default_params = {}
        self.add_default_params()
        self.params = {}
        for name, default in self.default_params.items():
            setattr(self, name, default)
            self.params[name] = None
        for name, value in params.items():
            if name not in self.params:
                raise ValueError(
                    "Invalid StaticVisualState parameter name %r" % name)
            setattr(self, name, value)

        # set the log attrs
        self.log_attrs.extend(['appear_time',
                               'disappear_time'])
        self.log_attrs.extend(self.params.keys())

    def add_default_params(self):
        pass

    def get_updated_param(self, name):
        return self.params[name]

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

        for name in self.params:
            self.params[name] = val(getattr(self, name))

        self.appear_video = self.exp.app.schedule_video(
            self.appear, self.start_time, self.set_appear_time)
        if self.end_time is not None:
            self.disappear_video = self.exp.app.schedule_video(
                self.disappear, self.end_time, self.set_disappear_time)

    def _appear(self):
        raise NotImplementedError

    def appear(self):
        self.claim_exceptions()
        self.appear_video = None
        self.on_screen = True
        self._appear()
        clock.schedule(self.leave)

    def _disappear(self):
        raise NotImplementedError

    def disappear(self):
        self.claim_exceptions()
        self.disappear_video = None
        self.on_screen = False
        self._disappear()
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

    def _live_change(self):
        raise NotImplementedError

    def live_change(self, **params):
        if not self.on_screen:
            return
        for name, value in params.items():
            if name not in self.params:
                raise ValueError(
                    "Invalid StaticVisualState parameter name %r" % name)
            self.params[name] = val(value)
        self.exp.app.schedule_video(self._live_change)

    def animate(self, duration=None, parent=None, save_log=True, name=None,
                **anim_params):
        anim = Animate(self, duration=duration, parent=parent, name=name,
                       save_log=save_log, **anim_params)
        filename, lineno = get_calling_context(2)
        anim.instantiation_filename = filename
        anim.instantiation_lineno = lineno
        return anim

    def slide(self, duration=None, speed=None, accel=None, parent=None,
              save_log=True, name=None, **params):
        def interp(a, b, w):
            if type(a) in (list, tuple):
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
        filename, lineno = get_calling_context(2)
        anim.instantiation_filename = filename
        anim.instantiation_lineno = lineno
        return anim

    #TODO: animation helper methods


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
            self.initial_params = self.target.params.copy()
        if self.end_time is not None and now >= self.end_time:
            clock.unschedule(self.update)
            clock.schedule(self.finalize)
            now = self.end_time
        t = now - self.start_time
        params = {name : func(t, self.initial_params[name]) for
                  name, func in
                  self.anim_params.items()}
        self.target.live_change(**params)

    def cancel(self, cancel_time):
        if self.active and (self.end_time is None or
                            cancel_time < self.end_time):
            self.end_time = cancel_time


class DynamicVisualState(VisualState):
    def __init__(self, duration=None, parent=None, save_log=True):
        pass #...

    #...


class KivyInstructionVisualState(StaticVisualState):
    _kivy_instruction_class = None

    def __init__(self, *pargs, **kwargs):
        super(KivyInstructionVisualState, self).__init__(*pargs, **kwargs)
        self.kivy_color = None
        self.kivy_shape = None

    def add_default_params(self):
        super(KivyInstructionVisualState, self).add_default_params()
        self.default_params.update({
            "color": None})

    def get_instruction_attributes(self):
        raise NotImplementedError

    def _appear(self):
        with self.exp.app.wid.canvas:
            self.kivy_color = kivy.graphics.Color(*self.params["color"])
            self.kivy_shape = type(self)._kivy_instruction_class(
                **self.get_instruction_attributes())

    def _live_change(self):
        if self.kivy_shape is not None:
            self.kivy_color.rgba = self.params["color"]
            for name, value in self.get_instruction_attributes().items():
                setattr(self.kivy_shape, name, value)

    def _disappear(self):
        self.exp.app.wid.canvas.remove(self.kivy_color)
        self.exp.app.wid.canvas.remove(self.kivy_shape)
        self.kivy_color = None
        self.kivy_shape = None


class Rectangle(KivyInstructionVisualState):
    _kivy_instruction_class = kivy.graphics.Rectangle

    def add_default_params(self):
        super(Rectangle, self).add_default_params()
        self.default_params.update({
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100})

    def get_instruction_attributes(self):
        return {
            "pos": (self.params["x"], self.params["y"]),
            "size": (self.params["width"], self.params["height"])
            }

class Ellipse(KivyInstructionVisualState):
    _kivy_instruction_class = kivy.graphics.Ellipse

    def add_default_params(self):
        super(Ellipse, self).add_default_params()
        self.default_params.update({
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "segments": 180,
            "angle_start": 0,
            "angle_end": 360})

    def get_instruction_attributes(self):
        return {
            "pos": (self.params["x"], self.params["y"]),
            "size": (self.params["width"], self.params["height"]),
            "segments": self.params["segments"],
            "angle_start": self.params["angle_start"],
            "angle_end": self.params["angle_end"]
            }



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

    with Parallel():
        Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 0.0, 0.0, 1.0),
                  duration=3.0)
        Rectangle(x=50, y=50, width=50, height=50, color=(0.0, 1.0, 0.0, 1.0),
                  duration=2.0)
        Rectangle(x=100, y=100, width=50, height=50, color=(0.0, 0.0, 1.0, 1.0),
                  duration=1.0)

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
