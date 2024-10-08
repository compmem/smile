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
import platform as pf
import traceback
import sys

import weakref
import time
import threading
import pathlib

# kivy imports
from . import kivy_overrides
import kivy
import kivy.base
from kivy.utils import platform
import kivy.clock

# local imports
from .state import Serial, AutoFinalizeState, Wait
from .ref import Ref
from .clock import clock
from .log import LogWriter, log2csv
from .event import event_time
from .scale import scale
from . import version


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
        self._joybuttons_down = set()
        self._issued_joybutton_refs = weakref.WeakValueDictionary()
        self._joyaxis_value = dict()
        self._joyaxis_value_refs = dict()
        self._joyhat_value = dict()
        self._joyhat_value_refs = dict()

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

    def _is_joybutton_down(self, buttonid):
        return buttonid in self._joybuttons_down

    def _get_joybutton_ref(self, buttonid):
        try:
            return self._issued_joybutton_refs[buttonid]
        except KeyError:
            ref = Ref(self._is_joybutton_down, buttonid)
            self._issued_joybutton_refs[buttonid] = ref
            return ref

    def get_joyaxis_value(self, axisid):
        try:
            # try to pull from existing ref
            ref = self._joyaxis_value_refs[axisid]
        except KeyError:
            # no ref exists, so make it and try again
            self._set_joyaxis_value(axisid, 0.0)
            ref = self._joyaxis_value_refs[axisid]
        return ref

    def _set_joyaxis_value(self, axisid, value):
        # first set the value
        self._joyaxis_value[axisid] = value

        # make sure the ref exists
        try:
            self._joyaxis_value_refs[axisid].dep_changed()
        except KeyError:
            self._joyaxis_value_refs[axisid] = Ref.getitem(self._joyaxis_value, axisid)
            self._joyaxis_value_refs[axisid].dep_changed()

    def get_joyhat_value(self, hatid):
        try:
            # try to pull from existing ref
            ref = self._joyhat_value_refs[hatid]
        except KeyError:
            # no ref exists, so make it and try again
            self._set_joyhat_value(hatid, 0.0)
            ref = self._joyhat_value_refs[hatid]
        return ref

    def _set_joyhat_value(self, hatid, value):
        # first set the value
        self._joyhat_value[hatid] = value

        # make sure the ref exists
        try:
            self._joyhat_value_refs[hatid].dep_changed()
        except KeyError:
            self._joyhat_value_refs[hatid] = Ref.getitem(self._joyhat_value, hatid)
            self._joyhat_value_refs[hatid].dep_changed()

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
    screen size and frame-rate during experimental run
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
            Label(text=Ref(str, exp.SavedVariable), duration=1)
        exp.run()

    This example will set SavedVariable to 10, add the numbers 0 through 9 to
    it, and then end the experiment.  At the end, exp.SavedVariable will be
    equal to 55.

    """
    def __init__(self, fullscreen=None, scale_box=None, 
                 scale_up=False, scale_down=False,
                 background_color=None, name="SMILE", debug=False, Touch=None,
                 save_private_computer_info=False, data_dir=None,
                 working_dir=None,
                 local_crashlog=False, cmd_traceback=True, show_splash=True):

        self._sysinfo = {}
        self._sysinfo['DEFAULTDATADIR'] = kivy_overrides._get_config()['default_data_dir']
        if not (data_dir is None):
            if os.path.isdir(data_dir):
                self._sysinfo['DEFAULTDATADIR'] = data_dir
        self._working_dir = '.'
        # BGJNOTE: this needs to be automatic in the future, not passed in as a 
        # parameter
        if working_dir is not None and os.path.isdir(working_dir):
            self._working_dir = working_dir

        self._cmd_traceback = cmd_traceback
        self._local_crashlog = local_crashlog
        self._save_private_computer_info = save_private_computer_info
        self._platform = platform
        self._exp_name = name
        self._session = time.strftime("%Y%m%d_%H%M%S")
        self._debug = debug
        self._process_args()

        # handle fullscreen before Window is imported
        if fullscreen is not None:
            self._fullscreen = fullscreen

        # set scale box
        scale._set_scale_box(scale_box=scale_box,
                             scale_up=scale_up,
                             scale_down=scale_down)

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
        ss = Serial(name="EXPERIMENT BODY", parent=self)

        self._root_state.set_instantiation_context(self)
        self._parents = [self._root_state]

        # Adding a wait ensures the window is created and sized before
        # we try and place anything (this fixes the off-center splash)
        Wait(0.25, parent=ss)

        if Touch is None:
            Touch = (platform == "android") or (platform == "ios")

        if show_splash:
            from .startup import Splash
            Splash(Touch=Touch, parent=ss)

        if self._monitor:
            from .startup import ConfigWindow
            ConfigWindow(parent=ss)

        self._sysinfo_slog = os.path.join(self._session_dir,
                                          "sysinfo.slog")
        self._sysinfo.update(kivy_overrides._get_config())
        self._sysinfo.update({"fullscreen":self._fullscreen,
                              "data_time":self._session,
                              "debug":self._debug,
                              "background_color":self._background_color,
                              "scale_box":scale_box,
                              "scale_up":scale_up,
                              "scale_down":scale_down,
                              "expname":name,
                              "processor":pf.processor(),
                              "python_version":pf.python_version(),
                              "system":pf.system(),
                              "version":version.__version__,
                              "author":version.__author__,
                              "email":version.__email__,
                              "date_last_update":version.__date__,
                              "uname":pf.uname()}
                              )

        # place to save experimental variables
        self._vars = {}
        self.__issued_refs = weakref.WeakValueDictionary()

        self._reserved_data_filenames = set(os.listdir(os.path.join(self._session_dir)))
        self._reserved_data_filenames_lock = threading.Lock()
        self._state_loggers = {}

    def _change_smile_subj(self, subj_id):
        #kconfig = kivy_overrides._get_config()

        if subj_id is None:
           subj_id = ""
        elif subj_id.strip() == "":
            self._subject = "SUBJ0000"
        else:
            self._subject = subj_id.strip()

        self._subject_dir = os.path.join(self._sysinfo['DEFAULTDATADIR'],
                                         self._exp_name, self._subject)
        self._session_dir = os.path.join(self._sysinfo['DEFAULTDATADIR'],
                                         self._exp_name, self._subject,
                                         self._session)

        if not os.path.isdir(self._session_dir):
            os.makedirs(self._session_dir)

        os.rename(self._sysinfo_slog, os.path.join(self._session_dir,
                                                   "log_sysinfo_0.slog"))

        for dict_key, items in iter(self._state_loggers.items()):
            filename, logger = items
            logger.close()
            os.remove(filename)


        self._reserved_data_filenames = set(os.listdir(self._session_dir))
        self._reserved_data_filenames_lock = threading.Lock()
        self._state_loggers = {}
        self._root_state.begin_log()
        return self._subject_dir

    def clean_path(self, file_path):
        if os.path.exists(file_path):
            return os.path.relpath(file_path, start=self._working_dir)
        else:
            # NOTE: If your file_path doesn't exist, then it will just be
            # erased from the logs, and replaced with CLEANED.
            return "CLEANED"

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
        if len(self._vars) > 0:
            var_keys = list(self._vars.keys())
        else:
            var_keys = []
        return super(Experiment, self).__dir__() + var_keys

    def _process_args(self):
        # get args from kivy_overrides
        # and config variables from kivy
        args = kivy_overrides.args
        #kconfig = kivy_overrides._get_config()

        # set up the subject and subj dir
        self._subject = args.subject
        self._subject_dir = os.path.join(self._sysinfo['DEFAULTDATADIR'],
                                         self._exp_name, self._subject)

        self._session_dir = os.path.join(self._sysinfo['DEFAULTDATADIR'],
                                         self._exp_name, self._subject,
                                         self._session)

        if not os.path.exists(self._session_dir):
            os.makedirs(self._session_dir)

        if args.monitor:
            self._monitor = True
        else:
            self._monitor = None

        # check for fullscreen
        if args.fullscreen:
            self._fullscreen = False
        else:
            self._fullscreen = None

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
            for distinguisher in range(256):
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

    def _flush_state_loggers(self):
        # Fix this for py3
        for key in self._state_loggers.keys():
            self._state_loggers[key][1]._file.flush()
            os.fsync(self._state_loggers[key][1]._file)

    def _write_sysinfo(self, save_private=None, filename=None):
        if filename is None:
            filename = self._sysinfo_slog
        if save_private is None:
            save_private = self._save_private_computer_info
        logged_info = self._sysinfo.copy()
        if not save_private:
            logged_info.pop('uname')
            logged_info.pop('DEFAULTDATADIR')

        sysinfo_logger = LogWriter(filename=filename)
        sysinfo_logger.write_record(data=logged_info)
        sysinfo_logger.close()

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

            # we need to reset that window
            import kivy.core.window
            if kivy.core.window.Window.initialized == False:
                # we've shut the window down, so need a new one
                from kivy.core.window import core_select_lib, window_impl
                kivy.core.window.Window = core_select_lib('window',
                                                          window_impl,
                                                          True)

            # start up the app
            from .main import SmileApp
            self._app = SmileApp(self)

            # start up the app

            self._app.run()

        except:
            # clean up the logs
            self._root_state.end_log(self._csv)
            self.close_state_loggers(self._csv)

            exc_type, exc_value, exc_traceback = sys.exc_info()
            tra =  traceback.format_exception(exc_type, exc_value,
                                              exc_traceback)
            if self._local_crashlog:
                filename_crashlog = 'smile_crashlog_{}.log'.format(self.session)
                filename_smiletraceback = 'smile_traceback_{}.log'.format(self.session)
            else:
                filename_crashlog = os.path.join(self.session_dir, 'smile_crashlog.log')
                filename_smiletraceback = os.path.join(self.session_dir, 'smile_traceback.log')

            with open(filename_crashlog, 'w') as f:
                for t in tra:
                    f.write(t)
            if self._current_state is not None:
                if self._cmd_traceback:
                    self._current_state.print_traceback(to_file=None)
                else:
                    with open(filename_smiletraceback, 'w') as f:
                        self._current_state.print_traceback(to_file=f)

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
