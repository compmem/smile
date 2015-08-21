#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from functools import partial
from contextlib import contextmanager
import weakref
import operator

import kivy_overrides
from state import State, CallbackState, Parallel, ParentState
from ref import val, Ref
from clock import clock
import kivy.graphics
import kivy.uix.widget
from kivy.properties import ObjectProperty, ListProperty
import kivy.clock
_kivy_clock = kivy.clock.Clock


color_name_table = {
    # using "basic colors" from
    #   http://www.rapidtables.com/web/color/RGB_Color.htm
    "BLACK": (0.0, 0.0, 0.0, 1.0),
    "WHITE": (1.0, 1.0, 1.0, 1.0),
    "RED": (1.0, 0.0, 0.0, 1.0),
    "LIME": (0.0, 1.0, 0.0, 1.0),
    "BLUE": (0.0, 0.0, 1.0, 1.0),
    "YELLOW": (1.0, 1.0, 0.0, 1.0),
    "CYAN": (0.0, 1.0, 1.0, 1.0),
    "AQUA": (0.0, 1.0, 1.0, 1.0),
    "MAGENTA": (1.0, 0.0, 1.0, 1.0),
    "FUCHSIA": (1.0, 0.0, 1.0, 1.0),
    "SILVER": (0.75, 0.75, 0.75, 1.0),
    "GRAY": (0.5, 0.5, 0.5, 1.0),
    "MAROON": (0.5, 0.0, 0.0, 1.0),
    "OLIVE": (0.5, 0.5, 0.0, 1.0),
    "GREEN": (0.0, 0.5, 0.0, 1.0),
    "PURPLE": (0.5, 0.0, 0.5, 1.0),
    "TEAL": (0.0, 0.5, 0.5, 1.0),
    "NAVY": (0.0, 0.0, 0.5, 1.0)
    }
def normalize_color_spec(spec):
    if isinstance(spec, tuple) or isinstance(spec, list):
        if len(spec) == 3:
            return tuple(spec) + (1.0,)
        elif len(spec) == 4:
            return tuple(spec)
        else:
            raise ValueError(
                "Color spec tuple / list must have length 3 or 4.  Got: %r" %
                spec)
    elif isinstance(spec, str):
        if spec[0] == '#':
            if len(spec) == 7:
                try:
                    return (int(spec[1 : 3], 16) / 255.0,
                            int(spec[3 : 5], 16) / 255.0,
                            int(spec[5 : 7], 16) / 255.0,
                            1.0)
                except ValueError:
                    raise ValueError(
                        "Color spec hex string has invalid characters."
                        "  Got: %r" % spec)
            elif len(spec) == 9:
                try:
                    return (int(spec[1 : 3], 16) / 255.0,
                            int(spec[3 : 5], 16) / 255.0,
                            int(spec[5 : 7], 16) / 255.0,
                            int(spec[7 : 9], 16) / 255.0)
                except ValueError:
                    raise ValueError(
                        "Color spec hex string has invalid characters."
                        "  Got: %r" % spec)
            else:
                raise ValueError(
                    "Color spec hex string wrong length.  Got: %r" % spec)
        else:
            try:
                return color_name_table[spec.upper()]
            except KeyError:
                raise ValueError("Color spec string not valid.  Got: %r" %
                                 spec)


