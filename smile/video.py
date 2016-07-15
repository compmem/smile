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

import kivy.metrics
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
    """A state used to take a screenshot at a certain time during your experiment.

    A *Screenshot* state is used to take a screenshot of the screen during your
    experiment. Best used with an *UntilDone* or *Meanwhile* state, it will
    capture the screen and save it out to a png file. It will also log the time
    at which the screenshot was taken.

    Parameters
    ----------
    filename : string
        The string filename, without .png, that you want your screenshot to
        be saved as.
    parent : ParentState
        The parent of this state.  If None, it is set automatically.
    save_log : boolean
        Weather or not to save out *Logged Attributes**.
    name : string
        The unique name given to this state.
    blocking : boolean
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its Parallel Parent finishes
        running. Only relevant if within a *Parallel* Parent.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and manipulated
    within the experiment code, and will be automatically recorded in the
    state-specific log. Refer to State class docstring for additional logged
    parameters.

    event_time : dictionary
        The keys are *time* and *error* where *time* is the time at which the
        screenshot was taken, and the *error* refers to the maximum error that
        the presented time could be off by.

    """
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
    """The base state for all visual stimulus presenting states.

    A *VisualState* contains all of the methods that are needed to time visual
    states.  All visual stimulus presenting states will be a subclass of this
    class. Using the *show()* and *unshow()* methods, you can subclass
    *VisualState* to present to the *Experiment* window.

    Parameters
    ----------
    duration : float
        A float, in seconds, that is the duration of this *VisualState*
    parent : ParentState
        The parent of this state. If None, it will be set automatically
    save_log : boolean
        If True, this state will save out all of the Logged Attributes
    name : string
        The unique name to this state
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevant if within a *ParallelParent*.

    Logged Attributes
    -----------------
    All parameters above are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state-specific log. Refer to State class
    docstring for additional logged parameters.

    appear_time : dictionary
        The keys are *time* and *error*. Where *time* refers to the time the
        visual stimulus appeared on the screen, and *error* refers to the
        maximum error in calculating the appear time of the stimulus.
    disappear_time : dictionary
        The keys are *time* and *error*. Where *time* refers to the time the
        visual stimulus disappeared from the screen, and *error* refers to the
        maximum error in calculating the disappear time of the stimulus.

    """
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

    def cancel(self, cancel_time):
        if self._appear_time == NotAvailable:
            self._appear_time = None
        if self._disappear_time == NotAvailable:
            self._disappear_time = None
        super(VisualState, self).cancel(cancel_time)


class BackgroundColor(VisualState):  #TODO: this doesn't work with Done?  Never clears?
    """ Sets the BackgroundColor for a duration.

    If you need to change the background color during experimental runtime, you
    would use this state. The color can either be set as a string or a tuple
    with RGBA values between 0 and 1. The list of string colors are in
    smile.video.color_name_table.

    Parameters
    ----------
    color : tuple or string
        Pick either 4 values between 0 and 1 that correspond to the RGBA
        values of the color you would like to select, or you pick the
        string value, all capitol letters, that is the color you would
        like.
    duration : float, optional, default = None
        The duration you would like this state to last. If None, then this
        state lasts until canceled.
    parent : ParentState, optional, default = None
        The parent of this state. If None, it will be set automatically.
    save_log : boolean, optional, default = True
        If True, this state will save out all of the Logged Attributes.
    name : string, optional
        The unique name to this state.
    blocking : boolean, optional, default = True
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevent if within a *ParallelParent*.
    """
    layers = []

    def __init__(self, color, duration=None, parent=None, save_log=True,
                 name=None, blocking=True):
        super(BackgroundColor, self).__init__(parent=parent,
                                              duration=duration,
                                              save_log=save_log,
                                              name=name,
                                              blocking=blocking)
        self._init_color = color
        self._log_attrs.extend(['color'])

    def show(self):
        BackgroundColor.layers.append(self)
        self._exp._app.set_background_color(self._color)

    def unshow(self):
        if BackgroundColor.layers[-1] is self:
            BackgroundColor.layers.pop()
            try:
                color = BackgroundColor.layers[-1]._color
            except IndexError:
                color = None
            self._exp._app.set_background_color(color)
        else:
            BackgroundColor.layers.remove(self)


class BlockingFlips(VisualState):
    """Force blocking flips when updating the screen.
    """
    layers = []

    def __init__(self, duration=None, parent=None, save_log=True,
                 name=None, blocking=True):
        super(BlockingFlips, self).__init__(parent=parent,
                                            duration=duration,
                                            save_log=save_log,
                                            name=name,
                                            blocking=blocking)

    def show(self):
        BlockingFlips.layers.append(self)
        self._exp._app.force_blocking_flip = len(BlockingFlips.layers) > 0

    def unshow(self):
        if BlockingFlips.layers[-1] is self:
            BlockingFlips.layers.pop()
        else:
            BlockingFlips.layers.remove(self)
        self._exp._app.force_blocking_flip = len(BlockingFlips.layers) > 0


class NonBlockingFlips(VisualState):
    """Force non-blocking flips when updating the screen.
    """
    layers = []

    def __init__(self, duration=None, parent=None, save_log=True,
                 name=None, blocking=True):
        super(NonBlockingFlips, self).__init__(parent=parent,
                                               duration=duration,
                                               save_log=save_log,
                                               name=name,
                                               blocking=blocking)

    def show(self):
        NonBlockingFlips.layers.append(self)
        self._exp._app.force_nonblocking_flip = len(NonBlockingFlips.layers) > 0

    def unshow(self):
        if NonBlockingFlips.layers[-1] is self:
            NonBlockingFlips.layers.pop()
        else:
            NonBlockingFlips.layers.remove(self)
        self._exp._app.force_nonblocking_flip = len(NonBlockingFlips.layers) > 0


