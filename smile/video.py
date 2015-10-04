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
from ref import val, Ref, NotAvailable
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
        if len(spec) == 2:
            name, alpha = spec
            if not isinstance(name, str):
                raise ValueError(
                    "If color spec is 2-tuple, first element must be str.")
            if type(alpha) not in (int, float):
                raise ValueError(
                    "If color spec is 2-tuple, second element must be "
                    "int or float.")
            try:
                return color_name_table[name.upper()][:3] + (alpha,)
            except KeyError:
                raise ValueError("Color spec string not valid.  Got: %r" %
                                 spec)
        if len(spec) == 3:
            return tuple(spec) + (1.0,)
        elif len(spec) == 4:
            return tuple(spec)
        else:
            raise ValueError(
                "Color spec tuple / list must have length 2, 3, or 4.  "
                "Got: %r" % spec)
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


class Screenshot(CallbackState):
    def __init__(self, filename=None, parent=None, save_log=True, name=None,
                 blocking=True):
        super(Screenshot, self).__init__(parent=parent,
                                         save_log=save_log,
                                         name=name,
                                         blocking=blocking)
        self._init_filename = filename
        self._event_time = None

        self._log_attrs.extend(["filename", "event_time"])

    def _enter(self):
        super(Screenshot, self)._enter()
        if self._filename is None:
            self._filename = self._exp.reserve_data_filename(
                "screenshot_%s" % self._name, "png", use_timestamp=True)
        self._event_time = NotAvailable

    def _callback(self):
        before = clock.now()
        self._exp._app.screenshot(self._filename)
        after = clock.now()
        self._event_time = {"time": before, "error": after - before}


class VisualState(State):
    def __init__(self, duration=None, parent=None, save_log=True, name=None,
                 blocking=True):
        super(VisualState, self).__init__(parent=parent,
                                          duration=duration,
                                          save_log=save_log,
                                          name=name,
                                          blocking=blocking)

        self._appear_time = None
        self._disappear_time = None
        self._appeared = False
        self._disappeared = False
        self._on_screen = False
        self.__appear_video = None
        self.__disappear_video = None

        # set the log attrs
        self._log_attrs.extend(['appear_time',
                                'disappear_time'])

    def set_appear_time(self, appear_time):
        self._appear_time = appear_time
        self._on_screen = True
        self._appeared = True
        clock.schedule(self.leave)

    def set_disappear_time(self, disappear_time):
        self._disappear_time = disappear_time
        self._on_screen = False
        self._disappeared = True
        clock.schedule(self.finalize)

    def _schedule_start(self):
        self.__appear_video = self._exp._app.schedule_video(
            self.appear, self._start_time, self.set_appear_time)

    def _unschedule_start(self):
        if self.__appear_video is not None:
            self._exp._app.cancel_video(self.__appear_video)

    def _schedule_end(self):
        self.__disappear_video = self._exp._app.schedule_video(
            self.disappear, self._end_time, self.set_disappear_time)

    def _unschedule_end(self):
        if self.__disappear_video is not None:
            self._exp._app.cancel_video(self.__disappear_video)

    def _enter(self):
        self._appear_time = NotAvailable
        self._disappear_time = NotAvailable
        self._appeared = False
        self._disappeared = False
        self._on_screen = False
        self.__appear_video = None
        self.__disappear_video = None

    def show(self):
        pass

    def unshow(self):
        pass

    def appear(self):
        self.claim_exceptions()
        self._started = True
        self.__appear_video = None
        self.show()

    def disappear(self):
        self.claim_exceptions()
        self._ended = True
        self.__disappear_video = None
        self.unshow()


class BackgroundColor(VisualState):  #TODO: this doesn't work with Done?  Never clears?
    layers = []
    def __init__(self, color, duration=None, parent=None, save_log=True,
                 name=None, blocking=True):
        super(BackgroundColor, self).__init__(parent=parent,
                                              duration=duration,
                                              save_log=save_log,
                                              name=name,
                                              blocking=blocking)
        self._init_color = color

    def show(self):
        BackgroundColor.layers.append(self)
        self._exp.set_background_color(self._color)

    def unshow(self):
        if BackgroundColor.layers[-1] is self:
            BackgroundColor.layers.pop()
            try:
                color = BackgroundColor.layers[-1]._color
            except IndexError:
                color = None
            self._exp.set_background_color(color)
        else:
            BackgroundColor.layers.remove(self)