class WidgetState(State):
    layout_stack = []

    @classmethod
    def wrap(cls, widget_class, name=None):
        if not issubclass(widget_class, kivy.uix.widget.Widget):
            raise ValueError(
                "widget_class must be a subclass of kivy.uix.widget.Widget")
        if name is None:
            name = widget_class.__name__
        def __init__(self, *pargs, **kwargs):
            cls.__init__(self, widget_class, *pargs, **kwargs)
        return type(name, (cls,), {"__init__" : __init__})

    def __init__(self, widget_class, duration=None, parent=None, save_log=True,
                 name=None, index=0, layout=None, **params):
        super(WidgetState, self).__init__(parent=parent,
                                          duration=duration,
                                          save_log=save_log,
                                          name=name)

        self.widget_class = widget_class
        self.index = index
        self.widget = None
        self.parent_widget = None
        self.init_param_names = params.keys()
        self.widget_param_names = widget_class().properties().keys()
        self.params = None
        self.issued_param_refs = weakref.WeakValueDictionary()
        for name, value in params.items():
            setattr(self, name, value)
        if layout is None:
            if len(WidgetState.layout_stack):
                self.layout = WidgetState.layout_stack[-1]
            else:
                self.layout = None
        else:
            self.layout = layout

        self.appear_time = None
        self.disappear_time = None
        self.appear_video = None
        self.disappear_video = None

        # set the log attrs
        self.log_attrs.extend(['appear_time',
                               'disappear_time'])
        self.log_attrs.extend(self.init_param_names)

        self.parallel = None

    def get_current_param(self, name):
        return getattr(self.original_state.most_recently_entered_clone.widget,
                       name)

    def __getitem__(self, name):
        if name in self.widget_param_names:
            #TODO: aliases???
            try:
                return self.issued_param_refs[name]
            except KeyError:
                ref = Ref(self.get_current_param, name)
                self.issued_param_refs[name] = ref
                return ref
        else:
            return Super(WidgetState, self).__getitem__(name)

    def property_callback(self, name, *pargs):
        try:
            ref = self.issued_param_refs[name]
        except KeyError:
            return
        ref.dep_changed()

    def eval_init_refs(self):
        self.params = {name : val(getattr(self, name)) for
                       name in self.init_param_names}

    def resolve_params(self, **updates):
        updates = {name : val(value) for name, value in updates.iteritems()}
        self.params.update(updates)

        #TODO: color names, pos_hint stand-alone arguments?

        # see which absolute placement components we have directly...
        if "pos" in self.params:
            have_left = True
            have_bottom = True
        else:
            have_left = "x" in self.params
            have_bottom = "y" in self.params
        have_top = "top" in self.params
        have_right = "right" in self.params
        if "center" in self.params:
            have_center_x = True
            have_center_y = True
        else:
            have_center_x = "center_x" in self.params
            have_center_y = "center_y" in self.params
        if "size" in self.params:
            have_width = True
            have_height = True
        else:
            have_width = "width" in self.params
            have_height = "height" in self.params

        # see which absolute placement components we have indirectly...
        if sum([have_left, have_right, have_center_x, have_width]) >= 2:
            have_left = True
            have_right = True
            have_center_x = True
            have_width = True
        if sum([have_top, have_bottom, have_center_y, have_height]) >= 2:
            have_top = True
            have_bottom = True
            have_center_y = True
            have_height = True

        # see which pos hints we have...
        #TODO: make copy of pos_hint dict?
        pos_hint = self.params.setdefault("pos_hint", {})
        have_x_hint = any(name in pos_hint for name in ("x", "center_x", "right"))
        have_y_hint = any(name in pos_hint for name in ("y", "center_y", "top"))

        # add pos hints where we don't have prior pos hint or absolute pos...
        if not (have_x_hint or have_left or have_right or have_center_x):
            pos_hint["center_x"] = 0.5
        if not (have_y_hint or have_top or have_bottom or have_center_y):
            pos_hint["center_y"] = 0.5

        # remove kivy's default size hints...
        if "size_hint" not in self.params:
            self.params.setdefault("size_hint_x", None)
            self.params.setdefault("size_hint_y", None)

    def construct(self):
        self.widget = self.widget_class(**self.params)
        self.widget.bind(**{name : partial(self.property_callback, name) for
                            name in self.widget_param_names})

    def show(self):
        if self.layout is None:
            self.parent_widget = self.exp.app.wid
        else:
            self.parent_widget = self.layout.widget
        self.parent_widget.add_widget(self.widget, index=self.index)

    def unshow(self):
        self.parent_widget.remove_widget(self.widget)
        self.parent_widget = None

    def live_change(self, **params):
        self.resolve_params(**params)
        for name, value in self.params.items():
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

        self.eval_init_refs()
        self.resolve_params()
        self.construct()

        self.appear_video = self.exp.app.schedule_video(
            self.appear, self.start_time, self.set_appear_time)
        if self.end_time is not None:
            self.disappear_video = self.exp.app.schedule_video(
                self.disappear, self.end_time, self.set_disappear_time)

    def appear(self):
        self.claim_exceptions()
        self.appear_video = None
        self.on_screen = True
        self.show()
        clock.schedule(self.leave)

    def disappear(self):
        self.claim_exceptions()
        self.disappear_video = None
        self.on_screen = False
        self.unshow()
        clock.schedule(self.finalize)

    def cancel(self, cancel_time):
        if self.active:
            clock.schedule(self.leave)
            cancel_time = max(cancel_time, self.start_time)
            if self.end_time is None or cancel_time < self.end_time:
                if self.disappear_video is not None:
                    self.exp.app.cancel_video(self.disappear_video)
                self.disappear_video = self.exp.app.schedule_video(
                    self.disappear, cancel_time, self.set_disappear_time)
                self.end_time = cancel_time

    def __enter__(self):
        if self.parallel is not None:
            raise RuntimeError("WidgetState context is not reentrant!")  #!!!
        #TODO: make sure we're the previous state?
        WidgetState.layout_stack.append(self)
        self.parallel = Parallel(name="LAYOUT")
        self.parallel.override_instantiation_context()
        self.parallel.claim_child(self)
        self.parallel.__enter__()
        return self

    def __exit__(self, type, value, tb):
        ret = self.parallel.__exit__(type, value, tb)
        if self.duration is None:
            self.parallel.set_child_blocking(0, False)
        else:
            for n in range(1, len(self.parallel.children)):
                self.parallel.set_child_blocking(n, False)
        self.parallel = None
        if len(WidgetState.layout_stack):
            WidgetState.layout_stack.pop()
        return ret