class WidgetState(VisualState):
    """A *WidgetState* is used to wrap Kivy widgets into SMILE classes

    SMILE needed a wrapper for Kivy widgets in order for them to interact in a
    meaningful way, so that is why *WidgetState* was written. If you decided to
    go the route of using a custom Kivy widget in SMILE, you'll just need to
    wrap it with *WidgetState* and it should work without much issue.

    Parameters
    ----------
    widget_class : a Kivy Widget
        Pass in a Kivy Widget to get it wrapped.
    duration : float
        In seconds, the duration of this state. If None, it will last
        until canceled.
    parent : ParentState
        The parent of this state, if None, it will be set automatically
    save_log : boolean
        If True, this state will save out all of the Logged Attributes.
    name : string
        The unique name to this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevent if within a *ParallelParent*.
    index : integer
        The index of the widget if it exists within the context of another
        widget.
    layout : Layout (Kivy class)
        Used to calculate and assign widget positions

    Widget Parameters
    -----------------
    These are a kind of parameter that are only associated with the Kivy Widget
    version of this WidgetState. Each Seperate Kivy Widget has its own set of
    parameters that can be set to change the look of the widget.  If you set a
    positional parameter like *center_x* then x will be calculated and set
    appropriately, and visa versa. Any positional parameter being set will echo
    out into the other parameters and change everything that needs to change
    for your parameter set to be valid.

    x : integer (optional)
        x coordinate of the bottom left point of the widget.
    y : integer (optional)
        y coordinate of the bottom left point of the widget.
    pos : tuple (optional)
        (x, y)
    height : integer (optional)
        The height of the widget.
    width : integer (optional)
        The width of the widget.
    size : tuple (optional)
        (height, width)
    center : tuple (optional)
        A tuple of integers that corresponds to the center point of the widget
    center_x : integer (optional)
        The x coordinate of the center of your widget.
    center_y : integer (optional)
        The y coordinate of the center of your widget.
    left : integer (optional)
        The x value that corresponds to the left side of your widget.
    right : integer (optional)
        The x value that corresponds to the right side of your widget.
    left_bottom : tuple (optional)
        (x, y)
    left_top : tuple (optional)
        (x, y + height)
    left_center : tuple (optional)
        (x, (y + height) / 2)
    center_bottom : tuple (optional)
        ((x + width) / 2, y)
    center_top : tuple (optional)
        ((x + width) / 2, y + height)
    right_bottom : tuple (optional)
        (x + width, y)
    right_top : tuple (optional)
        (x + width, y + height)
    right_center : tuple (optional)
        (x + width, (y + height) / 2)
    opacity : float (optional)
        Float between 0 and 1.  The opacity of the widget and its children.
    rotate : float (optional)
        Degree of rotation. Only rotates the image of the WidgetState that is
        drawn to the screen, not the actual widget itself.
    rotate_origin : list (optional)
        For now, this parameter is ignored. The rotate_origin is defaulted to
        the center of a widget. Will be fixed in later releases.

    """
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
                 name=None, blocking=True, index=0, layout=None,
                 rotate=0, rotate_origin=None, **params):
        super(WidgetState, self).__init__(parent=parent,
                                          duration=duration,
                                          save_log=save_log,
                                          name=name,
                                          blocking=blocking)

        self.__issued_refs = weakref.WeakValueDictionary()
        self.__widget_param_names = widget_class().properties().keys()
        self.__widget_class = widget_class
        self._init_index = index
        self._init_rotate = rotate
        self._init_rotate_origin = rotate_origin
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
        self._log_attrs.extend(['constructor_params',
                                'index', 'rotate',
                                'rotate_origin'])

        self.__parallel = None

    def get_attribute_ref(self, name):
        try:
            return self.__issued_refs[name]
        except KeyError:
            try:
                props = WidgetState.property_aliases[name]
            except KeyError:
                if name in self.__widget_param_names + ['rotate', 'rotate_origin']:
                    props = name
                else:
                    return super(WidgetState, self).get_attribute_ref(name)
            if isinstance(props, str):
                ref = Ref(self.get_current_param, props, _parent_state=self)
            elif isinstance(props, tuple):
                # must make this a Ref to tuple or there is a weakref error
                prop_tuple = [Ref(self.get_current_param, prop) for
                              prop in props]
                ref = Ref(tuple, prop_tuple, _parent_state=self)
                #ref = prop_tuple
            else:
                raise RuntimeError("Bad value for 'props': %r" % props)
            self.__issued_refs[name] = ref
            return ref

    def attribute_update_state(self, name, value, index=None):
        if name in self.__widget_param_names + ['rotate', 'rotate_origin']:
            return UpdateWidgetUntimed(self, name, value, index)
        else:
            raise AttributeError("%r is not a property of this widget (%r)." %
                                 (name, self))

    def get_current_param(self, name):
        # important that this is pulling from the current clone
        current_clone = self.current_clone
        if name in ['index', 'rotate', 'rotate_origin']:
            return getattr(current_clone, '_'+name)
        else:
            return getattr(current_clone._widget, name)

    def property_callback(self, name, *pargs):
        # ensure we update dependencies if necessary
        try:
            ref = self.__issued_refs[name]
        except KeyError:
            return
        ref.dep_changed()

    def eval_init_refs(self):
        return self.transform_params(self.apply_aliases(
            {name: getattr(self, "_" + name) for
             name in self._constructor_param_names +
             ['rotate', 'rotate_origin']}))

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
        # elif "rotate_origin" in name and isinstance(value, str):
        #     # convert the string to position based on self
        #     try:
        #         props = WidgetState.property_aliases[value]
        #     except KeyError:
        #         props = value
        #     if isinstance(props, str):
        #         return Ref(self.get_current_param, props,
        #                    current_clone=self)
        #     elif isinstance(props, tuple):
        #         return tuple(Ref(self.get_current_param, prop,
        #                          current_clone=self) for
        #                      prop in props)
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

        # handle rotation
        # will fill None after live_change
        if self._rotate_origin is None:
            rot_orig = (0,0)
        else:
            rot_orig = self._rotate_origin
        self.__rotate_inst = kivy.graphics.Rotate(angle=self._rotate,
                                                  origin=rot_orig)
        self.live_change(**params)
        self._widget.bind(**{name: partial(self.property_callback, name) for
                             name in self.__widget_param_names})

    def _set_widget_defaults(self):
        pass

    def show(self):
        # add the widget to the correct parent to handle drawing
        if self.__layout is None:
            self.__parent_widget = self._exp._app.wid
        else:
            self.__parent_widget = self.__layout.current_clone._widget
        try:
            self.__parent_widget.add_widget(self._widget, index=self._index)
        except TypeError:
            # The ScatterLayout does not have an index
            self.__parent_widget.add_widget(self._widget)

        # handle rotation
        self._widget.canvas.before.add(kivy.graphics.PushMatrix())
        #self.__rotate_inst = kivy.graphics.Rotate(angle=self._rotate,
        #                                          )#origin=self._rotate_origin)
        self._widget.canvas.before.add(self.__rotate_inst)
        self._widget.canvas.after.add(kivy.graphics.PopMatrix())

    def unshow(self):
        # remove the widget from the parent
        self.__parent_widget.remove_widget(self._widget)
        self.__parent_widget = None

    def live_change(self, **params):
        # first remove rotation params b/c they don't go to widget
        rot_params = {rp: params.pop(rp)
                      for rp in ['rotate', 'rotate_origin']
                      if rp in params}

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

        # set the rotation info
        if 'rotate' in rot_params:
            self._rotate = rot_params['rotate']
            self.__rotate_inst.angle = self._rotate
        if 'rotate_origin' in rot_params:
            if rot_params['rotate_origin'] is None:
                # defaults to center of widget
                rot_params['rotate_origin'] = list(self._widget.center)
            self._rotate_origin = rot_params['rotate_origin']
            self.__rotate_inst.origin = self._rotate_origin
            pass

    def update(self, parent=None, save_log=True, name=None, blocking=True,
               **kwargs):
        """
        Creates an **UpdateWidget** state that updates the passed in parameters

        Parameters
        ----------
        parent : ParentState, optional
            The parent of this state, if None, it will be set automatically
        save_log : boolean, optional
            If True, this state will save out all of the Logged Attributes.
        name : string , optional
            The unique name to this state.
        blocking : boolean, optional, default = True
            If True, this state will prevent a *Parallel* state from ending. If
            False, this state will be canceled if its *ParallelParent* finishes
            running. Only relevent if within a *ParallelParent*.
        kwargs : Keyword = Argument
            The keywords and values you would like to update this widget with.

        Returns
        -------
        UpdateWidget(self, parent, save_log, name, blocking, **kwargs)
        """
        ud = UpdateWidget(self,
                          parent=parent,
                          save_log=save_log,
                          name=name,
                          blocking=blocking,
                          **kwargs)
        ud.override_instantiation_context()
        return ud

    def animate(self, interval=None, duration=None, parent=None, save_log=True,
                name=None, blocking=True, **anim_params):
        """Returns a created animate state with specific animate parameters

        This function call will create an Animate state during experimental
        build time and run the animate at the correct spot during experimental
        runtime. Animate is used to change a value of a property of a state
        over the course of a duration. This state will do all of the
        calculations of how much the property needs to change each frame to
        last the entire duration. You can animate anything from the height,
        width, x, and y to the color of a rectangle.

        Parameters
        ----------
        interval : float
            A frequency value. If not set, it is None, Animate will update at
            the same interval as the frame-rate.  You cannot set interval to any
            number faster than the frame-rate.
        duration : float
            A duration, in seconds, that the Animate state will animate the
            changes to the target's properties. Over the course of a duration,
            animate will gradually change the value of a parameter.
        parent : ParentState, optional
            The parent of this state, if None, it will be set automatically
        save_log : boolean, optional
            If True, this state will save out all of the Logged Attributes.
        name : string , optional
            The unique name to this state.
        blocking : boolean, optional, default = True
            If True, this state will prevent a *Parallel* state from ending. If
            False, this state will be canceled if its *ParallelParent* finishes
            running. Only relevent if within a *ParallelParent*.
        anim_params : (keyword = argument)
            These keywords have to be parameters or properties of the Kivy
            widget passed in through this state that are to be changed over the
            course of the Animate state.

        """
        anim = Animate(self, interval=interval, duration=duration,
                       parent=parent, name=name, save_log=save_log,
                       blocking=blocking, **anim_params)
        anim.override_instantiation_context()
        return anim

    def slide(self, interval=None, duration=None, speed=None, accel=None,
              parent=None, save_log=True, name=None, blocking=True, **params):
        """Like animate, but you are able to give a duration and the option to
        give a speed and acceleration.

        """
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
        anim = self.animate(interval=interval, duration=duration,
                            parent=parent, save_log=save_log, name=name,
                            blocking=blocking, **anim_params)
        anim.override_instantiation_context()  # PBS: Is this line needed (see animate)?
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
        # TODO: make sure we're the previous state?
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


class UpdateWidgetUntimed(CallbackState):
    def __init__(self, target, prop_name, prop_value, prop_index=None,
                 parent=None, save_log=True, name=None, blocking=True):
        super(UpdateWidgetUntimed, self).__init__(duration=0.0,
                                                  parent=parent,
                                                  save_log=save_log,
                                                  name=name,
                                                  blocking=blocking)
        self.__target = target
        self._widget = target._name
        self._init_prop_name = prop_name
        self._init_prop_value = prop_value
        self._init_prop_index = prop_index
        self._log_attrs.extend(['widget', 'prop_name', 'prop_value',
                                'prop_index'])

    def _enter(self):
        super(UpdateWidgetUntimed, self)._enter()
        self.__target_clone = self.__target.current_clone

    def _callback(self):
        # set the param
        if self._prop_index is None:
            # set the value from what was passed in
            full_value = self._prop_value
        else:
            # get the current param value
            full_value = self.__target.get_attribute_ref(self._prop_name).eval()

            # set the index with the value
            full_value[self._prop_index] = self._prop_value

        # update the widget
        params = self.__target_clone.transform_params(
            self.__target_clone.apply_aliases(
                {self._prop_name: full_value}))

        # do the live_change
        self.__target_clone.live_change(**params)


class UpdateWidget(VisualState):
    """ A state used to change widget parameters in Experimental Run Time.

    You call this state in your experiment if you want to change the parameters
    of a widget in experimental runtime. You can change anything that is a
    property of the **VisualState**, or a property of the Kivy Widget.
    **UpdateWidget** will call the *target* **VisualState**'s method called
    *live_change* when the experiment clock calls *show*.

    Parameters
    ----------
    target : VisualState (a wrapped Kivy Widget)
        The target for the change set in motion by update widget.
    parent : ParentState
        The parent of this state, if None, it will be set automatically
    save_log : boolean
        If True, this state will save out all of the Logged Attributes.
    name : string
        The unique name to this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevent if within a *ParallelParent*.
    kwargs : (keyword = argument)
        These keywords have to be parameters or properties of the Kivy
        widget passed in through *target*.

    Logged Attributes
    -----------------
    All parameters above are available to be accessed and manipulated within
    the experiment code, and will be automatically recorded in the
    state-specific log. Refer to **VisualState** and **State** classes
    docstring for additional logged parameters.

    time : dictionary
        The keys *time* and *error* are associated with the appear time of the
        UpdateWidget state. *time* points to the approximate time that the
        update happens.

    """
    def __init__(self, target, parent=None, save_log=True, name=None,
                 blocking=True, **kwargs):
        super(UpdateWidget, self).__init__(duration=0.0,
                                           parent=parent,
                                           save_log=save_log,
                                           name=name,
                                           blocking=blocking)
        self.__target = target
        self._widget = target._name
        self._init_values = kwargs
        self._log_attrs.extend(['widget', 'values'])

    def _enter(self):
        super(UpdateWidget, self)._enter()
        self.__target_clone = self.__target.current_clone

    def show(self):
        self.__target_clone.live_change(**self.__target_clone.transform_params(
            self.__target_clone.apply_aliases(self._values)))

    def get_log_fields(self):
        return ['instantiation_filename', 'instantiation_lineno', 'name',
                'time', 'prop_name', 'prop_value']

    def save_log(self):
        class_name = type(self).__name__
        for name, value in self._values.iteritems():
            field_values = {
                "instantiation_filename": self._instantiation_filename,
                "instantiation_lineno": self._instantiation_lineno,
                "name": self._name,
                "time": self._appear_time,
                "prop_name": name,
                "prop_value": value}
            self._exp.write_to_state_log(class_name, field_values)


