#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# import main modules
#from __future__ import with_statement
import sys
import os
import weakref
import argparse
import time
import threading

# kivy imports
import kivy_overrides
import kivy
import kivy.base
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.base import EventLoop
from kivy.core.window import Window
from kivy.graphics.opengl import (
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glVertexAttrib4f,
    glDrawArrays,
    glDisableVertexAttribArray,
    glFinish,
    GL_INT,
    GL_FALSE,
    GL_POINTS)
import kivy.clock
_kivy_clock = kivy.clock.Clock

# local imports
from state import Serial, AutoFinalizeState
from ref import val, Ref
from clock import clock
from log import LogWriter, log2csv

def event_time(time, time_error=0.0):
    return {'time': time, 'error': time_error}


class _VideoChange(object):
    def __init__(self, update_cb, flip_time, flip_time_cb):
        self.update_cb = update_cb
        self.flip_time = flip_time
        self.flip_time_cb = flip_time_cb
        self.drawn = False
        self.flipped = False


class Screen(object):
    def __init__(self, app):
        self.__app = app

    @property
    def width(self):
        return self.__app.width_ref

    @property
    def height(self):
        return self.__app.height_ref

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
    def __init__(self, exp, *pargs, **kwargs):
        super(ExpApp, self).__init__(*pargs, **kwargs)
        self.exp = exp
        self.callbacks = {}
        self.pending_flip_time = None
        self.video_queue = []
        self.keys_down = set()
        self.issued_key_refs = weakref.WeakValueDictionary()
        self.mouse_pos = (None, None)
        self.mouse_pos_ref = Ref.getattr(self, "mouse_pos")
        self.mouse_button = None
        self.mouse_button_ref = Ref.getattr(self, "mouse_button")
        self.width_ref = Ref.getattr(Window, "width")
        self.height_ref = Ref.getattr(Window, "height")
        self.__screen = Screen(self)

    @property
    def screen(self):
        return self.__screen

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
        try:
            callbacks = self.callbacks[event_name]
        except KeyError:
            return
        for func in callbacks:
            func(*pargs, **kwargs)

    def build(self):
        self.wid = FloatLayout()
        Window._system_keyboard.bind(on_key_down=self._on_key_down,
                                     on_key_up=self._on_key_up)
        Window.bind(on_motion=self._on_motion,
                    mouse_pos=self._on_mouse_pos,
                    on_resize=self._on_resize)
        self.current_touch = None
        
        self._last_time = clock.now()
        self._last_kivy_tick = clock.now()
        kivy.base.EventLoop.set_idle_callback(self._idle_callback)
        print 1.0 / self.calc_flip_interval()  #...
        return self.wid

    def _on_resize(self):
        self.width_ref.dep_changed()
        self.height_ref.dep_changed()

    def is_key_down(self, name):
        return name.upper() in self.keys_down

    def get_key_ref(self, name):
        try:
            return self.issued_key_refs[name]
        except KeyError:
            ref = Ref(self.is_key_down, name)
            self.issued_key_refs[name] = ref
            return ref

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[0] == 27 and "shift" in modifiers:
            self.stop()
            return
        name = keycode[1].upper()
        self.keys_down.add(name)
        try:
            self.issued_key_refs[name].dep_changed()
        except KeyError:
            pass
        self._trigger_callback("KEY_DOWN", keycode, text, modifiers,
                               self.event_time)

    def _on_key_up(self, keyboard, keycode):
        name = keycode[1].upper()
        self.keys_down.discard(name)
        try:
            self.issued_key_refs[name].dep_changed()
        except KeyError:
            pass
        self._trigger_callback("KEY_UP", keycode, self.event_time)

    def _on_mouse_pos(self, window, pos):
        if self.current_touch is None:
            self.mouse_pos = tuple(pos)
            self.mouse_pos_ref.dep_changed()
            self._trigger_callback("MOTION", pos=pos, button=None,
                                   newly_pressed=False,
                                   double=False, triple=False,
                                   event_time=self.event_time)

    def _on_motion(self, window, etype, me):
        if etype == "begin":
            self.mouse_button = me.button
            self.mouse_button_ref.dep_changed()
            self.current_touch = me
            self._trigger_callback("MOTION", pos=me.pos, button=me.button,
                                   newly_pressed=True,
                                   double=me.is_double_tap,
                                   triple=me.is_triple_tap,
                                   event_time=self.event_time)
        elif etype == "update":
            self.mouse_pos = tuple(int(round(x)) for x in  me.pos)
            self.mouse_pos_ref.dep_changed()
            self.current_touch = me
            self._trigger_callback("MOTION", pos=me.pos, button=me.button,
                                   newly_pressed=False,
                                   double=me.is_double_tap,
                                   triple=me.is_triple_tap,
                                   event_time=self.event_time)
        else:
            self.mouse_button = None
            self.mouse_button_ref.dep_changed()
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

        clock.tick()

        ready_for_video = (self._new_time - self.last_flip["time"] >=
                           self.flip_interval)
        ready_for_kivy_tick = ready_for_video and (self._new_time -
                                                   self._last_kivy_tick >=
                                                   self.flip_interval)

        need_draw = False
        for video in self.video_queue:
            if (not video.drawn and
                ((self.pending_flip_time is None and
                  self._new_time >= video.flip_time -
                  self.flip_interval / 2.0) or
                 video.flip_time == self.pending_flip_time)):
                video.update_cb()
                need_draw = True
                video.drawn = True
                self.pending_flip_time = video.flip_time
            else:
                break
        do_kivy_tick = ready_for_kivy_tick or need_draw
        if do_kivy_tick:
            _kivy_clock.tick()
            self._last_kivy_tick = self._new_time
        event_loop.dispatch_input()
        if do_kivy_tick:
            Builder.sync()
            _kivy_clock.tick_draw()
            Builder.sync()
            kivy_needs_draw = EventLoop.window.canvas.needs_redraw
            #print (_kivy_clock.get_fps(), _kivy_clock.get_rfps(), self._new_time)  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        else:
            kivy_needs_draw = False
        if kivy_needs_draw:
            EventLoop.window.dispatch('on_draw')

        if ready_for_video:
            need_flip = kivy_needs_draw and self.pending_flip_time is None
            flip_time_callbacks = []
            for video in self.video_queue:
                if video.drawn and video.flip_time == self.pending_flip_time:
                    need_flip = True
                    if video.flip_time_cb is not None:
                        flip_time_callbacks.append(video.flip_time_cb)
                    video.flipped = True
                else:
                    break
            while len(self.video_queue) and self.video_queue[0].flipped:
                del self.video_queue[0]
            if need_flip:
                if len(flip_time_callbacks):
                    #print "BLOCKING FLIP!"  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    self.blocking_flip()  #TODO: use sync events instead!
                    for cb in flip_time_callbacks:
                        cb(self.last_flip)
                else:
                    #print "FLIP!"  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    EventLoop.window.dispatch('on_flip')
                    self.last_flip = event_time(clock.now(), 0.0)
                self.pending_flip_time = None

        # save the time
        self._last_time = self._new_time

        # exit if experiment done
        if not self.exp.root_state._active:
            self.stop()

    def blocking_flip(self):
        EventLoop.window.dispatch('on_flip')
        #glEnableVertexAttribArray(0)  # kivy has this enabled already
        glVertexAttribPointer(0, 2, GL_INT, GL_FALSE, 0,
                              "\x00\x00\x00\x0a\x00\x00\x00\x0a")  # Position
        glVertexAttrib4f(3, 0.0, 0.0, 0.0, 0.0)  # Color
        glDrawArrays(GL_POINTS, 0, 1)
        #glDisableVertexAttribArray(0)  # kivy needs this to stay enabled
        glFinish()
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
            clock.usleep(5000)  # 5ms for 200Hz
        
        # take the mean and return
        self.flip_interval = diffs / count
        return self.flip_interval

    def schedule_video(self, update_cb, flip_time=None, flip_time_cb=None):
        if flip_time is None:
            flip_time = self.last_flip["time"] + self.flip_interval
        new_video = _VideoChange(update_cb, flip_time, flip_time_cb)
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


