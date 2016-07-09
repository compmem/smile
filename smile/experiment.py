# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# import main modules
import sys
import os
import weakref
import time
import threading

# kivy imports
import kivy_overrides
import kivy
import kivy.base
from kivy.config import Config
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.base import EventLoop  # this is actually our event loop
from kivy.core.window import Window
from kivy.graphics.opengl import (
    glVertexAttribPointer,
    glVertexAttrib4f,
    glDrawArrays,
    glFinish,
    GL_INT,
    GL_FALSE,
    GL_POINTS)
from kivy.utils import platform
import kivy.clock
_kivy_clock = kivy.clock.Clock

# local imports
from state import Serial, AutoFinalizeState
from ref import val, Ref
from clock import clock
from log import LogWriter, log2csv
from video import normalize_color_spec

FLIP_TIME_MARGIN = 0.002     # increase this if we're missing flips
IDLE_USLEEP = 250            # USLEEP During idle


def event_time(time, time_error=0.0):  # TODO: make this a class!
    return {'time': time, 'error': time_error}


class _VideoChange(object):
    """Container for a change to the graphics tree."""

    def __init__(self, update_cb, flip_time, flip_time_cb):
        self.update_cb = update_cb
        self.flip_time = flip_time
        self.flip_time_cb = flip_time_cb
        self.drawn = False
        self.flipped = False


class Screen(object):
    """Provides references to screen/app properties.
    Properties
    ----------
    last_flip : event_time
        Time of last flip updating the screen
    mouse_pos : tuple
        Location of the mouse on the screen
    mouse_button : string
        What mouse button is pressed
    width : integer
    height : integer
    size : tuple
        (self.width, self.height)
    left : integer
        The left most horizontal value. self.left = 0
    right : integer
        self.right = width
    top : integer
        self.top = height
    bottom : integer
        The bottom most vertical point on the screen. self.bottom = 0
    x : integer
        self.left
    y : integer
        self.bottom
    pos : tuple
        self.pos = (x, y)
    center_x : integer
        self.center_x = width//2
    center_y : integer
        self.center_y = height//2
    center : tuple
        self.center = (self.center_x, self.center_y)
    right_center : tuple
        self.right_center = (self.right, self.center_y)
    right_top : tuple
        self.right_top = (self.right, self.top)
    right_bottom : tuple
        self.right_bottom = (self.right, self.bottom)
    left_center : tuple
        self.left_center = (self.left, self.center_y)
    left_top : tuple
        self.left_top = (self.left, self.top)
    left_bottom : tuple
        self.left_bottom = (self.left, self.bottom)
    """

    def __init__(self):
        # set up the values of interest and their refs
        self._width = 0.0
        self._width_ref = Ref.getattr(self, "_width")
        self._height = 0.0
        self._height_ref = Ref.getattr(self, "_height")
        self._last_flip = event_time(0.0, 0.0)
        self._last_flip_ref = Ref.getattr(self, "_last_flip")
        self._mouse_pos = (0, 0)
        self._mouse_pos_ref = Ref.getattr(self, "_mouse_pos")
        self._mouse_button = None
        self._mouse_button_ref = Ref.getattr(self, "_mouse_button")
        self._keys_down = set()
        self._issued_key_refs = weakref.WeakValueDictionary()

    @property
    def last_flip(self):
        return self._last_flip_ref

    def _set_last_flip(self, etime):
        self._last_flip = etime
        self._last_flip_ref.dep_changed()

    @property
    def mouse_pos(self):
        return self._mouse_pos_ref

    def _set_mouse_pos(self, mouse_pos):
        self._mouse_pos = mouse_pos
        self._mouse_pos_ref.dep_changed()

    @property
    def mouse_button(self):
        return self._mouse_button_ref

    def _set_mouse_button(self, mouse_button):
        self._mouse_button = mouse_button
        self._mouse_button_ref.dep_changed()

    def _is_key_down(self, name):
        return name.upper() in self._keys_down

    def _get_key_ref(self, name):
        try:
            return self._issued_key_refs[name]
        except KeyError:
            ref = Ref(self._is_key_down, name)
            self._issued_key_refs[name] = ref
            return ref

    @property
    def width(self):
        return self._width_ref

    def _set_width(self, width):
        self._width = width
        self._width_ref.dep_changed()

    @property
    def height(self):
        return self._height_ref

    def _set_height(self, height):
        self._height = height
        self._height_ref.dep_changed()

    @property
    def size(self):
        return (self.width, self.height)

    @property
    def left(self):
        return 0

    @property
    def bottom(self):
        return 0

    @property
    def right(self):
        return self.width - 1

    @property
    def top(self):
        return self.height - 1

    x = left
    y = bottom

    @property
    def pos(self):
        return (self.x, self.y)

    @property
    def center_x(self):
        return self.width // 2

    @property
    def center_y(self):
        return self.height // 2

    @property
    def left_bottom(self):
        return (self.left, self.bottom)

    @property
    def left_center(self):
        return (self.left, self.center_y)

    @property
    def left_top(self):
        return (self.left, self.top)

    @property
    def center_bottom(self):
        return (self.center_x, self.bottom)

    @property
    def center(self):
        return (self.center_x, self.center_y)

    @property
    def center_top(self):
        return (self.center_x, self.top)

    @property
    def right_bottom(self):
        return (self.right, self.bottom)

    @property
    def right_center(self):
        return (self.right, self.center_y)

    @property
    def right_top(self):
        return (self.right, self.top)