class Animate(State):
    """A state that will animate the changes of properties over a duration.

    This state will calculate how much a given property of a Kivy Widget needs
    to change each frame, so that it will be completed at the end of a
    duration. It is an extremely strong state that can do anything from blend
    one color of a rectangle state into another over 5 seconds, to completely
    change the height and width of an image over a duration.

    Parameters
    ----------
    target : WidgetState
        This is the widget that will be changed during the Animate state.
    interval : float
        A frequency value. If not set, it is None, Animate will update at
        the same interval as the frame-rate.  You cannot set interval to any
        number faster than the frame-rate.
    duration : float
        A duration, in seconds, that the this state will changes the values
        of the anim_params over.
    parent : ParentState
        The parent of this state, if None, it will be set automatically
    save_log : boolean
        If True, this state will save out all of the Logged Attributes.
    name : string
        The unique name to this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevent if within a *ParallelParent*.
    anim_params : (keyword = argument)
        These keywords have to be parameters or properties of the Kivy
        widget passed in through *target* that are to be changed over the
        course of the Animate state's duration.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state-specific log. Refer to State class
    docstring for additional logged parameters.

    Example
    -------

    ::

        exp = Experiment()
        rn = Rectangle(color="BLUE", duration = 6)
        with UntilDone():
            Wait(2)
            Animate(rn, duration=3, color="GREEN")

    This example will show a blue box, and after waiting 2 seconds it will
    gradually change the color of the box to green over the course of 3
    seconds.


    """
    # TODO: log updates!
    def __init__(self, target, interval=None, duration=None, parent=None,
                 save_log=True, name=None, blocking=True, **anim_params):
        super(Animate, self).__init__(duration=duration, parent=parent,
                                      save_log=save_log, name=name,
                                      blocking=blocking)
        self.__target = target  # TODO: make sure target is a WidgetState
        self.__anim_params = anim_params
        self.__initial_params = None
        self._init_interval = interval

    def _schedule_start(self):
        first_update_time = self._start_time + self._interval
        clock.schedule(self.update, event_time=first_update_time,
                       repeat_interval=self._interval)

    def _unschedule_start(self):
        clock.unschedule(self.update)

    def _enter(self):
        self.__initial_params = None
        self.__target_clone = self.__target.current_clone
        if self._interval is None:
            self._interval = self._exp._app.flip_interval

    def update(self):
        self.claim_exceptions()
        self._started = True
        now = clock.now()
        if self.__initial_params is None:
            # get values from the target (not the target_clone)
            # because get_attribute_ref looks up the target clone
            self.__initial_params = {
                name: self.__target.get_attribute_ref(name).eval() for
                name in self.__anim_params.iterkeys()}

            # we can leave now that we have initial params
            clock.schedule(self.leave)

        if self._end_time is not None and now >= self._end_time:
            clock.unschedule(self.update)
            clock.schedule(self.finalize)
            now = self._end_time
        t = now - self._start_time
        params = {name: func(t, self.__initial_params[name]) for
                  name, func in
                  self.__anim_params.iteritems()}
        self.__target_clone.live_change(
            **self.__target_clone.transform_params(
                self.__target_clone.apply_aliases(params)))


def vertex_instruction_widget(instr_cls, name=None):
    """The widget wrapper for special drawing functions like *Rectangle*.

    This class was created as a wrapper for all of the vertex Kivy
    instructions. These these instructions range from *Rectangle* to *Bezier*.
    This class sets up the method *redraw* which is needed by these
    instructions.
    """
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

WSP_doc_addition = """Logged Attributes
-----------------
All parameters above are available to be accessed and
manipulated within the experiment code, and will be automatically
recorded in the state-specific log. Refer to WidgetState class
docstring for additional logged parameters.

appear_time : dictionary
    The keys are *time* and *error*. Where *time* refers to the time the
    visual stimulus appeared on the screen, and *error* refers to the
    maximum error in calculating the appear time of the stimulus.
disappear_time : dictionary
    The keys are *time* and *error*. Where *time* refers to the time the
    visual stimulus disappeared from the screen, and *error* refers to the
    maximum error in calculating the disappear time of the stimulus.
    """


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


Bezier.__doc__ = """A **WidgetState** that creates a 2D Bezier curve.

Use this State to create a Bezier curve somewhere in the experiment window.

A **WidgetState** that shows a button in the window.

Use this state when you would like to show a button on the screen. This State
will display a button that can be clicked by a mouse cursor. When used in
conjunction with the **ButtonPress** state, you can create multiple buttons, all
with different colors, text, or even images.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

points : list (Parameter)
    List of points in the format (x1, y1, x2, y2...)
segments : integer (Parameter, optional, default=180)
    Define how many segments are needed for drawing the curve. The drawing will
    be smoother if you have many segments.
loop : boolean (Parameter, optional, default=False)
    Set the bezier curve to join the last point to the first.
dash_length : integer (Parameter, optional, default=1)
    Length of a segment (if dashed).
dash_offset : integer (Parameter, optional, default=0)
    Distance between the end of a segment and the start of the next one,
    Changing this makes it dashed.
color : list (Parameter, optional, default=[1.0, 1.0, 1.0, 1.0])
    The color in the bezier (r, g, b, a) format.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.graphics.bezier. <https://kivy.org/docs/api-kivy.graphics.html?highlight=bezier#kivy.graphics.Bezier>'_

"""
Mesh.__doc__ = """A **WidgetState** that allows you to freehand draw shapes.

Depending on the shape of *vertices* and *indices*, you can draw all kinds of
different shapes.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

vertices : list (Parameter)
    List of vertices in the format (x1, y1, u1, v1, x2, y2, u2, v2...).
indices : list (Parameter)
    List of indices in the format (i1, i2, i3...).
mode : string (Parameter, optional, default="points")
    Mode of the vbo. Can be one of "points", "line_strip", "line_loop",
    "lines", "triangles", "triangle_strip" or "triangle_fan".
fmt : list (Property)
    The format for vertices, by default, each vertex is described by 2D
    coordinates (x, y) and 2D texture coordinate (u, v). Each element of the
    list should be a tuple or list, of the form

        (variable_name, size, type)

    which will allow mapping vertex data to the glsl instructions.

        [(b"v_pos", 2, b"float"), (b"v_tc", 2, b"float"),]

    will allow using

        attribute vec2 v_pos; attribute vec2 v_tc;

    in glsl's vertex shader.
color : list (Parameter, optional, default=[1.0, 1.0, 1.0, 1.0])
    The color of this mesh in (r, g, b, a) format.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.graphics.mesh. <https://kivy.org/docs/api-kivy.graphics.html?highlight=mesh#kivy.graphics.Mesh>'_

"""
Point.__doc__ = """A **WidgetState that draws a bunch of points.

You can list any number of points and the **Point** state will draw all of them. s

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

points : list (Parameter)
    List of points in the format (x1, y1, x2, y2, ...).
pointsize : float (Parameter, optional, default=1)
    The size of the point, measured from the center to the edge. A value of 1.0
    therefore means the real size will be 2.0 x 2.0.
color : list (Parameter, optional, default=[1.0, 1.0, 1.0, 1.0])
    The color of the points being draw in (r, g, b, a) format.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.graphics.Point. <https://kivy.org/docs/api-kivy.graphics.html?highlight=kivy.graphics.point#kivy.graphics.Point>'_

"""
Triangle.__doc__ = """A **WidgetState** that shows a triangle on the screen.

With 3 sets of points, you can define a triangle to be presented in your
experiment. You can also set the color.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

points : list (Parameter)
    List of points in the format (x1, y1, x2, y2, x3, y3).
color : list (Parameter, optional, default=[1.0, 1.0, 1.0, 1.0])
    The color of the Triangle in (r, g, b, a) format.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.graphics.Triangle. <https://kivy.org/docs/api-kivy.graphics.html?highlight=kivy.graphics.triangle#kivy.graphics.Triangle>'_

"""

Quad.__doc__ = """A **WidgetState** that can draw a Quadrangle.

Use this State to draw any 4 sided shape onto the screen.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

points : list (Parameter)
    List of points in the format (x1, y1, x2, y2, x3, y3, x4, y4).
color : list (Parameter, optional, defaut=[1.0, 1.0, 1.0, 1.0])
    The color of the quadrangle in (r, g, b, a) format.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.graphics.Quad. <https://kivy.org/docs/api-kivy.graphics.html?highlight=kivy.graphics.quad#kivy.graphics.Quad>'_

"""
Rectangle.__doc__ = """A **WidgetState** to display a rectangle on the screen.

You can set the color, height, width, x, y, and all the other positional
properties of this state.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the rectangle in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the rectangle in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.
color : list (Parameter, optional, default=[1.0, 1.0, 1.0, 1.0])
    The color of the rectangle in (r, g, b, a) format.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.graphics.Rectangle. <https://kivy.org/docs/api-kivy.graphics.html?highlight=rectangle#kivy.graphics.Rectangle>'_

"""
BorderImage.__doc__ = """A **WidgetState** that creates 4 Rectangles around an area.

This 2d border image creates rectangles at a postion depending on the parameters
passed in. You can use any of the parameters or properties that a **Rectagnle**
State has access to.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

border : list (Parameter, optional, default=[])
"""
Ellipse.__doc__ = """A **WidgetState** that produces a 2D ellipse.

Use this **WidgetState** to produce an ellipse of any size or color.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

segments : integer (Parameter, optional, default=180)
    Define how many segments are needed for drawing the ellipse. The drawing
    will be smoother if you have many segments.
angle_start : integer (Parameter, optional, default=0)
    Specifies the starting angle, in degrees, of the disk portion.
angle_end : integer (Parameter, optional, default=360)
    Specifies the ending angle, in degrees, of the disk portion.
width : integer (Parameter, optional, default=50)
    The horizontal size of the Ellipse.
height : integer (Parameter, optional, default=50)
    The vertical size of the Ellipse.
color : list (Parameter, optional, default=[1.0, 1.0, 1.0, 1.0])
    The color of the ellipse in (r, g, b, a) format.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.graphics.Ellipse. <https://kivy.org/docs/api-kivy.graphics.html?highlight=ellipse#kivy.graphics.Ellipse>'_

"""
for instr in vertex_instructions:
    exec("%s.__doc__ = %s.__doc__ + WSP_doc_addition" %
         (instr, instr))