class Experiment(object):
    def __init__(self, fullscreen=False, resolution=(800,600), name="Smile",
                 vsync=True, background_color=(0,0,0,1), screen_ind=0):

        # first process the args
        self._process_args()

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.vsync = vsync
        self.fullscreen = fullscreen or self.fullscreen
        self.resolution = resolution

        self.app = ExpApp(self)

        # set the clear color
        self._background_color = background_color

        # set up instance for access throughout code
        self.__class__.last_instance = weakref.ref(self)

        # set up initial root state and parent stack
        Serial(name="EXPERIMENT BODY", parent=self)
        self.root_state.set_instantiation_context(self)
        self._parents = [self.root_state]

        # we have not flipped yet
        self.last_flip = event_time(0.0)
        
        # event time
        self.last_event = event_time(0.0)

        # default flip interval
        self.flip_interval = 1.0 / 60.0

        # place to save experimental variables
        self._vars = {}
        self.issued_refs = weakref.WeakValueDictionary()

        self._reserved_data_filenames = set(os.listdir(self.subj_dir))
        self._reserved_data_filenames_lock = threading.Lock()
        self._state_loggers = {}

    def _process_args(self):
        # set up the arg parser
        parser = argparse.ArgumentParser(description='Run a SMILE experiment.')
        parser.add_argument("-s", "--subject", 
                            help="unique subject id", 
                            default='test000')        
        parser.add_argument("-f", "--fullscreen", 
                            help="toggle fullscreen", 
                            action='store_true')   
        parser.add_argument("-si", "--screen", 
                            help="screen index", 
                            type=int,
                            default=0)        
        parser.add_argument("-i", "--info", 
                            help="additional run info", 
                            default='')        
        parser.add_argument("-c", "--csv", 
                            help="perform automatic conversion of yaml logs to csv", 
                            action='store_true')   

        # do the parsing
        args = parser.parse_args()

        # set up the subject and subj dir
        self.subj = args.subject
        self.subj_dir = os.path.join('data',self.subj)
        if not os.path.exists(self.subj_dir):
            os.makedirs(self.subj_dir)

        # check for fullscreen
        self.fullscreen = args.fullscreen

        # check screen ind
        self.screen_ind = args.screen

        # set the additional info
        self.info = args.info

        # set whether to log csv
        self.csv = args.csv

    def reserve_data_filename(self, title, ext=None, use_timestamp=False):
        """
        Construct a unique filename for a data file in the log directory.  The
        filename will incorporate the specified 'title' string and it will have
        extension specified with 'ext' (without the dot, if not None).  The
        filename will also incorporate a timestamp and a number to disambiguate
        data files with the same title, extension, and timestamp.  The filename
        is not a file path.  The filename will be distinct from all filenames
        previously returned from this method even if a file of that name has
        not yet been created in the log directory.

        Returns the new filename.
        """
        if use_timestamp:
            title = "%s_%s" % (title, time.strftime("%Y%m%d%H%M%S",
                                                    time.gmtime()))
        with self._reserved_data_filenames_lock:
            self._reserved_data_filenames |= set(os.listdir(self.subj_dir))
            for distinguisher in xrange(256):
                if ext is None:
                    filename = "%s_%d" % (title, distinguisher)
                else:
                    filename = "%s_%d.%s" % (title, distinguisher, ext)
                if filename not in self._reserved_data_filenames:
                    self._reserved_data_filenames.add(filename)
                    return os.path.join(self.subj_dir, filename)
            else:
                raise RuntimeError(
                    "Too many data files with the same title, extension, and timestamp!")

    def setup_state_logger(self, state_class_name, field_names):
        field_names = tuple(field_names)
        if state_class_name in self._state_loggers:
            if field_names == self._state_loggers[state_class_name][2]:
                return
            raise ValueError("'field_names' changed for state class %r!" %
                             state_class_name)
        title = "state_" + state_class_name
        filename = self.reserve_data_filename(title, "smlog") 
        logger = LogWriter(filename, field_names)
        self._state_loggers[state_class_name] = filename, logger, field_names

    def close_state_loggers(self, to_csv):
        for filename, logger, field_names in self._state_loggers.itervalues():
            logger.close()
            if to_csv:
                csv_filename = (os.path.splitext(filename)[0] + ".csv")
                log2csv(filename, csv_filename)
        self._state_loggers = {}

    def write_to_state_log(self, state_class_name, record):
        self._state_loggers[state_class_name][1].write_record(record)

    @property
    def screen(self):
        return self.app.screen

    def run(self, trace=False):
        """
        Run the experiment.
        """
        # create the window
        #self.app = ExpApp(self)

        self.current_state = None
        if trace:
            self.root_state.tron()
        self.root_state.begin_log()
        try:
            # start the first state (that's the root state)
            self.root_state.enter()

            # kivy main loop
            self.app.run()
        except:
            if self.current_state is not None:
                self.current_state.print_traceback()
            raise
        self.root_state.end_log(True) #self.csv) #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.close_state_loggers(True) #self.csv) #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


