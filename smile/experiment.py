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
#from kivy.uix.widget import Widget
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
from log import dump, yaml2csv
from clock import clock

def event_time(time, time_error=0.0):
    return {'time': time, 'error': time_error}


class _VideoChange(object):
    def __init__(self, update_cb, flip_time, flip_time_cb):
        self.update_cb = update_cb
        self.flip_time = flip_time
        self.flip_time_cb = flip_time_cb
        self.drawn = False
        self.flipped = False


class ExpApp(App):
    def __init__(self, exp, *pargs, **kwargs):
        super(ExpApp, self).__init__(*pargs, **kwargs)
        self.exp = exp
        self.callbacks = {}
        self.pending_flip_time = None
        self.video_queue = []

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
        #self.wid = Widget()
        #TODO: bind kivy events...
        Window._system_keyboard.bind(on_key_down=self._on_key_down,
                                     on_key_up=self._on_key_up)
        Window.bind(on_mouse_up=self._on_mouse_up,
                    on_mouse_down=self._on_mouse_down,
                    on_mouse_move=self._on_mouse_move,
                    on_motion=self._on_motion)
        #...
        self._last_time = clock.now()  #???
        self._last_kivy_tick = clock.now()  #???
        kivy.base.EventLoop.set_idle_callback(self._idle_callback)
        print 1.0 / self.calc_flip_interval()  #...
        return self.wid

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[0] == 27 and "shift" in modifiers:
            self.stop()
            return
        self._trigger_callback("KEY_DOWN", keycode, text, modifiers,
                               self.event_time)

    def _on_key_up(self, keyboard, keycode):
        self._trigger_callback("KEY_UP", keycode, self.event_time)

    def _on_mouse_down(self, x, y, button, modifiers):
        print "mouse down %r, %r, %r, %r" % (x, y, button, modifiers)

    def _on_mouse_up(self, x, y, button, modifiers):
        print "mouse up %r, %r, %r, %r" % (x, y, button, modifiers)

    def _on_mouse_move(self, x, y, modifiers):
        print "mouse move %r, %r, %r" % (x, y, modifiers)

    def _on_motion(self, *pargs):
        print "motion %r" % (pargs,)

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
        if not self.exp.root_state.active:
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
    """
    A SMILE experiment.

    This is the top level parent state for all experiments. It handles
    the event loop, manages the window and associated input/output,
    and processes the command line arguments.

    Parameters
    ----------
    fullscreen : bool
        Create the window in full screen.
    resolution : tuple
        Resolution of the window specified as (width, height) when not 
        full screen.
    name : str
        Name on the window title bar.
    pyglet_vsync : bool
        Whether to instruct pyglet to sync to the vertical retrace.
    background_color : tuple
        4 tuple specifying the background color of the experiment 
        window in (R,G,B,A).
    screen_id : int
        What screen/monitor to send the window to in multi-monitor 
        layouts.
    
    Example
    -------
    exp = Experiment(resolution=(1920x1080), background_color=(0,1,0,1.0))
    ...
    run(exp)
    Define an experiment window with a green background and a size of
    1920x1080 pixels. This experiment window will not open until the 
    run() command is executed. 
            
    Log Parameters
    --------------
    All parameters above and below are available to be accessed and 
    manipulated within the experiment code, and will be automatically 
    recorded in the state.yaml and state.csv files. Refer to State class
    docstring for addtional logged parameters.              
    """
    def __init__(self, fullscreen=False, resolution=(800,600), name="Smile",
                 vsync=True, background_color=(0,0,0,1), screen_ind=0):

        # first process the args
        self._process_args()

        # set up the window
        #screens = pyglet.window.get_platform().get_default_display().get_screens()  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #if screen_ind != self.screen_ind:
        #    # command line overrides
        #    screen_ind = self.screen_ind  #IS: isn't this if statement just equivalent to "screen_ind = self.screen_ind"?
        self.screen = None  #screens[screen_ind]  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.vsync = vsync
        self.fullscreen = fullscreen or self.fullscreen
        self.resolution = resolution
        self.app = None   # will create when run

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

        # add log locs (state.yaml, experiment.yaml)
        self.state_log = os.path.join(self.subj_dir, 'state.yaml')
        self.state_log_stream = open(self.state_log, 'a')
        self.exp_log = os.path.join(self.subj_dir, 'exp.yaml')
        self.exp_log_stream = open(self.exp_log, 'a')
        self._reserved_data_filenames = set(os.listdir(self.subj_dir))
        self._reserved_data_filenames_lock = threading.Lock()

        # # grab the nice
        # import psutil
        # self._current_proc = psutil.Process(os.getpid())
        # cur_nice = self._current_proc.get_nice()
        # print "Current nice: %d" % cur_nice
        # if hasattr(psutil,'HIGH_PRIORITY_CLASS'):
        #     new_nice = psutil.HIGH_PRIORITY_CLASS
        # else:
        #     new_nice = -10
        # self._current_proc.set_nice(new_nice)
        # print "New nice: %d" % self._current_proc.get_nice()

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

    def reserve_data_filename(self, title, ext=None):
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
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        with self._reserved_data_filenames_lock:
            self._reserved_data_filenames |= set(os.listdir(self.subj_dir))
            for distinguisher in xrange(256):
                if ext is None:
                    filename = "%s_%s_%d" % (title, timestamp, distinguisher)
                else:
                    filename = "%s_%s_%s.%s" % (title, timestamp,
                                                distinguisher, ext)
                if filename not in self._reserved_data_filenames:
                    self._reserved_data_filenames.add(filename)
                    return filename
            else:
                raise RuntimeError(
                    "Too many data files with the same title, extension, and timestamp!")

    def run(self, trace=False):
        """
        Run the experiment.
        """
        # create the window
        self.app = ExpApp(self)

        self.current_state = None
        if trace:
            self.root_state.tron()
        try:
            # start the first state (that's the root state)
            self.root_state.enter()

            # kivy main loop
            self.app.run()
        except:
            if self.current_state is not None:
                self.current_state.print_traceback()
            raise

        # write out csv logs if desired
        if self.csv:
            self.state_log_stream.flush()
            yaml2csv(self.state_log,
                     os.path.splitext(self.state_log)[0] + '.csv')
            self.exp_log_stream.flush()
            yaml2csv(self.exp_log, os.path.splitext(self.exp_log)[0] + '.csv')


