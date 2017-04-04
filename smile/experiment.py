# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# import main modules
import os

import weakref
import time
import threading

# kivy imports
import kivy_overrides
import kivy
import kivy.base
from kivy.utils import platform
import kivy.clock

# local imports
from state import Serial, AutoFinalizeState
from ref import Ref
from clock import clock
from log import LogWriter, log2csv
from event import event_time

_kivy_clock = kivy.clock.Clock


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
        String to where to save this subject's sessions. By default, it will be
        "data\experiment_name\subject\*"
    session : string
        The session number in the format YYYYMMDD_HHmmss, where the hours are
        on the 24 hour clock.
    session_dir : string
        String to the directory where this subjects data for this session
        exists. "data\experiment_name\subject\session\*"
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
                 name="SMILE"):

        self._platform = platform
        self._exp_name = name
        self._session = time.strftime("%Y%m%d_%H%M%S")

        self._process_args()

        # handle fullscreen and resolution before Window is imported
        if fullscreen is not None:
            self._fullscreen = fullscreen
        self._resolution = self._resolution or resolution

        # process background color
        self._background_color = background_color

        # make custom experiment app instance
        #self._app = ExpApp(self)
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

        self._reserved_data_filenames = set(os.listdir(os.path.join(self._session_dir)))
        self._reserved_data_filenames_lock = threading.Lock()
        self._state_loggers = {}

    def _change_smile_subj(self, subj_id):
        kconfig = kivy_overrides._get_config()

        for filename, logger in self._state_loggers.itervalues():
            logger.close()
            os.remove(filename)

        self._subject = subj_id

        self._subject_dir = os.path.join(kconfig['default_data_dir'],
                                         self._exp_name, subj_id)

        self._session_dir = os.path.join(kconfig['default_data_dir'],
                                         self._exp_name, subj_id,
                                         self._session)

        if not os.path.isdir(self._session_dir):
            os.makedirs(self._session_dir)

        self._reserved_data_filenames = set(os.listdir(self._session_dir))
        self._reserved_data_filenames_lock = threading.Lock()
        self._state_loggers = {}
        self._root_state.begin_log()

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
        # and config variables from kivy
        args = kivy_overrides.args
        kconfig = kivy_overrides._get_config()

        # set up the subject and subj dir
        self._subject = args.subject

        self._subject_dir = os.path.join(kconfig['default_data_dir'],
                                         self._exp_name, self._subject)

        self._session_dir = os.path.join(kconfig['default_data_dir'],
                                         self._exp_name, self._subject,
                                         self._session)

        if not os.path.exists(self._session_dir):
            os.makedirs(self._session_dir)

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
        filename will also incorporate a time-stamp and a number to disambiguate
        data files with the same title, extension, and time-stamp.  The filename
        is not a file path.  The filename will be distinct from all filenames
        previously returned from this method even if a file of that name has
        not yet been created in the log directory.

        Returns the new filename.
        """
        if use_timestamp:
            title = "%s_%s" % (title, time.strftime("%Y%m%d%H%M%S",
                                                    time.gmtime()))
        with self._reserved_data_filenames_lock:
            self._reserved_data_filenames |= set(os.listdir(self._session_dir))
            for distinguisher in xrange(256):
                if ext is None:
                    filename = "%s_%d" % (title, distinguisher)
                else:
                    filename = "%s_%d.%s" % (title, distinguisher, ext)
                if filename not in self._reserved_data_filenames:
                    self._reserved_data_filenames.add(filename)
                    return os.path.join(self._session_dir, filename)
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
        for dict_key, items in iter(self._state_loggers.items()):
            filename, logger = items
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
    def platform(self):
        return self._platform

    @property
    def exp_name(self):
        return self._exp_name

    @property
    def subject(self):
        return self._subject

    @property
    def session(self):
        return self._session

    @property
    def subject_dir(self):
        return self._subject_dir

    @property
    def session_dir(self):
        return self._session_dir

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
            from main import SmileApp
            self._app = SmileApp(self)
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
    #exp = Experiment(fullscreen=False, pyglet_vsync=False)
    #exp.run()
    pass