class Set(AutoFinalizeState):
    def __init__(self, parent=None, save_log=True, name=None, **kwargs):
        # init the parent class
        super(Set, self).__init__(parent=parent,
                                  save_log=save_log,
                                  name=name,
                                  duration=0.0)
        self._init_values = kwargs

        self._log_attrs.extend(['values'])

    def get_log_fields(self):
        return ['instantiation_filename', 'instantiation_lineno', 'name',
                'time', 'var_name', 'value']

    def save_log(self):
        class_name = type(self).__name__
        for name, value in self._values.iteritems():
            field_values = {
                "instantiation_filename": self._instantiation_filename,
                "instantiation_lineno": self._instantiation_lineno,
                "name": self._name,
                "time": self._start_time,
                "var_name": name,
                "value": value
                }
            self._exp.write_to_state_log(class_name, field_values)
        
    def _enter(self):
        for name, value in self._values.iteritems():
            self._exp._vars[name] = value
            try:
                ref = self._exp.issued_refs[name]
            except KeyError:
                continue
            ref.dep_changed()
        clock.schedule(self.leave)

        
def Get(variable):
    exp = Experiment.last_instance()
    try:
        return exp.issued_refs[variable]
    except KeyError:
        ref = Ref.getitem(exp._vars, variable)
        exp.issued_refs[variable] = ref
        return ref


if __name__ == '__main__':
    # can't run inside this file
    #exp = Experiment(fullscreen=False, pyglet_vsync=False)
    #exp.run()
    pass