def _sp(value):
    return float(value)
_sp_save = kivy.metrics.sp
kivy.metrics.sp = _sp

# load the widgets
widgets = [
    "Button",
    "Slider",
    "TextInput",
    "ToggleButton",
    "ProgressBar",
    "CodeInput",
    "CheckBox",
    "Camera",

    #...
    "AnchorLayout",
    "BoxLayout",
    "FloatLayout",
    "RelativeLayout",
    "GridLayout",
    "PageLayout",
    "ScatterLayout",
    "StackLayout",
    "ScrollView",
    ]
for widget in widgets:
    modname = "kivy.uix.%s" % widget.lower()
    exec("import %s" % modname)
    exec("%s = WidgetState.wrap(%s.%s)" %
         (widget, modname, widget))

Button.__doc__ = """
A **WidgetState** that shows a button in the window.

Use this state when you would like to show a button on the screen. This State
will display a button that can be clicked by a mouse cursor. When used in
conjunction with the **ButtonPress** state, you can create multiple buttons, all
with different colors, text, or even images.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

background_color : list (Parameter, optional, default=[1.0, 1.0, 1.0, 1.0])
    Background color, in the format (r, g, b, a).

    This acts as a multiplier to the texture colour. The default texture is
    grey, so just setting the background color will give a darker result. To set
    a plain color, set the background_normal to "".
background_disabled_down : string (Parameter, optional, default="atlas://data/images/defaulttheme/button_disabled_pressed")
    Background image of the button used for the default graphical representation
    when the button is disabled and pressed.
background_disabled_normal : string (Parameter, optional, default="atlas://data/images/defaulttheme/button_disabled")
    Background image of the button used for the default graphical representation
    when the button is disabled and not pressed.
background_down : string (Parameter, optional, default="atlas://data/images/defaulttheme/button_pressed")
    Background image of the button used for the default graphical representation
    when the button is pressed.
background_normal : string (Parameter, optional, default="atlas://data/images/defaulttheme/button")
    Background image of the button used for the default graphical representation
    when the button is not pressed.
border : list (Parameter, optional, default=[16, 16, 16, 16])
    Border used for BorderImage graphics instruction. Used with
    background_normal and background_down. Can be used for custom backgrounds.

    It must be a list of four values: (top, right, bottom, left). Read the
    BorderImage instruction for more information about how to use it.
state : string (Property)
    The state of the button, must be one of "normal" or "down". The state is
    "down" only when the button is currently touched/clicked, otherwise its
    "normal".

See **Label** for other Kivy Parameters. Most parameters that can be passed into
**Label** can be passed into Button.

See **ButtonPress** for an example on how to use buttons.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.button. <https://kivy.org/docs/api-kivy.uix.button.html>'_
"""

Slider.__doc__ = """A **WidgetState** to display a Slider style input.

This state will display a varying size Slider that can be used in conjunction
with a **MouseCursor** to record a continuum input for your experiment.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

max : integer (Parameter, optional, default=100)
    Maximum value allowed for *value*.
min : integer (Parameter, optional, default=0)
    Minimum value allowed for *value*.
orientation : string (Parameter, optional, default="horizontal")
    Orientation of the slider. Can take a value of "vertical" or "horizontal".
padding : integer (Parameter, optional, default=16)
    Padding of the slider. The padding is used for graphical representation and
    interaction. It prevents the cursor from going out of the bounds of the
    slider bounding box.

    By default, padding is 16sp. The range of the slider is reduced from
    padding*2 on the screen. It allows drawing the default cursor of 32sp width
    without having the cursor go out of the widget.
range : list (Property)
    Range of the slider in the format (minimum value, maximum value).
step : float (Parameter, optional, default=1)
    Step size of the slider.

    Determines the size of each interval or step the slider takes between min
    and max. If the value range can't be evenly divisible by step the last step
    will be capped by slider.max
value : float (Property)
    Current value used for the slider.
value_normalized : float (Property)
    Normalized value inside the range (min/max) to 0-1 range.
value_pos : float (Property)
    Position of the internal cursor, based on the normalized value.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.slider. <https://kivy.org/docs/api-kivy.uix.slider.html>'_


"""

TextInput.__doc__ = """A **WidgetState** that will display a box for typing text.

With this **WidgetState**, you can display a box that allows participants to
enter text. This text box can be of any size on the screen, be single or multi
line, and even restrict the kinds of characters that can be typed into it.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

text : string (Parameter, optional, default="")
    Text of the widget
allow_copy : boolean (Parameter, optional, default=True)
    Decides whether to allow copying the text.
auto_indent : boolean (Parameter, optional, default=False)
    Automatically indent multiline text.
background_active : string (Parameter, optional, default="atlas://data/images/defaulttheme/textinput_active")
    Background image of the TextInput when it's in focus.
background_color : list (Parameter, optional, default=[1.0, 1.0, 1.0, 1.0])
    Current color of the background, in (r, g, b, a) format.
foreground_color : list (Parameter, optional, default=[0.0, 0.0, 0.0, 1.0])
    Current color of the foreground, in (r, g, b, a) format.
disabled_foreground_color : list (Parameter, optional, default=[0.0, 0.0, 0.0, 0;5])
    Current color of the foreground when disabled, in (r, g, b, a) format.
background_disabled_normal : string (Parameter, optional, default="atlas://data/images/defaulttheme/textinput_disabled")
    Background image of the TextInput when disabled.
background_normal : string (Parameter, optional, default="atlas://data/images/defaulttheme/textinput")
    Background image of the TextInput when it's not in focus.
border : list (Parameter, optional, default=[4.0, 4.0, 4.0, 4.0])
    Border used for BorderImage graphics instruction. Used with
    background_normal and background_active. Can be used for a custom
    background.

    It must be a list of four values: (top, right, bottom, left). Read the
    BorderImage instruction for more information about how to use it.
cursor : tuple (Property)
    Tuple of (row, col) values indicating the current cursor position. You can
    set a new (row, col) if you want to move the cursor. The scrolling area will
    be automatically updated to ensure that the cursor is visible inside the
    viewport.
cursor_col : integer (Property)
    Current column of the cursor.
cursor_row : integer (Property)
    Current row of the cursor.
cursor_blink : boolean (Parameter, optional, default=False)
    This property is used to blink the cursor graphic. The value of cursor_blink
    is automatically computed. Setting a value on it will have no impact.
cursor_pos : tuple (Property)
    Current position of the cursor, in (x,y)
font_name : string (Parameter, optional, default="Roboto")
    Filename of the font to use. The path can be absolute or relative.
font_size : integer (Parameter, optional, default=10)
    Font size of the text in pixels.
handle_image_left : string (Parameter, optional, default="atlas://data/images/defaulttheme/selector_left")
    Image used to display the Left handle on the TextInput for selection.
handle_image_middle : string (Parameter, optional, default="atlas://data/images/defaulttheme/selector_middle")
    Image used to display the middle handle on the TextInput for cursor
    positioning.
handle_image_right : string (Parameter, optional, default="atlas://data/images/defaulttheme/selector_right")
    Image used to display the Right handle on the TextInput for selection.
hint_text : string (Parameter, optional, default="")
    Hint text of the widget, shown if text is "".
hint_text_color : list (Parameter, optional, default=[0.5, 0.5, 0.5, 1.0])
    Current color of the hint_text text, in (r, g, b, a) format.
input_filter : object (Parameter, optional, default=None)
    Filters the input according to the specified mode, if not None. If None, no
    filtering is applied. Can be one of None, "int" (string), or
    "float" (string), or a callable. If it is "int", it will only accept
    numbers. If it is "float" it will also accept a single period. Finally, if
    it is a callable it will be called with two parameter; the string to be
    added and a bool indicating whether the string is a result of undo (True).
    The callable should return a new substring that will be used instead.
line_height : integer (Property, read-only)
    Height of a line. This property is automatically computed from the
    font_name, font_size. Changing the line_height will have no impact.
line_spacing : integer (Parameter, optional, default=0)
    Space taken up between the lines.
minimum_height : integer (Property, read-only)
    Minimum height of the content inside the TextInput.
multiline : boolean (Parameter, optional, default=True)
    If True, the widget will be able show multiple lines of text. If False, the
    "enter" keypress will defocus the textinput instead of adding a new line.
padding : list (Parameter, optional, default=[6, 6, 6, 6])
    Padding of the text: [padding_left, padding_top,
    padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].
password : boolean (Parameter, optional, default=False)
    If True, the widget will display its characters as the character set in password_mask.
paddword_mask : string (Parameter, optional, default="*")
    Sets the character used to mask the text when password is True.
readonly : boolean (Parameter, optional, default=False)
    If True, the user will not be able to change the content of a textinput.
scroll_x : integer (Parameter, optional, default=0)
    X scrolling value of the viewport. The scrolling is automatically updated
    when the cursor is moved or text changed. If there is no user input, the
    scroll_x and scroll_y properties may be changed.
scroll_y : integer (Parameter, optional, default=0)
    Y scrolling value of the viewport. See scroll_x for more information.
selection_color : list (Parameter, optional, default= [0.1843, 0.6549, 0.8313, .5])
    Current color of the selection, in (r, g, b, a) format.
selection_from : list (Property)
    If a selection is in progress or complete, this property will represent the
    cursor index where the selection started.
selection_to : list (Property)
    If a selection is in progress or complete, this property will represent the
    cursor index where the selection ends.
selection_text : string (Property)
    Current content selection.
suggestion_text : string (Parameter, optional, default="")
    Shows a suggestion text at the end of the current line. The feature is
    useful for text autocompletion, and it does not implement validation
    (accepting the suggested text on enter etc.). This can also be used by the
    IME to setup the current word being edited.
tab_width : integer (Parameter, optional, default=4)
    By default, each tab will be replaced by four spaces on the text input
    widget. You can set a lower or higher value.
use_bubble : boolean (Parameter, optional, default=True on Mobile OS's, and False on Desktop OS's)
    Indicates whether the cut/copy/paste bubble is used.
use_handles : boolean (Parameter, optional, default=True on mobile OS's, False on desktop OS's)
    Indicates whether the selection handles are displayed.
write_tab : boolean (Parameter, optional, default=True)
    Whether the tab key should move focus to the next widget or if it should
    enter a tab in the TextInput. If True a tab will be written, otherwise,
    focus will move to the next widget.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.textinput. <https://kivy.org/docs/api-kivy.uix.textinput.html>'_
"""

