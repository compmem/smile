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
    # subset from http://www.rapidtables.com/web/color/RGB_Color.htm
    "BLACK": (0.0, 0.0, 0.0, 1.0),
    "GRAY": (0.5, 0.5, 0.5, 1.0),
    "SILVER": (0.75, 0.75, 0.75, 1.0),
    "WHITE": (1.0, 1.0, 1.0, 1.0),
    "RED": (1.0, 0.0, 0.0, 1.0),
    "LIME": (0.0, 1.0, 0.0, 1.0),
    "BLUE": (0.0, 0.0, 1.0, 1.0),
    "YELLOW": (1.0, 1.0, 0.0, 1.0),
    "CYAN": (0.0, 1.0, 1.0, 1.0),
    "MAGENTA": (1.0, 0.0, 1.0, 1.0),
    "MAROON": (0.5, 0.0, 0.0, 1.0),
    "GREEN": (0.0, 0.5, 0.0, 1.0),
    "NAVY": (0.0, 0.0, 0.5, 1.0),
    "OLIVE": (0.5, 0.5, 0.0, 1.0),
    "TEAL": (0.0, 0.5, 0.5, 1.0),
    "PURPLE": (0.5, 0.0, 0.5, 1.0),
    "ORANGE": (1.0, 0.65, 0.0, 1.0),
    "PINK": (1.0, 0.75, 0.8, 1.0),
    "BROWN": (0.65, 0.16, 0.16, 1.0),
    "INDIGO": (0.29, 0.5, 0.0, 1.0)
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
    property_aliases = {
        "left": "x",
        "bottom": "y",
        "left_bottom": "pos",
        "left_center": ("x", "center_y"),
        "left_top": ("x", "top"),
        "center_bottom": ("center_x", "y"),
        "center_top": ("center_x", "top"),
        "right_bottom": ("right", "y"),
        "right_center": ("right", "center_y"),
        "right_top": ("right", "top")
        }

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

        self.x_pos_mode = None
        self.y_pos_mode = None

        # set the log attrs
        self.log_attrs.extend(['appear_time',
                               'disappear_time'])
        self.log_attrs.extend(self.init_param_names)

        self.parallel = None

    def get_current_param(self, name):
        return getattr(self.original_state.most_recently_entered_clone.widget,
                       name)

    def __getitem__(self, name):
        try:
            return self.issued_param_refs[name]
        except KeyError:
            try:
                props = WidgetState.property_aliases[name]
            except KeyError:
                if name in self.widget_param_names:
                    props = name
                else:
                    return super(WidgetState, self).__getitem__(name)
            if isinstance(props, str):
                ref = Ref(self.get_current_param, props)
            elif isinstance(props, tuple):
                ref = tuple(Ref(self.get_current_param, prop) for
                            prop in props)
            else:
                raise RuntimeError("Bad value for 'props': %r" % props)
            self.issued_param_refs[name] = ref
            return ref

    def property_callback(self, name, *pargs):
        try:
            ref = self.issued_param_refs[name]
        except KeyError:
            return
        ref.dep_changed()

    def eval_init_refs(self):
        return self.transform_params(self.apply_aliases(
            {name : getattr(self, name) for name in self.init_param_names}))

    def apply_aliases(self, params):
        new_params = {}
        for name, value in params.items():
            props = WidgetState.property_aliases.get(name, name)
            if isinstance(props, str):
                new_params[props] = value
            elif isinstance(props, tuple):
                for n, prop in enumerate(props):
                    new_params[prop] = subvalue[n]
            else:
                raise RuntimeError("Bad value for 'props': %r" % props)
        return new_params

    def transform_params(self, params):
        for name, value in params.iteritems():
            params[name] = self.transform_param(name, value)
        return params

    def transform_param(self, name, value):
        value = val(value)

        # normalize color specifier...
        if value is not None and "color" in name:
            return normalize_color_spec(value)
        else:
            return value

    def resolve_params(self, params):
        # remove kivy's default size hints...
        if "size_hint" not in params:
            params.setdefault("size_hint_x", None)
            params.setdefault("size_hint_y", None)

        return params

    def construct(self, params):
        self.widget = self.widget_class(**params)
        self.live_change(**params)
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
        xy_pos_props = {"pos": "min", "center": "mid"}
        x_pos_props = {"x": "min", "center_x": "mid", "right": "max"}
        y_pos_props = {"y": "min", "center_y": "mid", "top": "max"}
        pos_props = (xy_pos_props.keys() +
                     x_pos_props.keys() +
                     y_pos_props.keys())
        new_x_pos_mode = None
        new_y_pos_mode = None
        for prop, mode in xy_pos_props.iteritems():
            if prop in params:
                new_x_pos_mode = mode
                new_y_pos_mode = mode
                break
        else:
            for prop, mode in x_pos_props.iteritems():
                if prop in params:
                    new_x_pos_mode = mode
                    break
            for prop, mode in y_pos_props.iteritems():
                if prop in params:
                    new_y_pos_mode = mode
                    break
        if new_x_pos_mode is not None:
            self.x_pos_mode = new_x_pos_mode
        elif self.x_pos_mode is None:
            params["center_x"] = self.exp.screen["center_x"].eval()
        elif self.x_pos_mode == "min":
            params["x"] = self["x"].eval()
        elif self.x_pos_mode == "mid":
            params["center_x"] = self["center_x"].eval()
        elif self.x_pos_mode == "max":
            params["right"] = self["right"].eval()
        if new_y_pos_mode is not None:
            self.y_pos_mode = new_y_pos_mode
        elif self.y_pos_mode is None:
            params["center_y"] = self.exp.screen["center_y"].eval()
        elif self.y_pos_mode == "min":
            params["y"] = self["y"].eval()
        elif self.y_pos_mode == "mid":
            params["center_y"] = self["center_y"].eval()
        elif self.y_pos_mode == "max":
            params["top"] = self["top"].eval()
        for name, value in params.iteritems():
            if name not in pos_props:
                setattr(self.widget, name, value)
        for name, value in params.iteritems():
            if name in pos_props:
                setattr(self.widget, name, value)

    def animate(self, duration=None, parent=None, save_log=True, name=None,
                **anim_params):
        anim = Animate(self, duration=duration, parent=parent, name=name,
                       save_log=save_log, **anim_params)
        anim.override_instantiation_context()
        return anim

    def slide(self, duration=None, speed=None, accel=None, parent=None,
              save_log=True, name=None, **params):
        def interp(a, b, w):
            if isinstance(a, dict):
                return {name : interp(a[name], b[name], w) for
                        name in set(a) & set(b)}
            elif hasattr(a, "__iter__"):
                return [interp(a_prime, b_prime, w) for
                        a_prime, b_prime in
                        zip(a, b)]
            else:
                return a * (1.0 - w) + b * w
        condition = duration is None, speed is None, accel is None
        if condition == (False, True, True):  # simple, linear interpolation
            anim_params = {}
            for param_name, value in params.items():
                def func(t, initial, value=value, param_name=param_name):
                    new_value = self.transform_param(param_name, value)
                    return interp(initial, new_value, t / duration)
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
        self.x_pos_mode = None
        self.y_pos_mode = None

        params = self.eval_init_refs()
        params = self.resolve_params(params)
        self.construct(params)

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
                name : self.target_clone[name].eval() for
                name in self.anim_params.keys()}
        if self.end_time is not None and now >= self.end_time:
            clock.unschedule(self.update)
            clock.schedule(self.finalize)
            now = self.end_time
        t = now - self.start_time
        params = {name : func(t, self.initial_params[name]) for
                  name, func in
                  self.anim_params.items()}
        self.target_clone.live_change(
            **self.target_clone.transform_params(
                self.target_clone.apply_aliases(params)))

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
    def construct(self, params):
        super(Video, self).construct(params)

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

    rect = Rectangle(color="purple", width=50, height=50)
    with UntilDone():
        rect.slide(center=exp.screen["right_top"], duration=2.0)
        rect.slide(center=exp.screen["right_bottom"], duration=2.0)
        rect.slide(center=exp.screen["left_top"], duration=2.0)
        rect.slide(center=exp.screen["left_bottom"], duration=2.0)
        rect.slide(center=exp.screen["center"], duration=2.0)

    with Loop(range(3)):
        Video(source="test_video.mp4", size=exp.screen["size"], duration=5.0)

    with ButtonPress():
        Button(text="Click to continue", size=(exp.screen["width"] / 4,
                                               exp.screen["height"] / 4))

    with Meanwhile():
        Triangle(points=[0, 0, 500, 500, 0, 500],
                 color=(1.0, 1.0, 0.0, 0.5))

    bez = Bezier(segments=200, color="yellow", loop=True,
                 points=[0, 0, 200, 200, 200, 100, 100, 200, 500, 500])
    with UntilDone():
        bez.slide(points=[200, 200, 0, 0, 500, 500, 200, 100, 100, 200],
                  color="blue", duration=5.0)
        bez.slide(points=[500, 0, 0, 500, 600, 200, 100, 600, 300, 300],
                  color="white", duration=5.0)

    ellipse = Ellipse(right=exp.screen["left"],
                      center_y=exp.screen["center_y"], width=25, height=25,
                      angle_start=90.0, angle_end=460.0,
                      color=(1.0, 1.0, 0.0), name="Pacman")
    with UntilDone():
        with Parallel(name="Pacman motion"):
            ellipse.slide(left=exp.screen["right"], duration=8.0, name="Pacman travel")
            ellipse.animate(
                angle_start=lambda t, initial: initial + (cos(t * 8) + 1) * 22.5,
                angle_end=lambda t, initial: initial - (cos(t * 8) + 1) * 22.5,
                duration=8.0, name="Pacman gobble")

    with BoxLayout(width=500, height=500, top=exp.screen["top"], duration=4.0):
        rect = Rectangle(color=(1.0, 0.0, 0.0, 1.0), pos=(0, 0), size_hint=(1, 1), duration=3.0)
        Rectangle(color="#00FF00", pos=(0, 0), size_hint=(1, 1), duration=2.0)
        Rectangle(color=(0.0, 0.0, 1.0, 1.0), pos=(0, 0), size_hint=(1, 1), duration=1.0)
        rect.slide(color=(1.0, 1.0, 1.0, 1.0), duration=3.0)

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
        Rectangle(x=50, y=50, width=50, height=50, color="lime",
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

    rect = Rectangle(x=0, y=0, width=50, height=50, color="brown")
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
                          color="orange")
        with UntilDone():
            rect.slide(color="pink", x=0, y=0,
                       width=100, height=100, duration=5.0)
            ellipse.slide(color=(0.0, 0.0, 1.0, 0.0), duration=5.0)
            rect.slide(color=(1.0, 1.0, 1.0, 0.0), duration=5.0)
    img = Image(source="face-smile.png", size=(10, 10), allow_stretch=True,
                keep_ratio=False, mipmap=True)
    with UntilDone():
        img.slide(size=(100, 200), duration=5.0)

    Wait(5.0)
    exp.run(trace=False)