class ExpApp(App):
    """Kivy app associated with the experiment.
    Not instantiated by the end user."""

    def __init__(self, exp):
        super(ExpApp, self).__init__()
        self.exp = exp
        self.callbacks = {}
        self.pending_flip_time = None
        self.video_queue = []
        self.force_blocking_flip = False
        self.force_nonblocking_flip = False
        self.flip_interval = 1 / 60.  # default to 60 Hz

    def add_callback(self, event_name, func):
        self.callbacks.setdefault(event_name, []).append(func)

    def remove_callback(self, event_name, event_func):
        try:
            callbacks = self.callbacks[event_name]
        except KeyError:
            return
        self.callbacks[event_name] = [func for func in
                                      self.callbacks[event_name] if
                                      func != event_func]

    def _trigger_callback(self, event_name, *pargs, **kwargs):
        # call the callbacks associated with an event name
        try:
            callbacks = self.callbacks[event_name]
        except KeyError:
            return
        for func in callbacks:
            func(*pargs, **kwargs)

    def build(self):
        # base layout uses positional placement
        self.wid = FloatLayout()
        Window._system_keyboard.bind(on_key_down=self._on_key_down,
                                     on_key_up=self._on_key_up)
        Window.bind(on_motion=self._on_motion,
                    mouse_pos=self._on_mouse_pos,
                    on_resize=self._on_resize)
        self.current_touch = None

        # set starting times
        self._last_time = clock.now()
        self._last_kivy_tick = clock.now()

        # use our idle callback (defined below)
        kivy.base.EventLoop.set_idle_callback(self._idle_callback)

        # get start of event loop
        EventLoop.bind(on_start=self._on_start)

        # set width and height
        self.exp._screen._set_width(Window.width)
        self.exp._screen._set_height(Window.height)

        return self.wid

    def _on_start(self, *pargs):
        # print "on_start"
        # self.exp._root_state.enter(clock.now() + 1.0)
        self.blocking_flip()
        # hack to wait until fullscreen on OSX
        if True:  # not (platform in ('macosx',) and Window.fullscreen):
            print "Estimated Refresh Rate:", 1.0 / self.calc_flip_interval()
            self.exp._root_executor.enter(clock.now() + 0.25)

    def _on_resize(self, *pargs):
        # handle the resize
        self.exp._screen._set_width(Window.width)
        self.exp._screen._set_height(Window.height)

        # second half of OSX fullscreen hack that may no longer be needed
        if platform in ('macosx',) and Window.fullscreen and \
           not self.exp._root_executor._enter_time and \
           not self.exp._root_executor._active:
            print "Estimated Refresh Rate:", 1.0 / self.calc_flip_interval()
            self.exp._root_executor.enter(clock.now() + 0.25)

        # we need a redraw here
        EventLoop.window.dispatch('on_flip')

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[0] == 27 and "shift" in modifiers:
            self.stop()
            return
        name = keycode[1].upper()
        self.exp.screen._keys_down.add(name)
        try:
            self.exp.screen._issued_key_refs[name].dep_changed()
        except KeyError:
            pass
        self._trigger_callback("KEY_DOWN", keycode, text, modifiers,
                               self.event_time)

    def _on_key_up(self, keyboard, keycode):
        name = keycode[1].upper()
        self.exp.screen._keys_down.discard(name)
        try:
            self.exp.screen._issued_key_refs[name].dep_changed()
        except KeyError:
            pass
        self._trigger_callback("KEY_UP", keycode, self.event_time)

    def _on_mouse_pos(self, window, pos):
        if self.current_touch is None:
            self.exp._screen._set_mouse_pos(tuple(pos))
            self._trigger_callback("MOTION", pos=pos, button=None,
                                   newly_pressed=False,
                                   double=False, triple=False,
                                   event_time=self.event_time)

    def _on_motion(self, window, etype, me):
        if etype == "begin":
            try:
                button = me.button
                self.exp._screen._set_mouse_button(button)
            except AttributeError:
                self.exp._screen._set_mouse_button(None)
            self.current_touch = me
            self._trigger_callback("MOTION", pos=me.pos,
                                   button=self.exp._screen._mouse_button,
                                   newly_pressed=True,
                                   double=me.is_double_tap,
                                   triple=me.is_triple_tap,
                                   event_time=self.event_time)
        elif etype == "update":
            self.exp._screen._set_mouse_pos(tuple(int(round(x))
                                                  for x in me.pos))
            self.current_touch = me
            self._trigger_callback("MOTION", pos=me.pos,
                                   button=self.exp._screen._mouse_button,
                                   newly_pressed=False,
                                   double=me.is_double_tap,
                                   triple=me.is_triple_tap,
                                   event_time=self.event_time)
        else:
            self.exp._screen._set_mouse_button(None)
            self.current_touch = None
            self._trigger_callback("MOTION", pos=me.pos, button=None,
                                   newly_pressed=False,
                                   double=False, triple=False,
                                   event_time=self.event_time)

    def _idle_callback(self, event_loop):
        # record the time range
        self._new_time = clock.now()
        time_err = (self._new_time - self._last_time) / 2.0
        self.event_time = event_time(self._last_time + time_err, time_err)

        # call any of our scheduled events that are ready
        clock.tick()

        # see if we're ready for video
        ready_for_video = ((self._new_time - self.last_flip["time"]) >=
                           (self.flip_interval - FLIP_TIME_MARGIN))

        # see if the kivy clock needs a tick
        # throttled by flip interval
        ready_for_kivy_tick = ready_for_video and (self._new_time -
                                                   self._last_kivy_tick >=
                                                   self.flip_interval)

        # prepare for every video to be drawn on the next flip
        need_draw = False
        for video in self.video_queue:
            if (not video.drawn and
                ((self.pending_flip_time is None and
                  self._new_time >= (video.flip_time -
                                     (self.flip_interval / 2.0))) or
                 video.flip_time == self.pending_flip_time)):
                # prepare that video change
                video.update_cb()
                need_draw = True
                video.drawn = True

                # save the pending time so all other changes
                # for that time will also run
                self.pending_flip_time = video.flip_time
            else:
                # either none are ready or the remaining are
                # for a subsequent flip
                break

        # do a kivy tick if we're going to be drawing or enough time
        # has passed (see above)
        # but only tick and draw once before a flip
        do_kivy_tick = ready_for_kivy_tick or need_draw
        if do_kivy_tick:
            # tick the kivy clock
            _kivy_clock.tick()
            self._last_kivy_tick = self._new_time

        # dispatch input events
        event_loop.dispatch_input()

        # process the builder and check for kivy draws
        if do_kivy_tick:
            Builder.sync()
            _kivy_clock.tick_draw()
            Builder.sync()
            kivy_needs_draw = EventLoop.window.canvas.needs_redraw or need_draw
            # print (_kivy_clock.get_fps(),
            # _kivy_clock.get_rfps(), self._new_time)
        else:
            kivy_needs_draw = False

        # dispatch draw if necessary
        if kivy_needs_draw:
            EventLoop.window.dispatch('on_draw')

        # handle video and flips
        if ready_for_video:
            # we need flip if kivy needs one
            need_flip = kivy_needs_draw and self.pending_flip_time is None
            flip_time_callbacks = []
            for video in self.video_queue:
                if video.drawn and video.flip_time == self.pending_flip_time:
                    # a smile video change is ready, so we need flip
                    need_flip = True

                    # append the flip time callback
                    if video.flip_time_cb is not None:
                        flip_time_callbacks.append(video.flip_time_cb)

                    # mark that video as flipped (it's gonna be)
                    video.flipped = True
                else:
                    # no more of the videos could match, so break
                    break

            # remove any video change that's gonna be flipped
            while len(self.video_queue) and self.video_queue[0].flipped:
                del self.video_queue[0]

            # do flip if necessary
            if need_flip:
                # test if blocking or non-blocking flip
                # do a blocking if:
                # 1) Forcing a blocking flip_interval
                #   OR
                # 2) We have a specific flip callback request and we
                #      are not forcing a non-blocking flip
                if self.force_blocking_flip or \
                   (len(flip_time_callbacks) and
                        not self.force_nonblocking_flip):
                    # print "BLOCKING FLIP!"
                    self.blocking_flip()
                else:
                    # non-blocking flip
                    # print "FLIP!"
                    EventLoop.window.dispatch('on_flip')
                    self.last_flip = event_time(clock.now(), 0.0)

                # still may need to update flip_time_callbacks
                # even though they may be wrong for non-blocking flips
                for cb in flip_time_callbacks:
                    cb(self.last_flip)

                # tell refs that last_flip updated
                self.exp._screen._set_last_flip(self.last_flip)

                # no longer pending flip
                self.pending_flip_time = None

        # save the time
        self._last_time = self._new_time

        # exit if experiment done
        if not self.exp._root_executor._active:
            if self.exp._root_executor._enter_time:
                # stop if we're not active, but we have an enter time
                self.stop()

        # give time to other threads
        clock.usleep(IDLE_USLEEP)

    def blocking_flip(self):
        # TODO: use sync events instead!
        EventLoop.window.dispatch('on_flip')

        # draw a transparent point
        glVertexAttribPointer(0, 2, GL_INT, GL_FALSE, 0,
                              "\x00\x00\x00\x0a\x00\x00\x00\x0a")  # Position
        glVertexAttrib4f(3, 0.0, 0.0, 0.0, 0.0)  # Color
        glDrawArrays(GL_POINTS, 0, 1)

        # wait for flip and point to draw
        glFinish()

        # record the time immediately
        self.last_flip = event_time(clock.now(), 0.0)
        return self.last_flip

    def calc_flip_interval(self, nflips=55, nignore=5):
        diffs = 0.0
        last_time = 0.0
        count = 0.0
        for i in range(nflips):
            # perform the flip and record the flip interval
            cur_time = self.blocking_flip()
            if last_time > 0.0 and i >= nignore:
                diffs += cur_time['time'] - last_time['time']
                count += 1
            last_time = cur_time

            # add in sleep of something definitely less than the refresh rate
            clock.usleep(2000)  # 2ms for 500Hz

        # take the mean and return
        self.flip_interval = diffs / count
        return self.flip_interval

    def schedule_video(self, update_cb, flip_time=None, flip_time_cb=None):
        # TODO: Remove None options where possible
        if flip_time is None:
            flip_time = self.last_flip["time"] + self.flip_interval
        new_video = _VideoChange(update_cb, flip_time, flip_time_cb)
        if self.pending_flip_time is not None and \
           flip_time < self.pending_flip_time:
            # can't insert before already prepared pending flip
            # set flip_time to pending_flip_time
            flip_time = self.pending_flip_time
            new_video.flip_time = self.pending_flip_time
        for n, video in enumerate(self.video_queue):
            if video.flip_time > flip_time:
                self.video_queue.insert(n, new_video)
                break
        else:
            self.video_queue.append(new_video)
        return new_video

    def cancel_video(self, video):
        if not video.drawn:
            try:
                self.video_queue.remove(video)
            except ValueError:
                pass

    def screenshot(self, filename=None):
        Window.screenshot(filename)