ToggleButton.__doc__ = """A **WidgetState** that toggles on and off.

This widget state can use all of the same parameters and properties of the
**Button** state. **ToggleButtons** with the same *group* parameter can be used
as a set of radio buttons, where only one can be pressed at a time.
**ToggleButtons** with no *group* parameter set can be used as check boxes,
where the participant can check as many as they want.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

state : string (Parameter, optional, default="normal")
    When you touch/click it, the state toggles between "normal" and "down"
    (as opposed to a Button that is only "down" as long as it is pressed).
group : string (Parameter, optional, default="")
    Toggle buttons can also be grouped to make radio buttons - only one button
    in a group can be in a "down" state. The group name can be a string or any
    other hashable Python object.

See smile.video.Button for all the other parameters and properties that can be
used by this state.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.togglebutton. <https://kivy.org/docs/api-kivy.uix.togglebutton.html>'_
"""

ProgressBar.__doc__ = """A **WidgetState** used to visualize progress.

You can use this State in parallel with a **Loop** and an **UpdateWidget** to
change the value of a **ProgressBar** over time. This widget isn't interactive.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

max : integer (Parameter, optional, default=100)
    Maximum value allowed for *value*.
value : integer (Parameter, optional, default=0)
    Current value used for the slider. Can be set later to a different value.
value_normalized : float (Property)
    Normalized value inside the range 0-1.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.progressbar. <https://kivy.org/docs/api-kivy.uix.progressbar.html>'_
"""

CodeInput.__doc__ = """A **WidgetState** that is an editable box.

This State supports all all the same features as a **TextInput** but also allows
highlighting in different programming languages.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

lexer : object (Parameter, optional, default=PythonLexer)
    This holds the selected Lexer used by pygments to highlight the code.
style : object (Parameter, optional, default=None)
    The pygments style object to use for formatting.

    When style_name is set, this will be changed to the corresponding style
    object.
style_name : string (Parameter, optional, default="default")
    Name of the pygments style to use for formatting.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.codeinput. <https://kivy.org/docs/api-kivy.uix.codeinput.html>'_

"""

CheckBox.__doc__ = """A **WidgetState** that is like a **ToggleButton**.

The biggest differences in this and a **ToggleButton** is that within a group,
a **CheckBox** has a different set of images than when not in a group. Within a
group the images take on the look of radio buttons by default, and without a
group, the images take on the look of check boxes.

active : boolean (Parameter, optional, default=False)
    Indicates if the switch is active or inactive.
background_checkbox_disabled_down : string (Parameter, optional, default="atlas://data/images/defaulttheme/checkbox_disabled_on")
    Background image of the checkbox used for the default graphical
    representation when the checkbox is disabled and active.
background_checkbox_disabled_normal : string (Parameter, optional, default="atlas://data/images/defaulttheme/checkbox_disabled_off")
    Background image of the checkbox used for the default graphical
    representation when the checkbox is disabled and not active.
background_checkbox_down : string (Parameter, optional, default="atlas://data/images/defaulttheme/checkbox_on")
    Background image of the checkbox used for the default graphical
    representation when the checkbox is active.
background_checkbox_normal : string (Parameter, optional, default="atlas://data/images/defaulttheme/checkbox_off")
    Background image of the checkbox used for the default graphical
    representation when the checkbox is not active.
background_radio_disabled_down : string (Parameter, optional, default="atlas://data/images/defaulttheme/checkbox_radio_disabled_on")
    Background image of the radio button used for the default graphical
    representation when the radio button is disabled and active.
background_radio_disabled_normal : string (Parameter, optional, default="atlas://data/images/defaulttheme/checkbox_radio_disabled_off")
    Background image of the radio button used for the default graphical
    representation when the radio button is disabled and not active.
background_radio_down : string (Parameter, optional, default="atlas://data/images/defaulttheme/checkbox_radio_on")
    Background image of the radio button used for the default graphical
    representation when the radio button is active.
background_radio_normal : string (Parameter, optional, default="atlas://data/images/defaulttheme/checkbox_radio_off")
    Background image of the radio button used for the default graphical
    representation when the radio button is not active.
color : list (Parameter, optional, default=[1.0, 1.0, 1.0, 1.0])
    Color is used for tinting the default graphical representation of checkbox
    and radio button (images).

    Color is in the format (r, g, b, a). Use alpha greater than 1 for brighter
    colors. Alpha greater than 4 causes blending border and check mark together.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.checkbox. <https://kivy.org/docs/api-kivy.uix.checkbox.html>'_


"""

Camera.__doc__ = """A **WidgetState** is used to capture and display video.

This State can display what a webcam on a desktop or a camera on your phone
sees. You can also save out the *texture* property this state to take a picture.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

play : boolean (Parameter, optional, default=True)
    Boolean indicating whether the camera is playing or not. You can start/stop
    the camera by setting this property.
resolution : list (Parameter, optional, default=[-1, -1])
    Preferred resolution to use when invoking the camera. If you are using
    [-1, -1], the resolution will be the default one.

See smile.video.Image for all the other parameters and properties that can be
used by this state.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.camera. <https://kivy.org/docs/api-kivy.uix.camera.html>'_

"""


AnchorLayout.__doc__ = """A Layout designed to put its children aligned with the border.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

anchor_x : string (Parameter, optional, default="center")
    Horizontal anchor.
anchor_y : string (Parameter, optional, default="center")
    vertical anchor.
padding : list (Parameter, optional, default=[0, 0, 0, 0])
    Padding between the widget box and its children, in pixels: [padding_left,
    padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.AnchorLayout. <https://kivy.org/docs/api-kivy.uix.anchorlayout.html>'_

"""