class WidgetState(VisualState):
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
        if name is None:
            name = widget_class.__name__
        def __init__(self, *pargs, **kwargs):
            cls.__init__(self, widget_class, *pargs, **kwargs)
        return type(name, (cls,), {"__init__" : __init__})

    def __init__(self, widget_class, duration=None, parent=None, save_log=True,
                 name=None, blocking=True, index=0, layout=None, **params):
        super(WidgetState, self).__init__(parent=parent,
                                          duration=duration,
                                          save_log=save_log,
                                          name=name,
                                          blocking=blocking)

        self.__issued_refs = weakref.WeakValueDictionary()
        self.__widget_param_names = widget_class().properties().keys()
        self.__widget_class = widget_class
        self._init_index = index
        self._widget = None
        self.__parent_widget = None
        self._constructor_param_names = params.keys()
        self._init_constructor_params = params
        for name, value in params.iteritems():
            setattr(self, "_init_" + name, value)
        if layout is None:
            if len(WidgetState.layout_stack):
                self.__layout = WidgetState.layout_stack[-1]
            else:
                self.__layout = None
        else:
            self.__layout = layout

        self.__x_pos_mode = None
        self.__y_pos_mode = None

        # set the log attrs
        self._log_attrs.extend(['constructor_params'])

        self.__parallel = None

    def get_attribute_ref(self, name):
        try:
            return self.__issued_refs[name]
        except KeyError:
            try:
                props = WidgetState.property_aliases[name]
            except KeyError:
                if name in self.__widget_param_names:
                    props = name
                else:
                    return super(WidgetState, self).get_attribute_ref(name)
            if isinstance(props, str):
                ref = Ref(self.get_current_param, props)
            elif isinstance(props, tuple):
                ref = tuple(Ref(self.get_current_param, prop) for
                            prop in props)
            else:
                raise RuntimeError("Bad value for 'props': %r" % props)
            self.__issued_refs[name] = ref
            return ref

    def attribute_update_state(self, name, value):
        if name in self.__widget_param_names:
            return UpdateWidget(self, **{name : value})
        else:
            raise AttributeError("%r is not a property of this widget (%r)." %
                                 (name, self))

    def get_current_param(self, name):
        # important that this is pulling from the current clone
        return getattr(self.current_clone._widget, name)

    def property_callback(self, name, *pargs):
        # ensure we update dependencies if necessary
        try:
            ref = self.__issued_refs[name]
        except KeyError:
            return
        ref.dep_changed()

    def eval_init_refs(self):
        return self.transform_params(self.apply_aliases(
            {name : getattr(self, "_" + name) for
             name in self._constructor_param_names}))

    def apply_aliases(self, params):
        new_params = {}
        for name, value in params.items():
            props = WidgetState.property_aliases.get(name, name)
            if isinstance(props, str):
                new_params[props] = value
            elif isinstance(props, tuple):
                for n, prop in enumerate(props):
                    new_params[prop] = value[n]
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
        # remove kivy's default size hints
        # if a user didn't specify them
        if "size_hint" not in params:
            params.setdefault("size_hint_x", None)
            params.setdefault("size_hint_y", None)

        return params

    def construct(self, params):
        # construct the widget, set params, and bind them
        self._widget = self.__widget_class(**params)
        self._set_widget_defaults()
        self.live_change(**params)
        self._widget.bind(**{name : partial(self.property_callback, name) for
                            name in self.__widget_param_names})

    def _set_widget_defaults(self):
        pass

    def show(self):
        # add the widget to the correct parent to handle drawing
        if self.__layout is None:
            self.__parent_widget = self._exp._app.wid
        else:
            self.__parent_widget = self.__layout.current_clone._widget
        self.__parent_widget.add_widget(self._widget, index=self._index)

    def unshow(self):
        # remove the widget from the parent
        self.__parent_widget.remove_widget(self._widget)
        self.__parent_widget = None

    def live_change(self, **params):
        # handle setting any property of a widget
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
            self.__x_pos_mode = new_x_pos_mode
        elif self.__x_pos_mode is None:
            params["center_x"] = self._exp.screen.center_x.eval()
        elif self.__x_pos_mode == "min":
            params["x"] = self._widget.x
        elif self.__x_pos_mode == "mid":
            params["center_x"] = self._widget.center_x
        elif self.__x_pos_mode == "max":
            params["right"] = self._widget.right
        if new_y_pos_mode is not None:
            self.__y_pos_mode = new_y_pos_mode
        elif self.__y_pos_mode is None:
            params["center_y"] = self._exp.screen.center_y.eval()
        elif self.__y_pos_mode == "min":
            params["y"] = self._widget.y
        elif self.__y_pos_mode == "mid":
            params["center_y"] = self._widget.center_y
        elif self.__y_pos_mode == "max":
            params["top"] = self._widget.top
        for name, value in params.iteritems():
            if name not in pos_props:
                setattr(self._widget, name, value)
        for name, value in params.iteritems():
            if name in pos_props:
                setattr(self._widget, name, value)

    def animate(self, duration=None, parent=None, save_log=True, name=None,
                blocking=True, **anim_params):
        anim = Animate(self, duration=duration, parent=parent, name=name,
                       save_log=save_log, blocking=blocking, **anim_params)
        anim.override_instantiation_context()
        return anim

    def slide(self, duration=None, speed=None, accel=None, parent=None,
              save_log=True, name=None, blocking=True, **params):
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
                            save_log=save_log, name=name, blocking=blocking,
                            **anim_params)
        anim.override_instantiation_context()
        return anim

    def _enter(self):
        self.__x_pos_mode = None
        self.__y_pos_mode = None

        params = self.eval_init_refs()
        params = self.resolve_params(params)
        self.construct(params)

        # We do this after because self.construct might modify self._end_time.
        super(WidgetState, self)._enter()

    def __enter__(self):
        if self.__parallel is not None:
            raise RuntimeError("WidgetState context is not reentrant!")  #!!!
        #TODO: make sure we're the previous state?
        WidgetState.layout_stack.append(self)
        self.__parallel = Parallel(name="LAYOUT")
        self.__parallel.override_instantiation_context()
        self.__parallel.claim_child(self)
        self.__parallel.__enter__()
        return self

    def __exit__(self, type, value, tb):
        ret = self.__parallel.__exit__(type, value, tb)
        if self._init_duration is None:
            self.__parallel._children[0]._blocking = False
        else:
            for child in self.__parallel._children[1:]:
                child._blocking = False
        self.__parallel = None
        if len(WidgetState.layout_stack):
            WidgetState.layout_stack.pop()
        return ret