class Animate(State):
    def __init__(self, target, duration=None, parent=None, save_log=True,
                 name=None, **anim_params):
        super(Animate, self).__init__(duration=duration, parent=parent,
                                      save_log=save_log, name=name)
        self.target = target  #TODO: make sure target is a WidgetState
        self.anim_params = anim_params
        self.target_clone = self
        self.initial_params = None

    def _enter(self):
        self.initial_params = None
        self.target_clone = (
            self.target.original_state.most_recently_entered_clone)
        first_update_time = self.start_time + self.exp.app.flip_interval
        clock.schedule(self.update, event_time=first_update_time,
                       repeat_interval=self.exp.app.flip_interval)
        clock.schedule(self.leave)

    def update(self):
        self.claim_exceptions()
        now = clock.now()
        if self.initial_params is None:
            self.initial_params = {
                name : getattr(self.target_clone.widget, name) for
                name in self.anim_params.keys()}
        if self.end_time is not None and now >= self.end_time:
            clock.unschedule(self.update)
            clock.schedule(self.finalize)
            now = self.end_time
        t = now - self.start_time
        params = {name : val(func(t, self.initial_params[name])) for
                  name, func in
                  self.anim_params.items()}
        self.target_clone.live_change(**params)

    def cancel(self, cancel_time):
        if self.active and (self.end_time is None or
                            cancel_time < self.end_time):
            self.end_time = cancel_time


def vertex_instruction_widget(instr_cls, name=None):
    if name is None:
        name = instr_cls.__name__
    base_attrs = dir(kivy.graphics.instructions.VertexInstruction)
    props = []
    for attr in dir(instr_cls):
        if attr in base_attrs:
            continue
        attr_val = getattr(instr_cls, attr, None)
        if hasattr(attr_val, "__get__") and hasattr(attr_val, "__set__"):
            props.append(attr)
    dict_ = {prop : ObjectProperty(None) for prop in props if
             prop not in ("size", "pos")}
    dict_["color"] = ListProperty([1.0, 1.0, 1.0, 1.0])
    
    def __init__(self, *pargs, **kwargs):
        super(type(self), self).__init__(*pargs, **kwargs)
        with self.canvas:
            self._color = kivy.graphics.Color(*self.color)
            shape_kwargs = {}
            for prop in props:
                value = getattr(self, prop)
                if value is not None:
                    shape_kwargs[prop] = value
            for name, value in kwargs.items():
                if name not in shape_kwargs:
                    shape_kwargs[name] = value
            self._shape = instr_cls(**shape_kwargs)
        self.bind(color=self.redraw, **{prop : self.redraw for prop in props})
    dict_["__init__"] = __init__

    def redraw(self, *pargs):
        self._color.rgba = self.color
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                setattr(self._shape, prop, value)
    dict_["redraw"] = redraw

    return type(name, (kivy.uix.widget.Widget,), dict_)