BoxLayout.__doc__ = """A **WidgetState** arranges children in a verical or horizontal Line.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

minimum_height : integer (Property)
    Automatically computed minimum height needed to contain all children.
minimum_width : integer (Property)
    Automatically computed minimum width needed to contain all children.
minimum_size : list (Property)
    Automatically computed minimum size needed to contain all children.
orientation : string (Parameter, optional, default="horizontal")
    Orientation of the layout, can be "horizontal" or "vertical".
padding : list (Parameter, optional, default=[0, 0, 0, 0])
    Padding between the widget box and its children, in pixels: [padding_left,
    padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].
spacing : integer (Parameter, optional, default=0)
    Spacing between children, in pixels.
pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.BoxLayout. <https://kivy.org/docs/api-kivy.uix.boxlayout.html>'_

"""
FloatLayout.__doc__ = """A **WidgetState** where the postion of the children is realitive to the Experiment Screen.

If you move the position of the **FloatLayout**, then you must also change the
positions of its children manually.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.FloatLayout. <https://kivy.org/docs/api-kivy.uix.floatlayout.html>'_

"""
RelativeLayout.__doc__ = """A **WidgetState** Layout where its children are positioned realitive to itself.

In this layout, all of the **WidgetStates** that are children of it use the
position of this layout as (0, 0). Also if you update the position of this
layout, the positions of the **WidgetStates** within will also be updated
automatically.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.RelativeLayout. <https://kivy.org/docs/api-kivy.uix.relativelayout.html>'_

"""
GridLayout.__doc__ = """A **WidgetState** that arranges children in a matrix.

This layout takes the available size of the layout, and splits it evenly between
its children based on the number of columns and rows that are set in the
parameters of the layout.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.
rows : integer (Parameter, optional, default=0)
    Number of rows in the grid.
row_default_height : integer (Parameter, optional, default=0)
    Default minimum size to use for a height.
row_force_default : boolean (Parameter, optional, default=False)
    If True, ignore the height and size_hint_y of the child and use the default
    row height.
row_minimum : dictionary (Parameter, optional, default={})
    Dict of minimum height for each row. The dictionary keys are the row
    numbers, e.g. 0, 1, 2...
cols : integer (Parameter, optional, default=0)
    Number of columns in the grid.
col_default_width : integer (Parameter, optional, default=0)
    Default minimum size to use for a column.
col_force_default : boolean (Parameter, optional, default=False)
    If True, ignore the width and size_hint_x of the child and use the default
    column width.
col_minimum : dictionary (Parameter, optional, default={})
    Dict of minimum width for each column. The dictionary keys are the column
    numbers, e.g. 0, 1, 2...
minimum_height : integer (Property)
    Automatically computed minimum height needed to contain all children.
minimum_width : integer (Property)
    Automatically computed minimum width needed to contain all children.
minimum_size : list (Property)
    Automatically computed minimum size needed to contain all children.
padding : list (Parameter, optional, default=[0, 0, 0, 0])
    Padding between the widget box and its children, in pixels: [padding_left,
    padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].
spacing : integer (Parameter, optional, default=0)
    Spacing between children, in pixels.


For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.GridLayout. <https://kivy.org/docs/api-kivy.uix.gridlayout.html>'_


"""
PageLayout.__doc__ = """A **WidgetState** used to create a paged layout.

Use this **WidgetState** to when you want to create a set of pages that can be
*swiped* around. When used in conjuction with other layouts, each layout will be
a different page.

Example
-------

::

    from smile.common import *

    exp = Experiment()

    with PageLayout(size=exp.screen.size) as pg:
        with RelativeLayout():
            Label(text="bob", x=20, y=20, font_size=100)
        with GridLayout(rows=2):
            Button(text="ROWS : 2")
            Button(text="ROWS : 2")
            Button(text="ROWS : 2")
            Button(text="ROWS : 2")
            Button(text="ROWS : 2")
        with RelativeLayout(size=pg.size, x=0, y=0):
            Rectangle(size=pg.size)
            with GridLayout(cols=3):
                Button(text="COLS : 3")
                Button(text="COLS : 3")
                Button(text="COLS : 3")
                Button(text="COLS : 3")
                Button(text="COLS : 3")

    with Meanwhile():
        MouseCursor()
    exp.run()

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.
border : integer (Parameter, optional, default=50)
    The width of the border around the current page used to display the
    previous/next page swipe areas when needed.
page : integer (Property)
    The currently displayed page.
swipe_threshold : float (Parameter, optional, default=0.5)
    The thresold used to trigger swipes as percentage of the widget size.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.PageLayout. <https://kivy.org/docs/api-kivy.uix.pagelayout.html>'_

"""
ScatterLayout.__doc__ = """A **WidgetState** that allows for rotation, translation, and scalling.

Use this **WidgetState** when you want to be able to use clicks and drags to
control and adjust the size, rotation, or postion of its children.

Example
-------

::

    from smile.common import *

    exp = Experiment()

    with ScatterLayout(size=exp.screen.size,scale=5) as sc:
        Rectangle()
    with Meanwhile():
        MouseCursor()
    with Meanwhile():
        with Loop() as l:
            sc.update(rotation=l.i)
            Wait(.2)
    exp.run()

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.
bbox : list (Property)
    Bounding box of the widget in parent space: ((x, y), (w, h))
do_rotation : boolean (Parameter, optional, default=True)
    Allow roation.
do_scale : boolean (Parameter, optional, default=True)
    Allow scaling.
do_translation_x : boolean (Parameter, optional, default=True)
    Allow translation on the X axis.
do_translation_y : boolean (Parameter, optional, default=True)
    Allow translation on the Y axis.
rotation : float (Parameter, optional, default=0.0)
    Current rotation of the layout.
scale : float (Parameter, optional, default=1.0)
    Current scale of the layout.
scale_max : float (Parameter, optional, default=1x10^20)
    Maximum scaling factor allowed.
scale_min : float (Parameter, optional, default=0.01)
    Minimum scaling factor allowed.
transform : matrix (Parameter, optional, default=The identity matrix)
    Transformation matrix.
transform_inv : matrix (Parameter, optional, default=The identity matrix)
    Inverse of the transformation matrix.
translation_touches : integer (Parameter, optional, default=1)
    Determine whether translation was triggered by a single or multiple touches.
    This only has effect when do_translation = True.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.ScatterLayout. <https://kivy.org/docs/api-kivy.uix.scatterlayout.html>'_

"""
StackLayout.__doc__ = """A **WidgetState** that arranges its children to make them fit.

Use this layout to stack child states vertically or horizontally to the best of
the ability of the layout give its size. The invididual children do not have to
be the same size in this layout.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.
minimum_height : integer (Parameter, optional, default=0)
    Minimum height needed to contain all children. It is automatically set by
    the layout.
minimum_width : integer (Parameter, optional, default=0)
    Minimum width needed to contain all children. It is automatically set by the
    layout.
minimum_size : list (Parameter, optional, default=[0, 0])
    Minimum size needed to contain all children. It is automatically set by the
    layout.
orientation : string (Parameter, optional, default="lr-tb")
    Orientation of the layout. Valid orientations are "lr-tb", "tb-lr",
    "rl-tb", "tb-rl", "lr-bt", "bt-lr", "rl-bt" and "bt-rl".
padding : list (Parameter, optional, default=[0, 0, 0, 0])
    Padding between the widget box and its children, in pixels: [padding_left,
    padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].
spacing : integer (Parameter, optional, default=0)
    Spacing between children, in pixels.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.StackLayout. <https://kivy.org/docs/api-kivy.uix.stacklayout.html>'_

"""
ScrollView.__doc__ = """A **WidgetState** for scrollable/pannable viewing.

Use this layout if you would like to scroll through an area that is bigger than
the experiment window. You can set the ability to scroll horizontally and
vertically, and change some of the properties of the bar that dictates the
scroll position.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.
do_scroll_x : boolean (Parameter, optional, default=True)
    Allow scroll on X axis.
do_scroll_y : boolean (Parameter, optional, default=True)
    Allow scroll on X axis.
bar_color : list (Parameter, optional, default=[0.7, 0.7, 0.7, 0.9])
    Color of horizontal / vertical scroll bar, in RGBA format.
bar_inactive_color : list (Parameter, optional, default=[0.7, 0.7, 0.7, 0.2])
    Color of horizontal / vertical scroll bar (in RGBA format), when no scroll
    is happening.
bar_margin : integer (Parameter, optional, default=0)
    Margin between the bottom / right side of the scrollview when drawing the
    horizontal / vertical scroll bar.
bar_pos : list (Parameter, optional, default=["bottom", "right"])
    Which side of the scroll view to place each of the bars on.
    (bar_pos_x, bar_pos_y)
bar_pos_x : string (Parameter, optional, default="bottom")
    Which side of the ScrollView the horizontal scroll bar should go on.
    Possible values are "top" and "bottom".
bar_box_y : string (Parameter, optional, default="right")
    Which side of the ScrollView the vertical scroll bar should go on. Possible
    values are "left" and "right".
bar_width : integer (Parameter, optional, default=2)
    Width of the horizontal / vertical scroll bar. The width is interpreted as a
    height for the horizontal bar.
hbar : list (Property)
    Return a tuple of (position, size) of the horizontal scrolling bar.

    The position and size are normalized between 0-1, and represent a percentage
    of the current scrollview height. This property is used internally for
    drawing the little horizontal bar when you're scrolling.
scroll_distance : integer (Parameter, optional, default=20)
    Distance to move before scrolling the ScrollView, in pixels. As soon as the
    distance has been traveled, the ScrollView will start to scroll, and no
    touch event will go to children. It is advisable that you base this value on
    the dpi of your target device's screen.
scroll_timeout : integer (Parameter, optional, default=55)
    Timeout allowed to trigger the scroll_distance, in milliseconds. If the user
    has not moved scroll_distance within the timeout, the scrolling will be
    disabled, and the touch event will go to the children.
scroll_type : list (Parameter, optional, default=["content"])
    Sets the type of scrolling to use for the content of the scrollview.
    Available options are: ["content"], ["bars"], ["bars", "content"].
scroll_wheel_distance : integer (Parameter, optional, default=20)
    Distance to move when scrolling with a mouse wheel in pixels. It is
    advisable that you base this value on the dpi of your target device's
    screen.
scroll_x : float (Property)
    X scrolling value, between 0 and 1. If 0, the content's left side will touch
    the left side of the ScrollView. If 1, the content's right side will touch
    the right side.
scroll_y : float (Property)
    Y scrolling value, between 0 and 1. If 0, the content's bottom side will
    touch the bottom side of the ScrollView. If 1, the content's top side will
    touch the top side.
vbar : list (Property)
    Return a tuple of (position, size) of the vertical scrolling bar.

    The position and size are normalized between 0-1, and represent a percentage
    of the current scrollview height. This property is used internally for
    drawing the little vertical bar when you're scrolling.
viewport_size : integer (Property)
    (internal) Size of the internal viewport. This is the size of your only
    child in the scrollview.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.ScrollLayout. <https://kivy.org/docs/api-kivy.uix.Scrolllayout.html>'_


"""

for widget in widgets:
    exec("%s.__doc__ = %s.__doc__ + WSP_doc_addition" %
         (widget, widget))



import kivy.uix.rst
RstDocument = WidgetState.wrap(kivy.uix.rst.RstDocument)

RstDocument.__doc__="""A **WidgetState** for displaying RST documents.

This **WidgetState** allows you to control the colors, fonts, and functions as
a **ScrollView**. See **ScrollView** for other parameters you can use in this
**WidgetState**.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.
text : string (Parameter, optional, default=None)
    RST markup text of the document.
title : string (Property)
    Title of the current document. Read-only
source : string (Parameter, optional, default="")
    Filename of the RST document.
background_color : string (Parameter, optional, default="e5e6e9ff")
    Specifies the background_color to be used for the RstDocument.
base_font_size : integer (Parameter, optional, default=31)
        Font size for the biggest title. All other font sizes are
        derived from this.
colors : dictionary (Parameter, optional, default listed below)
    Dictionary of all the colors used in the RST rendering.

    Defaults

       - "paragraph" : "202020ff"
       - "link" : "ce5c00ff
       - "bullet" : "000000ff"
       - "background" : "e5e6e9ff"
       - "title" : "204a87ff"
document_root : string (Parameter, optional, default=None)
    Root path where :doc: will search for rst documents. If no path is given, it
    will use the directory of the first loaded source file.
show_errors : boolean (Parameter, optional, default=False)
    Indicate whether RST parsers errors should be shown on the screen or not.
source_encoding : string (Parameter, optional, default="utf-8")
    Encoding to be used for the source file.
source_error : string (Parameter, optional, default="strict"
    Error handling to be used while encoding the source file. Can be one of
    "strict", "ignore", "replace", "xmlcharrefreplace" or "backslashreplac".
title : string (Property)
    Title of the current document. Read-only.
toctrees : dictionary (Property)
    Toctree of all loaded or preloaded documents. This dictionary is filled when
    a rst document is explicitly loaded or where preload() has been called.

    If the document has no filename, e.g. when the document is loaded from a
    text file, the key will be "".
underline_color : string (Parameter, optional, default="204a9699")
    Underline color of the titles, expressed in html color notation.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.rst. <https://kivy.org/docs/api-kivy.uix.rst.html>'_



"""