class UpdateWidget(CallbackState):
    #TODO: separate log entry for each value (as in Set)
    def __init__(self, target, parent=None, save_log=True, name=None,
                 blocking=True, **kwargs):
        super(UpdateWidget, self).__init__(duration=0.0,
                                           parent=parent,
                                           save_log=save_log,
                                           name=name,
                                           blocking=blocking)
        self.__target = target
        self._init_values = kwargs
        self._log_attrs.extend(['values'])

    def _enter(self):
        super(UpdateWidget, self)._enter()
        self.__target_clone = self.__target.current_clone

    def _callback(self):
        self.__target_clone.live_change(**self._values)


class Animate(State):
    #TODO: log updates!
    def __init__(self, target, duration=None, parent=None, save_log=True,
                 name=None, blocking=True, **anim_params):
        super(Animate, self).__init__(duration=duration, parent=parent,
                                      save_log=save_log, name=name,
                                      blocking=blocking)
        self.__target = target  #TODO: make sure target is a WidgetState
        self.__anim_params = anim_params
        self.__initial_params = None

    def _schedule_start(self):
        first_update_time = self._start_time + self._exp._app.flip_interval
        clock.schedule(self.update, event_time=first_update_time,
                       repeat_interval=self._exp._app.flip_interval)
        clock.schedule(self.leave)

    def _unschedule_start(self):
        clock.unschedule(self.update)
        clock.unschedule(self.leave)

    def _enter(self):
        self.__initial_params = None
        self.__target_clone = self.__target.current_clone

    def update(self):
        self.claim_exceptions()
        self._started = True
        now = clock.now()
        if self.__initial_params is None:
            self.__initial_params = {
                name : self.__target_clone.get_attribute_ref(name).eval() for
                name in self.__anim_params.iterkeys()}
        if self._end_time is not None and now >= self._end_time:
            clock.unschedule(self.update)
            clock.schedule(self.finalize)
            now = self._end_time
        t = now - self._start_time
        params = {name : func(t, self.__initial_params[name]) for
                  name, func in
                  self.__anim_params.iteritems()}
        self.__target_clone.live_change(
            **self.__target_clone.transform_params(
                self.__target_clone.apply_aliases(params)))


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
    "Label",
    "Button",
    "Slider",
    "TextInput",
    "ToggleButton",
    "ProgressBar",
    
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

import kivy.uix.rst
RstDocument = WidgetState.wrap(kivy.uix.rst.RstDocument)