class Experiment(object):
    """The base for a SMILE state-machine.
    An *Experiment* is the object that needs to be defined when you
    are ready to start building your smile experiment. This is also
    the class that you save all of your experimental run time
    variables into. Experiment also gives you access to things like
    screen size, resolution, and frame-rate during experimental run
    time.
    When you have all of your smile code written, the last line you
    need to add to your experiment is `exp.run()`. This will run all
    of the smile code that was written between `exp=Experiment()` and
    `exp.run()`.  Once all of the SMILE code is finished, the .py will
    continue passed `exp.run()` and run any code you might want to run
    after an experiment.
    Parameters
    ----------
    fullscreen : boolean (default = True)
        Set to False if you would like to not run in full-screen.
    resolution : tuple
        A tuple of integers that define the size of the experiment
        window.
    background_color : string (default = 'BLACK')
        If given a string color name, see colors in video.py, the
        background of the window will be set to that color
    Properties
    ----------
    screen : Screen
        Used to gain access to the size, shape, and location of variables like
        **center_x**, **height**, and **size** on the screen.
    subject : string
        The subject number/name given in the command line via `-s name` or set
        during experimental build time.
    subject_dir : string
        string to where to save this subject's data. By default, it will be
        "data\subject_name"
    info : string
        The info for the arguments you pass into the Experiment at
        initialization.
    Example
    -------
    You always want to call `exp = Experiment()` before you type your
    SMILE code. However, you do not want to put this line at the top
    of your .py.  Another thing you need to use your newly created
    *Experiment* variable is to **set** and **get** variables during
    experimental run time. You are able to add and set new attributes
    to your *Experiment* variable that will not be evaluated until
    experimental run time.
    ::
        exp = Experiment()
        exp.SavedVariable = 10
        with Loop(10) as trial:
            exp.SavedVariable += trial.i
        Label(text=exp.SavedVariable, duration=3)
        exp.run()
    This example will set SavedVariable to 10, add the numbers 0 through 9 to
    it, and then end the experiment.  At the end, exp.SavedVariable will be
    equal to 55.
    """

    def __init__(self, fullscreen=None, resolution=None, background_color=None,
                 name="Smile"):
        # global Window
        self._process_args()

        # handle fullscreen and resolution before Window is imported
        if fullscreen is not None:
            self._fullscreen = fullscreen
        self._resolution = self._resolution or resolution

        # set fullscreen and resolution
        if self._fullscreen is not None:
            Window.fullscreen = self._fullscreen
        if self._resolution is not None:
            Window.system_size = self._resolution

        # process background color
        self._background_color = background_color
        self.set_background_color()

        # make custom experiment app instance
        # self._app = ExpApp(self)
        self._screen = Screen()
        self._app = None

        # set up instance for access throughout code
        self.__class__._last_instance = weakref.ref(self)

        # set up initial root state and parent stack
        # interacts with Meanwhile and UntilDone at top of experiment
        Serial(name="EXPERIMENT BODY", parent=self)
        self._root_state.set_instantiation_context(self)
        self._parents = [self._root_state]

        # place to save experimental variables
        self._vars = {}
        self.__issued_refs = weakref.WeakValueDictionary()

        self._reserved_data_filenames = set(os.listdir(self._subj_dir))
        self._reserved_data_filenames_lock = threading.Lock()
        self._state_loggers = {}

    def set_background_color(self, color=None):
        if color is None:
            if self._background_color is None:
                return
            color = self._background_color
        Window.clearcolor = normalize_color_spec(color)

    def get_var_ref(self, name):
        try:
            return self.__issued_refs[name]
        except KeyError:
            # ref = Ref.getitem(self._vars, name)
            ref = Ref(self.get_var, name, _parent_state=self)
            self.__issued_refs[name] = ref
            return ref

    def get_var(self, name):
        """Get a user variable of this ParentState.
        """
        return self._vars[name]

    def attribute_update_state(self, name, value, index=None):
        state = Set(name, value, index=index)
        return state

    def set_var(self, name, value, index=None):
        if index is None:
            self._vars[name] = value
        else:
            self._vars[name][index] = value

        try:
            ref = self.__issued_refs[name]
        except KeyError:
            return
        ref.dep_changed()

    def __getattr__(self, name):
        if name[0] == "_":
            return super(Experiment, self).__getattribute__(name)
        else:
            return self.get_var_ref(name)

    def __setattr__(self, name, value):
        if name[0] == "_":
            super(Experiment, self).__setattr__(name, value)
        else:
            return Set(name, value)

    def __dir__(self):
        return super(Experiment, self).__dir__() + self._vars.keys()

    def _process_args(self):
        # get args from kivy_overrides
        args = kivy_overrides.args

        # set up the subject and subj dir
        self._subj = args.subject
        self._subj_dir = os.path.join('data', self._subj)
        if not os.path.exists(self._subj_dir):
            os.makedirs(self._subj_dir)

        # check for fullscreen
        if args.fullscreen:
            self._fullscreen = False
        else:
            self._fullscreen = None

        if args.resolution:
            x, y = map(int, args.resolution.split("x"))
            self._resolution = x, y
        else:
            self._resolution = None

        # set the additional info from command line (sometimes useful)
        self._info = args.info

        # set whether to log csv
        self._csv = args.csv

    def reserve_data_filename(self, title, ext=None, use_timestamp=False):
        """
        Construct a unique filename for a data file in the log directory.  The
        filename will incorporate the specified 'title' string and it will have
        extension specified with 'ext' (without the dot, if not None).  The
        filename will also incorporate a time-stamp and a number to
        disambiguate data files with the same title, extension, and time-stamp.
        The filename is not a file path.  The filename will be distinct from
        all filenames previously returned from this method even if a file of
        that name has not yet been created in the log directory.
        Returns the new filename.
        """
        if use_timestamp:
            title = "%s_%s" % (title, time.strftime("%Y%m%d%H%M%S",
                                                    time.gmtime()))
        with self._reserved_data_filenames_lock:
            self._reserved_data_filenames |= set(os.listdir(self._subj_dir))
            for distinguisher in xrange(256):
                if ext is None:
                    filename = "%s_%d" % (title, distinguisher)
                else:
                    filename = "%s_%d.%s" % (title, distinguisher, ext)
                if filename not in self._reserved_data_filenames:
                    self._reserved_data_filenames.add(filename)
                    return os.path.join(self._subj_dir, filename)
            else:
                raise RuntimeError(
                    "Too many data files with the same title, extension, and timestamp!")

    def setup_state_logger(self, state_class_name):
        if state_class_name in self._state_loggers:
            filename, logger = self._state_loggers[state_class_name]
        else:
            title = "state_" + state_class_name
            filename = self.reserve_data_filename(title, "slog")
            logger = LogWriter(filename)
            self._state_loggers[state_class_name] = filename, logger
        return filename

    def close_state_loggers(self, to_csv):
        for filename, logger in self._state_loggers.itervalues():
            logger.close()
            if to_csv:
                csv_filename = (os.path.splitext(filename)[0] + ".csv")
                log2csv(filename, csv_filename)
        self._state_loggers = {}

    def write_to_state_log(self, state_class_name, record):
        self._state_loggers[state_class_name][1].write_record(record)

    @property
    def screen(self):
        return self._screen

    @property
    def subject(self):
        return self._subj

    @property
    def subject_dir(self):
        return self._subj_dir

    @property
    def info(self):
        return self._info

    def start(self):
        # open all the logs
        # (this will call begin_log for entire state machine)
        self._root_state.begin_log()

        # clone the root state in prep for starting the state machine
        self._root_executor = self._root_state._clone(None)

        # start it up
        self._root_executor.enter(clock.now() + 0.25)

    def finish(self):
        # clean up logs if we made it here
        self._root_state.end_log(self._csv)
        self.close_state_loggers(self._csv)

    def run(self, trace=False):
        self._current_state = None
        if trace:
            self._root_state.tron()

        # open all the logs
        # (this will call begin_log for entire state machine)
        self._root_state.begin_log()

        # clone the root state in prep for starting the state machine
        self._root_executor = self._root_state._clone(None)
        try:
            # start the first state (that's the root state)
            # self._root_executor.enter(clock.now() + 0.25)

            # kivy main loop
            self._app = ExpApp(self)
            self._app.run()

        except:
            # clean up the logs
            self._root_state.end_log(self._csv)
            self.close_state_loggers(self._csv)

            # see if we can traceback
            if self._current_state is not None:
                self._current_state.print_traceback()

            # raise the error
            raise

        # clean up logs if we made it here
        self._root_state.end_log(self._csv)
        self.close_state_loggers(self._csv)