vertex_instructions = [
    "Bezier",
    #"StripMesh",
    "Mesh",
    "Point",
    "Triangle",
    "Quad",
    "Rectangle",
    "BorderImage",
    "Ellipse",
    #"RoundedRectangle"
    ]
for instr in vertex_instructions:
    exec("%s = WidgetState.wrap(vertex_instruction_widget(kivy.graphics.%s))" %
         (instr, instr))


widgets = [
    "Image",
    "Label",
    "Button",
    "Slider",
    #...
    "AnchorLayout",
    "BoxLayout",
    "FloatLayout",
    "RelativeLayout",
    "GridLayout",
    "PageLayout",
    "ScatterLayout",
    "StackLayout"
    ]
for widget in widgets:
    modname = "kivy.uix.%s" % widget.lower()
    exec("import %s" % modname)
    exec("%s = WidgetState.wrap(%s.%s)" %
         (widget, modname, widget))


import kivy.uix.video
class Video(WidgetState.wrap(kivy.uix.video.Video)):
    def construct(self):
        super(Video, self).construct()

        # force video to load immediately so that duration is available...
        _kivy_clock.unschedule(self.widget._do_video_load)
        self.widget._do_video_load()
        self.widget._video.pause()
        while self.widget._video.duration == -1:
            pass  #TODO: make sure we can't get stuck here?
        
        if self.end_time is None:
            self.end_time = self.start_time + self.widget._video.duration

    def show(self):
        if "state" not in self.init_param_names:
            self.widget.state = "play"
        self.widget._video._update(0)  # prevent white flash at start
        super(Video, self).show()

    def unshow(self):
        super(Video, self).unshow()
        self.widget.state = "stop"


def iter_nested_buttons(state):
    if isinstance(state, Button):
        yield state
    if isinstance(state, ParentState):
        for child in state.children:
            for button in iter_nested_buttons(child):
                yield button


class ButtonPress(CallbackState):
    def __init__(self, buttons=None, correct_resp=None, base_time=None,
                 duration=None, parent=None, save_log=True, name=None):
        super(ButtonPress, self).__init__(parent=parent, 
                                          duration=duration,
                                          save_log=save_log,
                                          name=name)
        if buttons is None:
            self.buttons = []
        elif not isinstance(buttons, list):
            self.buttons = [buttons]
        else:
            self.buttons = buttons
        self.button_names = None
        if correct_resp is None:
            self.correct_resp = []
        elif not isinstance(correct_resp, list):
            self.correct_resp = [correct_resp]
        else:
            self.correct_resp = correct_resp
        self.base_time_src = base_time  # for calc rt
        self.base_time = None

        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None

        self.pressed_ref = None

        # append log vars
        self.log_attrs.extend(['button_names', 'correct_resp', 'base_time',
                               'pressed', 'press_time', 'correct', 'rt'])

        self.parallel = None

    def _enter(self):
        self.button_names = [button.name for button in self.buttons]
        self.pressed_ref = Ref(
            lambda lst: [name for name, down in lst if down],
            [(button.name, button["state"] == "down") for button in self.buttons])
        super(ButtonPress, self)._enter()

    def _callback(self):
        self.base_time = val(self.base_time_src)
        if self.base_time is None:
            self.base_time = self.start_time
        self.pressed = ''
        self.press_time = None
        self.correct = False
        self.rt = None
        self.pos = None
        self.pressed_ref.add_change_callback(self.button_callback)

    def button_callback(self):
        self.claim_exceptions()
        pressed_list = self.pressed_ref.eval()
        if not len(pressed_list):
            return
        button = pressed_list[0]
        correct_resp = val(self.correct_resp)
        self.pressed = button
        self.press_time = self.exp.app.event_time

        # calc RT if something pressed
        self.rt = self.press_time['time'] - self.base_time

        if self.pressed in correct_resp:
            self.correct = True

        # let's leave b/c we're all done
        self.cancel(self.press_time['time'])

    def _leave(self):
        self.pressed_ref.remove_change_callback(self.button_callback)
        super(ButtonPress, self)._leave()

    def __enter__(self):
        if self.parallel is not None:
            raise RuntimeError("ButtonPress context is not reentrant!")  #!!!
        #TODO: make sure we're the previous state?
        self.parallel = Parallel(name="BUTTONPRESS")
        self.parallel.override_instantiation_context()
        self.parallel.claim_child(self)
        self.parallel.__enter__()
        return self

    def __exit__(self, type, value, tb):
        ret = self.parallel.__exit__(type, value, tb)
        for n in range(1, len(self.parallel.children)):
            self.parallel.set_child_blocking(n, False)
        self.buttons.extend(iter_nested_buttons(self.parallel))
        self.parallel = None
        return ret


