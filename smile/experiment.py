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
from kivy.uix.widget import Widget
from kivy import clock
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.base import EventLoop

# local imports
from state import Serial, State, RunOnEnter
from ref import val, Ref
from log import dump, yaml2csv

# set up the basic timer
now = clock._default_time
def event_time(time, time_error=0.0):
    return {'time': time, 'error': time_error}

class ExpApp(App):
    def __init__(self, exp, *pargs, **kwargs):
        super(ExpApp, self).__init__(*pargs, **kwargs)
        self.exp = exp
        self.key_callbacks = []
        self.mouse_callbacks = []
        self.need_flip = False  #???
        self.need_draw = False  #???

    def build(self):
        self.canvas = Widget()
        #TODO: bind kivy events
        #...
        self._last_time = now()  #???
        kivy.base.EventLoop.set_idle_callback(self.idle_callback)

    def idle_callback(self, event_loop):
        # record the time range
        self._new_time = now()
        time_err = (self._new_time - self._last_time) / 2.0
        self.event_time = event_time(self._last_time + time_err, time_err)

        # update dt
        Clock.tick()

        # read and dispatch input from providers
        event_loop.dispatch_input()

        # flush all the canvas operation
        Builder.sync()  # do these calls do anything when a .kv file is not used?

        # tick before draw
        Clock.tick_draw()

        # flush all the canvas operation
        Builder.sync()

        # save the time
        self._last_time = self._new_time

        # exit if experiment done
        if self.exp.done:
            self.stop()

    def draw(self):
        #TODO: return if no draw needed?
        EventLoop.window.dispatch('on_draw')

    def flip(self):
        #TODO: return if no flip needed?
        EventLoop.window.dispatch('on_flip')

    def blocking_flip(self):
        #TODO: return if no flip needed?
        self.flip()
        #TODO: draw single transparent point
        #TODO: glFinish
        self.flip()
        self.last_flip = event_time(now(), 0.0)
        #TODO: clear need_flip?
        return self.last_flip

    def calc_flip_interval(self, nflips=55, nignore=5):
        diffs = 0.0
        last_time = 0.0
        count = 0.0
        for i in range(nflips):
            # must draw something so the flip happens
            #TODO: draw something

            # perform the flip and record the flip interval
            cur_time = self.blocking_flip()
            if last_time > 0.0 and i >= nignore:
                diffs += cur_time['time'] - last_time['time']
                count += 1
            last_time = cur_time

            # add in sleep of something definitely less than the refresh rate
            Clock.usleep(5000)  # 5ms for 200Hz

        # reset the background color
        #TODO: clear drawing
        self.blocking_flip()
        
        # take the mean and return
        self.flip_interval = diffs / count
        return self.flip_interval

    #...


class Experiment(Serial):
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
        
        # set up the state
        super(Experiment, self).__init__(parent=None, duration=-1)

        # set up the window
        #screens = pyglet.window.get_platform().get_default_display().get_screens()  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #if screen_ind != self.screen_ind:
        #    # command line overrides
        #    screen_ind = self.screen_ind  #IS: isn't this if statement just equivalent to "screen_ind = self.screen_ind"?
        self.screen = None  #screens[screen_ind]  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.vsync = vsync
        self.fullscreen = fullscreen or self.fullscreen
        self.resolution = resolution
        self.name = name
        self.app = None   # will create when run

        # set the clear color
        self._background_color = background_color

        # get a clock for sleeping 
        self.clock = clock.Clock

        # set up instance for access throughout code
        self.__class__.last_instance = weakref.ref(self)

        # init parents (with self at top)
        self._parents = [self]
        #global state._global_parents
        #state._global_parents.append(self)

        # we have not flipped yet
        self.last_flip = event_time(0.0)
        
        # event time
        self.last_event = event_time(0.0)

        # default flip interval
        self.flip_interval = 1 / 60.

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

    def run(self):
        """
        Run the experiment.
        """
        # create the window
        if self.fullscreen:
            self.app = ExpApp(self)
            #self.app = ExpApp(self, fullscreen=True, 
            #                  caption=self.name, 
            #                  vsync=self.vsync,
            #                  screen=self.screen)
        else:
            self.app = ExpApp(self)
            #self.app = ExpApp(self, *(self.resolution),
            #                  fullscreen=self.fullscreen, 
            #                  caption=self.name, 
            #                  vsync=self.vsync,
            #                  screen=self.screen)

        # set the clear color
        #self.window.set_clear_color(self._background_color)  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # set the mouse as desired
        #self.window.set_exclusive_mouse()
        #self.window.set_mouse_visible(False)                #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # get flip interval
        #self.flip_interval = self._calc_flip_interval()
        #print "Monitor Flip Interval is %f (%f Hz)"%(self.flip_interval,1./self.flip_interval)  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # first clear and do a flip
        #self.window.on_draw(force=True)
        #self.blocking_flip()  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # start the first state (that's this experiment)
        self.enter()

        # kivy main loop
        self.app.run()

        # write out csv logs if desired
        if self.csv:
            self.state_log_stream.flush()
            yaml2csv(self.state_log,
                     os.path.splitext(self.state_log)[0] + '.csv')
            self.exp_log_stream.flush()
            yaml2csv(self.exp_log, os.path.splitext(self.exp_log)[0] + '.csv')


class Set(State, RunOnEnter):
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
    def __init__(self, variable, value, eval_var=True, parent=None, save_log=True):

        # init the parent class
        super(Set, self).__init__(interval=0, parent=parent, 
                                  duration=0,
                                  save_log=save_log)
        self.var = variable
        self.variable = None
        self.val = value
        self.value = None
        self.eval_var = eval_var

        # append log vars
        self.log_attrs.extend(['variable','value'])
        
    def _callback(self, dt):
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


class Log(State, RunOnEnter):
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
    def __init__(self, log_dict=None, log_file=None, parent=None, **log_items):

        # init the parent class
        super(Log, self).__init__(interval=0, parent=parent, 
                                  duration=0,
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
        
    def _callback(self, dt):
        # eval the log_items and write the log
        keyvals = [(k,val(v)) for k,v in self.log_items.iteritems()]
        log = dict(keyvals)
        if self.log_dict:
            log.update(val(self.log_dict))
        # log it to the correct file
        dump([log], self._get_stream())
        pass
    
            
if __name__ == '__main__':
    # can't run inside this file
    #exp = Experiment(fullscreen=False, pyglet_vsync=False)
    #exp.run()
    pass