class Set(AutoFinalizeState):
    """How to set a variable during Experimental Runtime.
    Whenever you ask SMILE to set an `exp.` variable, SMILE will create a
    Set state. The same way you can set using `exp.` you can with Set. On
    enter(), a Set state will call the Experiment method `set_var` which
    checks to see if the variable was created, creates it if not, and then
    fills it with the value passed into the Set state.
    Parameters
    ----------
    var_name : string
       The name of the variable you want to set. This is the same as what
       you would put next to `exp.`.
    value : object
       Whatever you would like to set the variable's value to.
    parent : ParentState
       The parent state that this state is contained within.
    save_log : Boolean (False)
       If set to True, will save a .slog with all of the information from
       this state.
    name : string, optional, default = None
        The unique name you give this state.
    """

    def __init__(self, var_name, value, index=None,
                 parent=None, save_log=True, name=None):
        # init the parent class
        super(Set, self).__init__(parent=parent,
                                  save_log=save_log,
                                  name=name,
                                  duration=0.0)
        self._init_var_name = var_name
        self._init_value = value
        self._init_index = index

        self._log_attrs.extend(['var_name', 'value', 'index'])

    def _enter(self):
        self._exp.set_var(self._var_name, self._value, self._index)
        clock.schedule(self.leave)
        self._started = True
        self._ended = True


if __name__ == '__main__':
    # can't run inside this file
    # exp = Experiment(fullscreen=False, pyglet_vsync=False)
    # exp.run()
    pass