import kivy.uix.video
class Video(WidgetState.wrap(kivy.uix.video.Video)):
    def _set_widget_defaults(self):
        # force video to load immediately so that duration is available...
        _kivy_clock.unschedule(self._widget._do_video_load)
        self._widget._do_video_load()
        self._widget._video.pause()
        while self._widget._video.duration == -1:
            pass  #TODO: make sure we can't get stuck here?
        if self._end_time is None:
            self._end_time = self._start_time + self._widget._video.duration

        # set the size to (0, 0) so we know if it has been changed later
        self._widget.size = (0, 0)

    def show(self):
        if "state" not in self._constructor_param_names:
            self._widget.state = "play"
        self._widget._video._update(0)  # prevent white flash at start
        #while self._widget._video.texture is None:
        #    print '.',
        if self._widget.width == 0 and self._widget.height == 0:
            self.live_change(size=self._widget._video.texture.size)
        super(Video, self).show()

    def unshow(self):
        super(Video, self).unshow()
        self._widget.state = "stop"


import kivy.uix.image
class Image(WidgetState.wrap(kivy.uix.image.Image)):
    def _set_widget_defaults(self):
        self._widget.size = self._widget.texture_size


def iter_nested_buttons(state):
    if isinstance(state, Button):
        yield state
    if isinstance(state, ParentState):
        for child in state._children:
            for button in iter_nested_buttons(child):
                yield button

class ButtonPress(CallbackState):
    def __init__(self, buttons=None, correct_resp=None, base_time=None,
                 duration=None, parent=None, save_log=True, name=None,
                 blocking=True):
        super(ButtonPress, self).__init__(parent=parent, 
                                          duration=duration,
                                          save_log=save_log,
                                          name=name,
                                          blocking=blocking)
        if buttons is None:
            self.__buttons = []
        elif type(buttons) not in (list, tuple):
            self.__buttons = [buttons]
        else:
            self.__buttons = buttons
        self._button_names = None
        self._init_correct_resp = correct_resp
        self._init_base_time = None

        self._pressed = ''
        self._press_time = None
        self._correct = False
        self._rt = None

        self.__pressed_ref = None

        # append log vars
        self._log_attrs.extend(['button_names', 'correct_resp', 'base_time',
                                'pressed', 'press_time', 'correct', 'rt'])

        self.__parallel = None

    def _enter(self):
        self._button_names = [button._name for button in self.__buttons]
        if self._correct_resp is None:
            self._correct_resp = []
        elif type(self.correct_resp) not in (list, tuple):
            self._correct_resp = [self._correct_resp]
        self.__pressed_ref = Ref(
            lambda lst: [name for name, down in lst if down],
            [(button.name, button.state == "down") for
             button in self.__buttons])
        super(ButtonPress, self)._enter()

    def _callback(self):
        if self._base_time is None:
            self._base_time = self._start_time
        self._pressed = NotAvailable
        self._press_time = NotAvailable
        self._correct = NotAvailable
        self._rt = NotAvailable
        self.__pressed_ref.add_change_callback(self.button_callback)

    def button_callback(self):
        self.claim_exceptions()
        pressed_list = self.__pressed_ref.eval()
        if not len(pressed_list):
            return
        button = pressed_list[0]
        self._pressed = button
        self._press_time = self._exp._app.event_time

        # calc RT if something pressed
        self._rt = self._press_time['time'] - self._base_time

        if self._pressed in self._correct_resp:
            self._correct = True

        # let's leave b/c we're all done
        self.cancel(self._press_time['time'])

    def _leave(self):
        self.__pressed_ref.remove_change_callback(self.button_callback)
        super(ButtonPress, self)._leave()
        if self._pressed is NotAvailable:
            self._pressed = ''
        if self._press_time is NotAvailable:
            self._press_time = None
        if self._correct is NotAvailable:
            self._correct = False
        if self._rt is NotAvailable:
            self._rt = None

    def __enter__(self):
        if self.__parallel is not None:
            raise RuntimeError("ButtonPress context is not reentrant!")  #!!!
        #TODO: make sure we're the previous state?
        self.__parallel = Parallel(name="BUTTONPRESS")
        self.__parallel.override_instantiation_context()
        self.__parallel.claim_child(self)
        self.__parallel.__enter__()
        return self

    def __exit__(self, type, value, tb):
        ret = self.__parallel.__exit__(type, value, tb)
        for child in self.__parallel._children[1:]:
            child._blocking = False
        self.__buttons.extend(iter_nested_buttons(self.__parallel))
        self.__parallel = None
        return ret