import kivy.uix.filechooser
FileChooserListView = WidgetState.wrap(kivy.uix.filechooser.FileChooserListView)

FileChooserListView.__doc__="""A **WidgetState** that displays and selects files and directories.

Only used in the spash screen of SMILE, this state is useful if you are trying
to design your own splash screen.

Parameters
----------
duration : float (optional, default = None)
    The duration of this state. Can be None. Will continue running until
    canceled, or until the duration is over.
parent : ParentState (optional)
    The parent of this state, if None, it will be set automatically
save_log : boolean (optinal, default = True)
    If True, this state will save out all of the Logged Attributes.
name : string (optinal)
    The unique name to this state.
blocking : boolean (optional, default = True)
    If True, this state will prevent a *Parallel* state from ending. If
    False, this state will be canceled if its *ParallelParent* finishes
    running. Only relevent if within a *ParallelParent*.

Positional Parameters
---------------------
All **WidgetState** States have the ability to set the positional variables
as parameters when building the states. Please see **WidgetState** for the
positional paramters you can set.

Kivy Parameters and Properties
------------------------------
Below is the docstring attached to the Kivy widget that this WidgetState is
based on. Any of the parameters listed below are able to be used by this
WidgetState and can be passed into it the same way any other parameter can.
Any of the internal properties that are readable by this Kivy Widget are
readable during Experimental Run Time.

pos : list (Parameter, optional, default=[screen.width/2, screen.height/2])
    Position of the layout in format (x,y). If you pass in any of the
    positional parameters of a WidgetState, like center_x or center_y, this
    widget will fill in pos automatically.
size : list (Parameter, optional, default=[50, 50])
    Size of the layout in format (width, height). If you pass in any of the
    positional parameters of a WidgetState, like width or height, this
    widget will fill in size automatically.
dirselect : boolean (Parameter, optional, default=False)
    Determines whether directories are valid selections or not.
file_econdings : list (Parameter, optional, default=["utf-8", "latin1", "cp1252"])
    Possible encodings for decoding a filename to unicode. In the case that the
    user has a non-ascii filename, undecodable without knowing it's initial
    encoding, we have no other choice than to guess it.

    Please note that if you encounter an issue because of a missing encoding
    here, we'll be glad to add it to this list.
file_system : object (Parameter, optional, default=FileSystemLocal())
    The file system object used to access the file system. This should be a
    subclass of FileSystemAbstract.
files : list (Property)
    The list of files in the directory specified by path after applying the
    filters. Read-only.
filter_dirs : boolean (Parameter, optional, default=False)
    Indicates whether filters should also apply to directories.
filters : list (Parameter, optional, default=[])
    filters specifies the filters to be applied to the files in the directory.
    filters is a ListProperty and defaults to []. This is equivalent to "*" i.e.
    nothing is filtered.

    The filters are not reset when the path changes. You need to do that
    yourself if desired.

    There are two kinds of filters: patterns and callbacks. Patterns are strings
    that match the file name patteres. Use "*" to match all files, or "*.png" to
    only match png files. You can also use a sequence of characters to match any
    files with that sequence in it.

    callbacks are just a function that takes the folder and the file as the
    parameters, in that order. If you write a callback function, it must take
    2 parameters and return True to indicate a match, and False to indicate
    otherwise.
layout : object (Property)
    Reference to the layout widget instance.
multiselect : boolean (Parameter, optional, default=False)
    Determines whether the user is able to select multiple files or not.
path : string (Parameter, optional, defaults to current working directory)
    It specifies the path on the filesystem that this controller should refer
    to.
rootpath : string (Parameter, optional, default=None)
    Root path to use instead of the system root path. If set, it will not show a
    ".." directory to go up to the root path. For example, if you set rootpath
    to /users/foo, the user will be unable to go to /users or to any other
    directory not starting with /users/foo.
selection : list (Property)
    Contains the list of files that are currently selected.
show_hidden : boolean (Parameter, optional, default=False)
    Determines whether hidden files and folders should be shown.
sort_func : object (Parameter, optional, defaults to a function returning alphanumerically named folders first.)
    Provides a function to be called with a list of filenames as the first
    argument and the filesystem implementation as the second argument. It
    returns a list of filenames sorted for display in the view.

For other parameters or properties that this Widget might have, refer to the
Kivy documentation for 'kivy.uix.filechooser. <https://kivy.org/docs/api-kivy.uix.filechooser.html>'_


"""

# set the sp function back
kivy.metrics.sp = _sp_save


import kivy.uix.video
class Video(WidgetState.wrap(kivy.uix.video.Video)):
    """A **WidgetState** that plays a video.

    Use this smile state to play a video file. Depending on what package is
    driving your video core, you maybe able to play different types of
    video files. If you are on windows, your video provider is gtstreamer,
    which means you can use AVi, ASF, mpeg, OGG, dv. If you are using Linux
    or OSX, find out what your video provider is in python, and go to their
    website to check the available file types. This state ends when the
    video is over.

    Paramters
    ---------
    duration : float (optional, default = None)
        The duration of this state, or how long you want the video to play. If
        the *duration* is less than the duration of the file, than the video
        will stop playing before done. If the *duration* is more than the file's
        duration, than the video will stop on the last frame and will display
        that frame until the *duration* is over.
    parent : ParentState (optional)
        The parent of this state, if None, it will be set automatically
    save_log : boolean (optinal, default = True)
        If True, this state will save out all of the Logged Attributes.
    name : string (optinal)
        The unique name to this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevent if within a *ParallelParent*.

    Positional Parameters
    ---------------------
    All **WidgetState** States have the ability to set the positional variables
    as parameters when building the states. Please see **WidgetState** for the
    positional paramters you can set.


    Kivy Parameters and Properties
    ------------------------------
    Below is the docstring attached to the Kivy widget that this WidgetState is
    based on. Any of the parameters listed below are able to be used by this
    WidgetState and can be passed into it the same way any other parameter can.
    Any of the internal properties that are readable by this Kivy Widget are
    readable during Experimental Run Time.

    source : string (Parameter)
        Filename or source of your video file.
    allow_strech : boolean (Parameter, optional, default = False)
        If True, the normalized image size will be maximized to fit in the image
        box. Otherwise, if the box is too tall, the image will not be stretched
        more than 1:1 pixels.
    keep_ratio : boolean (Parameter, optional, default = True)
        If False along with allow_stretch being True, the normalized image size
        will be maximized to fit in the image box and ignores the aspect ratio
        of the image. Otherwise, if the box is too tall, the image will not be
        stretched more than 1:1 pixels.
    volume : float (Parameter, optional, default = 1.0)
        Volume of the video, in the range 0-1. 1 means full volume, 0 means
        mute.
    position : float (Property)
        Position of the video between 0 and duration. The position defaults to
        -1 and is set to a real position when the video is loaded.

    For other parameters or properties that this Widget might have, refer to the
    Kivy documentation for 'kivy.uix.video. <https://kivy.org/docs/api-kivy.uix.Video.html>'_

    """
    def _set_widget_defaults(self):
        # force video to load immediately so that duration is available...
        _kivy_clock.unschedule(self._widget._do_video_load)
        self._widget._do_video_load()
        self._widget._video.pause()
        if self._end_time is None:
            # we need the duration to set the end time
            if self._widget._video.duration == -1:
                # try for up to 1 ms
                for i in range(10):
                    if self._widget._video.duration == -1:
                        break
                    print 'd',
                    clock.usleep(100)

            self._end_time = self._start_time + self._widget._video.duration

        # override the update interval (eventually make this a setting)
        _kivy_clock.unschedule(self._widget._video._update)
        _kivy_clock.schedule_interval(self._widget._video._update, 1/60.)

        # set the size to (0, 0) so we know if it has been changed later
        self._widget.size = (0, 0)

    def show(self):
        if "state" not in self._constructor_param_names:
            self._widget.state = "play"
        self._widget._video._update(0)  # prevent white flash at start
        if self._widget.width == 0 and self._widget.height == 0:
            if not self._widget._video.texture:
                # gotta wait for the texture to load (up to 1ms)
                for i in range(10):
                    if self._widget._video.texture:
                        break
                    print 't',
                    clock.usleep(100)
                    self._widget._video._update(0)
            self.live_change(size=self._widget._video.texture.size)
        super(Video, self).show()

    def unshow(self):
        super(Video, self).unshow()
        self._widget.state = "stop"


import kivy.uix.image
class Image(WidgetState.wrap(kivy.uix.image.Image)):
    """A WidgetState subclass to present and image on the screen.

    This state will present an image from a file onto the experiment window. By
    default, the size of the widget will be the size of the image, but you are
    able to set the height and width independently, as well as if you would
    like the image to stretch into the new size of the widget.

    Parameters
    ----------
    duration : float
        A float value in seconds that this image lasts for.
    parent : ParentState
        The parent of this state, if None, it will be set automatically
    save_log : boolean
        If True, this state will save out all of the Logged Attributes.
    name : string
        The unique name to this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevent if within a *ParallelParent*.

    Kivy Parameters and Properties
    ------------------------------
    Below is the docstring attached to the Kivy widget that this WidgetState is
    based on. Any of the parameters listed below are able to be used by this
    WidgetState and can be passed into it the same way any other parameter can.
    Any of the internal properties that are readable by this Kivy Widget are
    readable during Experimental Run Time.

    source : string (Parameter)
        Filename or source of your video file.
    allow_strech : boolean (Parameter, optional, default = False)
        If True, the normalized image size will be maximized to fit in the image
        box. Otherwise, if the box is too tall, the image will not be stretched
        more than 1:1 pixels.
    keep_ratio : boolean (Parameter, optional, default = True)
        If False along with allow_stretch being True, the normalized image size
        will be maximized to fit in the image box and ignores the aspect ratio
        of the image. Otherwise, if the box is too tall, the image will not be
        stretched more than 1:1 pixels.
    anim_loop : integer (Parameter, optional, default = 0)
        Number of loops to play then stop animating a nonstatic image like a
        gif. 0 means keep animating.
    anim_delay : float (Parameter, optional, default = .25 (meaning 4 FPS))
        Delay the animation if the image is sequenced (like an animated gif). If
        anim_delay is set to -1, the animation will be stopped.
    color : list (Parameter, optional, default = [1.0, 1.0, 1.0, 1.0])
        Image color, in the format (r, g, b, a). This attribute can be used to
        "tint" an image. Be careful: if the source image is not gray/white, the
        color will not really work as expected.
    image_ratio : list (Property)
        Ratio of the image (width / float(height).

    For other parameters or properties that this Widget might have, refer to the
    Kivy documentation for 'kivy.uix.image. <https://kivy.org/docs/api-kivy.uix.image.html>'_

    """
    def _set_widget_defaults(self):
        self._widget.size = self._widget.texture_size