if __name__ == '__main__':
    from experiment import Experiment
    from state import Wait, Loop, Parallel, Meanwhile, UntilDone
    from math import sin, cos
    from contextlib import nested

    exp = Experiment()

    Wait(5.0)

    with Loop(range(3)):
        Video(source="test_video.mp4", size_hint=(1, 1), duration=5.0)

    #button = Button(text="Click to continue", size_hint=(0.25, 0.25))
    #with UntilDone():
    #    Wait(until=button['state']=='down')
    with ButtonPress():
        Button(text="Click to continue", size_hint=(0.25, 0.25))

    with Meanwhile():
        Triangle(points=[0, 0, 500, 500, 0, 500],
                 color=(1.0, 1.0, 0.0, 0.5))

    bez = Bezier(segments=200, color=(1.0, 1.0, 0.0, 1.0), loop=True,
                 points=[0, 0, 200, 200, 200, 100, 100, 200, 500, 500])
    with UntilDone():
        bez.slide(points=[200, 200, 0, 0, 500, 500, 200, 100, 100, 200],
                  color=(0.0, 0.0, 1.0, 1.0), duration=5.0)
        bez.slide(points=[500, 0, 0, 500, 600, 200, 100, 600, 300, 300],
                  color=(1.0, 1.0, 1.0, 1.0), duration=5.0)

    ellipse = Ellipse(x=-25, pos_hint={"center_y": 0.5}, width=25, height=25,
                      angle_start=90.0, angle_end=460.0,
                      color=(1.0, 1.0, 0.0, 1.0), name="Pacman")
    with UntilDone():
        with Parallel(name="Pacman motion"):
            ellipse.slide(x=800, duration=8.0, name="Pacman travel")
            ellipse.animate(
                angle_start=lambda t, initial: initial + (cos(t * 8) + 1) * 22.5,
                angle_end=lambda t, initial: initial - (cos(t * 8) + 1) * 22.5,
                duration=8.0, name="Pacman gobble")

    with BoxLayout(width=500, height=500, pos_hint={"top": 1}, duration=4.0):
        rect = Rectangle(color=(1.0, 0.0, 0.0, 1.0), size_hint=(1, 1),
                         duration=3.0)
        Rectangle(color=(0.0, 1.0, 0.0, 1.0), size_hint=(1, 1), duration=2.0)
        Rectangle(color=(0.0, 0.0, 1.0, 1.0), size_hint=(1, 1), duration=1.0)
        rect.slide(color=(1.0, 1.0, 1.0, 1.0), size_hint=(1, 1), duration=3.0)

    with Loop(range(3)):
        Rectangle(x=0, y=0, width=50, height=50, color=(1.0, 0.0, 0.0, 1.0),
                  duration=1.0)
        Rectangle(x=50, y=50, width=50, height=50, color=(0.0, 1.0, 0.0, 1.0),
                  duration=1.0)
        Rectangle(x=100, y=100, width=50, height=50, color=(0.0, 0.0, 1.0, 1.0),
                  duration=1.0)

    with Parallel():
        label = Label(text="SMILE!", duration=4.0, center_x=100, center_y=100,
                      font_size=50)
        label.slide(center_x=400, center_y=400, font_size=100, duration=4.0)
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
    img = Image(source="face-smile.png", size=(10, 10), allow_stretch=True,
                keep_ratio=False, mipmap=True)
    with UntilDone():
        img.slide(size=(100, 200), duration=5.0)

    Wait(5.0)
    exp.run(trace=False)