if __name__ == '__main__':
    from experiment import Experiment
    from state import Wait, Loop, Parallel, Meanwhile, UntilDone, Serial, Done, Debug
    from mouse import MouseCursor
    from math import sin, cos
    from contextlib import nested

    exp = Experiment(background_color="#330000")

    Wait(2.0)

    pb = ProgressBar(max=100)
    with UntilDone():
        pb.slide(value=100, duration=2.0)

    Image(source="face-smile.png", duration=5.0)

    text = """
.. _top:

Hello world
===========

This is an **emphased text**, some ``interpreted text``.
And this is a reference to top_::

$ print("Hello world")

    """
    RstDocument(text=text, duration=5.0, size=exp.screen.size)

    with ButtonPress():
        button = Button(text="Click to continue", size=(exp.screen.width / 4,
                                                        exp.screen.height / 8))
        slider = Slider(min=exp.screen.left, max=exp.screen.right,
                        top=button.bottom, blocking=False)
        rect = Rectangle(color="purple", width=50, height=50,
                         center_top=exp.screen.left_top, blocking=False)
        rect.animate(center_x=lambda t, initial: slider.value, blocking=False)
        ti = TextInput(text="EDIT!", top=slider.bottom, blocking=False)
        MouseCursor()
    label = Label(text=ti.text, duration=5.0, font_size=50, color="white")
    Done(label)
    Debug(label_disappear_time=label.disappear_time)

    Ellipse(color="white", width=100, height=100)
    with UntilDone():
        with Parallel():
            BackgroundColor("blue", duration=6.0)
            with Serial():
                Wait(1.0)
                BackgroundColor("green", duration=2.0)
            with Serial():
                Wait(2.0)
                BackgroundColor("red", duration=2.0)
            with Serial():
                Wait(3.0)
                BackgroundColor("yellow", duration=2.0)

    rect = Rectangle(color="purple", width=50, height=50)
    with UntilDone():
        Wait(1.0)
        rect.center = exp.screen.right_top
        Wait(1.0)
        rect.center = exp.screen.right_bottom
        Wait(1.0)
        rect.center = exp.screen.left_top
        #Screenshot()
        Wait(1.0)
        rect.center = exp.screen.left_bottom
        Wait(1.0)
        rect.center = exp.screen.center
        Wait(1.0)
        rect.slide(center=exp.screen.right_top, duration=2.0)
        rect.slide(center=exp.screen.right_bottom, duration=2.0)
        rect.slide(center=exp.screen.left_top, duration=2.0)
        rect.slide(center=exp.screen.left_bottom, duration=2.0)
        rect.slide(center=exp.screen.center, duration=2.0)

    vid = Video(source="test_video.mp4", right_top=exp.screen.center,
                allow_stretch=True, keep_ratio=False)
    with Meanwhile():
        vid.slide(center_x=exp.screen.width * 0.75,
                  center_y=exp.screen.center_y,
                  duration=1.0)
        #Screenshot("my_screenshot.png")
        vid.animate(center_x=(lambda t, initial: exp.screen.center_x +
                              cos(t / 3.0) * exp.screen.width * 0.25),
                    center_y=(lambda t, initial: exp.screen.center_y +
                              sin(t / 3.0) * exp.screen.width * 0.25),
                    height=(lambda t, initial: initial + sin(t / 2.0) *
                            initial * 0.5))
    with Loop(3) as loop:
        Video(source="test_video.mp4", size=exp.screen.size,
              allow_stretch=loop.i%2, duration=5.0)
        #Screenshot(name="foo")

    with ButtonPress():
        Button(text="Click to continue", size=(exp.screen.width / 4,
                                               exp.screen.height / 4))
        MouseCursor()
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

    ellipse = Ellipse(right=exp.screen.left,
                      center_y=exp.screen.center_y, width=25, height=25,
                      angle_start=90.0, angle_end=460.0,
                      color=(1.0, 1.0, 0.0), name="Pacman")
    with UntilDone():
        with Parallel(name="Pacman motion"):
            ellipse.slide(left=exp.screen.right, duration=8.0, name="Pacman travel")
            ellipse.animate(
                angle_start=lambda t, initial: initial + (cos(t * 8) + 1) * 22.5,
                angle_end=lambda t, initial: initial - (cos(t * 8) + 1) * 22.5,
                duration=8.0, name="Pacman gobble")

    with BoxLayout(width=500, height=500, top=exp.screen.top, duration=4.0):
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
            ellipse.slide(color=("orange", 0.0), duration=5.0)
            rect.slide(color=("pink", 0.0), duration=5.0)
    img = Image(source="face-smile.png", size=(10, 10), allow_stretch=True,
                keep_ratio=False, mipmap=True)
    with UntilDone():
        img.slide(size=(100, 200), duration=5.0)

    Wait(2.0)
    exp.run(trace=False)