import kivy.uix.label
class Label(WidgetState.wrap(kivy.uix.label.Label)):
    """State for presenting any kind of text stimulus onto the screen.

    This state presents a text stimulus for a duration. Using widget
    parameters, you are able to set any of the properties that a Kivy Label
    would need set.  This includes anything from emboldening your text to
    changing the font of you text. Because this is a Kivy widget you are able
    to set any of the size and shape properties as parameters when setting up
    this state.

    Parameters
    ----------
    duration : float
        A float value in seconds that this image lasts for.
    parent : ParentState
        The parent of this state, if None, it will be set automatically
    save_log : boolean
        If True, this state will save out all of the Logged Attributes.
    name : string
        The unique name to this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevent if within a *ParallelParent*.

    Positional Parameters
    ---------------------
    All **WidgetState** States have the ability to set the positional variables
    as parameters when building the states. Please see **WidgetState** for the
    positional paramters you can set.

    Kivy Parameters and Properties
    ------------------------------
    Below is the docstring attached to the Kivy widget that this WidgetState is
    based on. Any of the parameters listed below are able to be used by this
    WidgetState and can be passed into it the same way any other parameter can.
    Any of the internal properties that are readable by this Kivy Widget are
    readable during Experimental Run Time.

    text : string (Parameter)
        The string of text that you would like to present
    bold : boolean (Parameter, optional, default = False)
        Indicates use of the bold version of your font.
    italic : boolean (Parameter, optional, default = False)
        Indicates use of the italic version of your font.
    color : boolean (Parameter, optional, default = [1.0, 1.0, 1.0, 1.0])
        Text color, in the format (r, g, b, a).
    font_name : string (Parameter, optional, default = "Roboto")
        Filename of the font to use. The path can be absolute or relative.
        Relative paths are resolved by the resource_find() function.
    font_size : integer (Parameter, optional, default = 15)
        Font size of the text, in pixels.
    max_lines : integer (Parameter, optional, default = 0)
        Maximum number of lines to use, defaults to 0, which means unlimited.
        Please note that shorten take over this property. (with shorten, the
        text is always one line.)
    padding : list (Parameter, optional, default=[0,0])
        Padding of the text in the format (padding_x, padding_y)
    padding_x : integer (Parameter, optional, default=0)
        Horizontal padding of the text inside the widget box.
    padding_y : integer (Parameter, optional, default=0)
        Vertical padding of the text inside the widget box.
    shorten : boolean (Paremter, optional, default=False)
        Indicates whether the label should attempt to shorten its textual
        contents as much as possible if a text_size is given. Setting this to
        True without an appropriately set text_size will lead to unexpected
        results.

        shorten_from and split_str control the direction from which the text is
        split, as well as where in the text we are allowed to split.
    shorten_from : string (Parameter, optional, default="center")
        The side from which we should shorten the text from, can be "left", "
        right", or "center".

        For example, if left, the ellipsis will appear towards the left side and
        we will display as much text starting from the right as possible.
        Similar to shorten, this option only applies when text_size [0] is not
        None, In this case, the string is shortened to fit within the specified
        width.
    split_str : string (Parameter, optional, default="")
        The string used to split the text while shortening the string when
        shorten is True.

        For example, if it's a space, the string will be broken into words and
        as many whole words that can fit into a single line will be displayed.
        If shorten_from is the empty string, "", we split on every character
        fitting as much text as possible into the line.
    strip : boolean (Parameter, optional, default=False)
        Whether leading and trailing spaces and newlines should be stripped from
        each displayed line. If True, every line will start at the right or left
        edge, depending on halign. If halign is justify it is implicitly True.
    text_size : list (Parameter, optional, default=[Nonce, None])
        By default, the label is not constrained to any bounding box. You can
        set the size constraint of the label with this property. The text will
        autoflow into the constrains. So although the font size will not be
        reduced, the text will be arranged to fit into the box as best as
        possible, with any text still outside the box clipped.

        This sets and clips texture_size to text_size if not None.

        For example, whatever your current widget size is, if you want the label
        to be created in a box with width=200 and unlimited height:

            Label(text="Very big big line", text_size=(200, None))

    texture : object (Property)
        Texture object of the text. The text is rendered automatically when a
        property changes. The OpenGL texture created in this operation is stored
        in this property. You can use this texture for any graphics elements.

        Depending on the texture creation, the value will be a Texture or
        TextureRegion object.
    texture_size : list (Property)
        Texture size of the text. The size is determined by the font size and
        text. If text_size is [None, None], the texture will be the size
        required to fit the text, otherwise it's clipped to fit text_size.

        When text_size is [None, None], one can bind to texture_size and rescale
        it proportionally to fit the size of the label in order to make the text
        fit maximally in the label.
    unicode_errors : string (Parameter, optional, default="replace")
        How to handle unicode decode errors. Can be "strict", "replace" or
        "ignore".
    valign : string (Parameter, optional, default="bottom")
        Vertical alignment of the text. Can be "bottom", "middle", or "top"

    For other parameters or properties that this Widget might have, refer to the
    Kivy documentation for 'kivy.uix.label. <https://kivy.org/docs/api-kivy.uix.label.html>'_

    """
    def _set_widget_defaults(self):
        # we need to update the texture now
        _kivy_clock.unschedule(self._widget.texture_update)
        self._widget.texture_update()
        self._widget.size = self._widget.texture_size

def iter_nested_buttons(state):
    if isinstance(state, Button):
        yield state
    if isinstance(state, ParentState):
        for child in state._children:
            for button in iter_nested_buttons(child):
                yield button

class ButtonPress(CallbackState):
    """Like a KeyPress state, but listens for any buttons to be clicked.

    This is a ParentState, so you must use it like you would a Parallel
    state or a Serial state.  Below there is an example.  You can have the
    ButtonPress state last for a duration, give it a correct_resp string
    name, and even set the base time of the timing, just like any other
    state. Remember to use a MouseCursor state to allow for the mouse to be
    visible during the ButtonPress state.

    Parameters
    ----------
    buttons : list of Button states, optional
        A list of all of the buttons contained in this state. If left as
        None, and the ButtonPress state is used as a context state, then
        the Buttons will be added automatically.
    correct_resp : string or list of strings
        Put in the string value that you put in the *name* parameter of
        the button you would like to be the correct response to this button
        press.
    base_time : float
        The time at which you would like to base the timing of this state
        off of. Defaults to self.appear_time["time"].
    duration : float (optional)
        The duration of the state in seconds, if no duration is set, it
        will last forever.
    parent : ParentState (optional)
        The state you would like this state to be a child of. If not set,
        the *Experiment* will make it a child of a ParentState or the
        Experiment automatically.
    name : string (optional)
        The unique name of this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its Parallel Parent finishes
        running. Only relevent if within a *Parallel* Parent.
    save_log : boolean (optional, defaults = True)
        If True, this state will save all of its information into a
        .slog file.

    Logged Attributes
    -----------------
    button_names : list of strings
        This field contains all of the buttons that this state is listening
        to for a button press.
    pressed : string
        The button that was pressed.
    press_time : float
        The time at which a button was pressed.
    correct : boolean
        Will be True if the button pressed was in the correct_resp list at
        initialization.
    rt : float
        This contains the float value of the difference between the
        press_time and the base_time.

    Example
    -------

    The following example shows a 3 button choice, where Choice A is the
    correct answer.  They have 4 seconds to click one of the three buttons,
    otherwise the Experiment will continue to the next state.

    ::

        with ButtonPress(correct_resp="chA", duration=4) as bp:
            MouseCursor()
            a = Button(name="chA", text="Choice A",
                       center_x=exp.screen.center_x/3)

            b = Button(name="chB", text="Choice B")

            c = Button(name="chC", text="Choice C",
                       center_x=exp.screen.center_x*3/2)

    """
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
        elif type(self._correct_resp) not in (list, tuple):
            self._correct_resp = [self._correct_resp]
        from mouse import MouseButton
        self.__pressed_ref = Ref(
            lambda lst: [name for name, mouse_button in lst if
                         mouse_button is not None],
            [(button._name, MouseButton(button)) for button in
             self.__buttons])
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

    Video(source="test_video.mp4", duration=4.0)

    pb = ProgressBar(max=100)
    with UntilDone():
        pb.slide(value=100, duration=2.0)

    Image(source="face-smile.png", duration=5.0)

    text = """
.. _top:

Hello world
===========

This is an **emphasized text**, some ``interpreted text``.
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
        #rect.center = exp.screen.left_bottom
        rect.update(center=exp.screen.left_bottom, color="yellow")
        Wait(1.0)
        #rect.center = exp.screen.center
        rect.update(center=exp.screen.center, color="purple")
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
                  duration=1.0)#, interval=0.5)
        #Screenshot("my_screenshot.png")
        vid.animate(center_x=(lambda t, initial: exp.screen.center_x +
                              cos(t / 3.0) * exp.screen.width * 0.25),
                    center_y=(lambda t, initial: exp.screen.center_y +
                              sin(t / 3.0) * exp.screen.width * 0.25),
                    height=(lambda t, initial: initial + sin(t / 2.0) *
                            initial * 0.5))#, interval=0.5)
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