class Set(AutoFinalizeState):
    """
    State to set a experiment variable.

    See Get state for how to access experiment variables.
    
    Parameters
    ----------
    variable : str
        Name of variable to save.
    value : object
        Value to set the variable. Can be a Reference evaluated at 
        runtime.
    eval_var : bool
        If set to 'True,' the variable will be evaluated at runtime.
    parent : {None, ``ParentState``}
        Parent state to attach to. Will search for experiment if None.
    save_log : bool
        If set to 'True,' details about the state will be
        automatically saved in the log files. 
    
    Example
    -------
    See Get state for example.
    
    Log Parameters
    --------------
    All parameters above are available to be accessed and 
    manipulated within the experiment code, and will be automatically 
    recorded in the state.yaml and state.csv files. Refer to State class
    docstring for addtional logged parameters. 
    """
    def __init__(self, variable, value, eval_var=True, parent=None,
                 save_log=True, name=None):
        # init the parent class
        super(Set, self).__init__(parent=parent,
                                  save_log=save_log,
                                  name=name)
        self.var = variable
        self.variable = None
        self.val = value
        self.value = None
        self.eval_var = eval_var

        # append log vars
        self.log_attrs.extend(['variable','value'])
        
    def _enter(self):
        # set the exp var
        if self.eval_var:
            self.variable = val(self.var)
        else:
            self.variable = self.var
        self.value = val(self.val)
        if isinstance(self.variable, str):
            # set the experiment variable
            self.exp._vars[self.variable] = self.value
        elif isinstance(self.variable, Ref):
            # set the ref
            self.variable.set(self.value)
        else:
            raise ValueError('Unrecognized variable type. Must either be string or Ref')
        clock.schedule(self.leave)
        self.end_time = self.start_time

        
def Get(variable):
    """Retrieve an experiment variable.

    Parameters
    ----------
    variable : str
        Name of variable to retrieve. Can be a Reference evaluated 
        at runtime.
        
    Example
    -------
    with Parallel():
        txt = Text('Press a key as quickly as you can!')
        key = KeyPress(base_time=txt['last_flip']['time'])
    Unshow(txt)
    Set('good',key['rt']<0.5)
    with If(Get('good')) as if_state:
        with if_state.true_state:
            Show(Text('Good job!'), duration=1.0)
        with if_state.false_state:
            Show(Text('Better luck next time.'), duration=1.0)
            
    Text will be shown on the screen, instructing the participant to press 
    a key as quickly as they can. The participant will press a key while 
    the text is on the screen, then the text will be removed. The 'Set' 
    state will be used to define a variable for assessing the participant's 
    reaction time for the key press that just occurred, and the 'Get' state 
    accesses that new variable. If the participant's reaction time was 
    faster than 0.5 seconds, the text 'Good job!' will appear on the 
    screen. If the participant's reaction time was slower than 0.5 seconds, 
    the text 'Better luck next time.' will appear on the screen.
    
    Log Parameters
    --------------
    All parameters above are available to be accessed and 
    manipulated within the experiment code, and will be automatically 
    recorded in the state.yaml and state.csv files. Refer to State class
    docstring for addtional logged parameters. 
    """
    gfunc = lambda : Experiment.last_instance()._vars[val(variable)]
    return Ref(gfunc=gfunc)


class Log(AutoFinalizeState):
    """
    State to write values to a custom experiment log.
    Write data to a YAML log file.

    Parameters
    ----------
    log_dict : dict
        Key-value pairs to log. Handy for logging trial information.
    log_file : str, optional
        Where to log, defaults to exp.yaml in the subject directory.
    parent : {None, ``ParentState``}
        Parent state to attach to. Will search for experiment if None.
    **log_items : kwargs
        Key-value pairs to log.
        
    Example
    --------
    numbers_list = [1,2,3]
    with Loop(numbers_list) as trial:
        num = Text(trial.current)
        key = KeyPress()
        Unshow(num)
        
    Log(stim = trial.current,
        response = key['pressed'])
    
    Each number in numbers_list will appear on the screen, and will be
    removed from the screen after the participant presses a key. For each
    trial in the loop, the number that appeared on the screen as well as
    the key that the participant pressed will be recorded in the log files.
    
    Log Parameters
    --------------
    The following information about each state will be stored in addition 
    to the state-specific parameters:

        duration : 
            Duration of the state in seconds. If the duration is not set
            as a parameter of the specific state, it will default to -1 
            (which means it will be calculated on exit) or 0 (which means
            the state completes immediately and does not increment the
            experiment clock).
        end_time :
            Unix timestamp for when the state ended.
        first_call_error
            Amount of time in seconds between when the state was supposed
            to start and when it actually started.
        first_call_time :
            Unix timestamp for when the state was called.
        last_call_error :
            Same as first_call_error, but refers to the most recent time 
            time the state was called.
        last_draw :
            Unix timestamp for when the last draw of a visual stimulus
            occurred.
        last_flip :
            Unix timestamp for when the last flip occurred (i.e., when 
            the stimulus actually appeared on the screen).
        last_update :
            Unix timestamp for the last time the context to be drawn 
            occurred. (NOTE: Displaying a stimulus entails updating it,
            drqwing it to the back buffer, then flipping the front and
            back video buffers to display the stimulus.
        start_time :
            Unix timestamp for when the state is supposed to begin.
        state_time :
            Same as start_time.
    """
    def __init__(self, log_dict=None, log_file=None, parent=None, name=None,
                 **log_items):
        # init the parent class
        super(Log, self).__init__(parent=parent,
                                  name=name,
                                  duration=0.0,
                                  save_log=False)
        self.log_file = log_file
        self.log_items = log_items
        self.log_dict = log_dict

    def _get_stream(self):
        if self.log_file is None:
            stream = self.exp.exp_log_stream
        else:
            # make it from the name
            stream = open(os.path.join(self.exp.subj_dir,self.log_file),'a')
        return stream
        
    def _enter(self):
        # eval the log_items and write the log
        keyvals = [(k,val(v)) for k,v in self.log_items.iteritems()]
        log = dict(keyvals)
        if self.log_dict:
            log.update(val(self.log_dict))
        # log it to the correct file
        dump([log], self._get_stream())
        clock.schedule(self.leave)

if __name__ == '__main__':
    # can't run inside this file
    #exp = Experiment(fullscreen=False, pyglet_vsync=False)
    #exp.run()
    pass
