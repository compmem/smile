#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from __future__ import print_function
from contextlib import contextmanager
from functools import partial
from types import GeneratorType
import copy
import inspect
import weakref
import os.path, os

import smile.kivy_overrides as kivy_overrides
import smile.ref as ref
from .ref import Ref, val, NotAvailable, NotAvailableError
#from utils import rindex, get_class_name
from .log import LogWriter, log2csv
from .clock import clock


class StateConstructionError(RuntimeError):
    """
    An error with constructing a SMILE state machine.
    """
    pass


class StateBuilder(object):
    """A Mixin class that gives States Ref-based attribute access for state
    machine construction.

    """
    def _clone(self, parent):
        """Return an inactive copy of this state builder as an instance of its
        state class with the specified parent.

        """
        # Make a shallow copy of self.
        state_class = type(self)._state_class
        new_clone = state_class.__new__(state_class, use_state_class=True)
        new_clone.__dict__.update(self.__dict__)

        # Delete the __most_recently_entered_clone attribute from the new clone
        # to avoid a chain of clones resulting in a memory leak.
        del new_clone.__dict__["_State__most_recently_entered_clone"]

        # Replace certain attributes with deep copies of themselves.
        for attr in self._deepcopy_attrs:
            setattr(new_clone, attr, copy.deepcopy(getattr(self, attr)))

        # Set the clone inactive.
        new_clone._active = False

        # Set the parent of the clone.
        new_clone._parent = parent

        # Prepare the Ref context for the clone.
        new_clone._ref_context = {self: new_clone}

        return new_clone

    def __getattr__(self, name):
        try:
            return self.get_attribute_ref(name)
        except NameError:
            return super(StateBuilder, self).__getattribute__(name)

    def __setattr__(self, name, value):
        # If this isn't an internal value (with a leading underscore), create
        # an attribute update state or raise an error...
        if name[0] != "_":
            try:
                state = self.attribute_update_state(name, value)
                state.override_instantiation_context()
                return
            except NotImplementedError:
                raise AttributeError("State does not support attribute setting!")

        # First, set the attribute value as normal.
        super(StateBuilder, self).__setattr__(name, value)

        # If the name has the prefix "_init_" create a corresponding internal
        # attribute without that prefix.  Set it to None for now.  At enter
        # time it will be set to that val of the "_init_" value (resolving any
        # Refs)...
        if name[:6] == "_init_":
            target_name = name[5:]
            self._refs_for_init_attrs[target_name] = value
            setattr(self, target_name, None)

    def __dir__(self):
        # get the default dir()
        lst = super(StateBuilder, self).__dir__()

        # return that plus the log attribute names
        return lst + self._log_attrs

class StateClass(type):
    """A metaclass for States that creates a StateBuilder class for each State
    class.
    """
    def __init__(cls, name, bases, dict_):
        super(StateClass, cls).__init__(name, bases, dict_)
        if StateBuilder not in bases:
            cls._builder_class = type(cls.__name__ + "Builder",
                                      (StateBuilder, cls),
                                      {"_state_class": cls})
    #def __new__(cls, *pargs, **kwargs):
    #    return super(StateClass, cls).__new__(cls, *pargs, **kwargs)


#class State(object):
#-- @FIX: python3 __metaclass__ changed
class State(object, metaclass=StateClass):
    """Base State object for the hierarchical state machine.

    This class contains all of the calls that are required of a state
    to run properly in experimental run time.  Functions like *enter*
    and *leave* are the staples of a **State**. These functions are
    called by the **Experiment** which then uses our own scheduler to
    set the start and end times of our **State**. Below is a list of
    parameters and logged attributes that all **State** subclasses
    have access to and use.

    Parameters
    ----------
    parent : ParentState
        The parent state that this state is contained within
    duration : float
        The duration you would like the state to last in seconds
    save_log : Boolean (False)
        If set to True, will save a .slog with all of the information
        from this state.
    name : string
        The unique name you give this state.
    blocking : boolean (True)
        If True, this state will prevent a **Parallel** state from ending. If
        False, this state will be canceled if its **ParallelParent** finishes
        running. Only relevant if within a **ParallelParent**.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state-specific log.

    instantiation_filename : string
        The file in which this state is instantiated.
    instantiation_lineno : int
        the line number that this particular state was instantiated.
    start_time : float
        The time the state was started in experimental runtime.
    end_time : float
        The time this state ended in experimental runtime.
    enter_time : float
        The time this state entered and started all of it's preprossessing in
        experimental runtime.
    leave_time : float
        Logged time that this state left, called callbacks, and ended processes
        in experimental runtime.
    finalize_time : float
        The time this state calls `finalize()`

    """

    # Apply the StateClass metaclass
    #__metaclass__ = StateClass
    def __new__(cls, *pargs, **kwargs):
        use_state_class = kwargs.pop("use_state_class", False)
        if use_state_class or issubclass(cls, StateBuilder):
            #@FIX: deleted *pargs, **kwargs
            return super(State, cls).__new__(cls)
        else:
            return cls._builder_class.__new__(cls._builder_class, *pargs, **kwargs)

    def __init__(self, parent=None, duration=None, save_log=True, name=None,
                 blocking=True):
        # Weak value dictionary to track Refs issued by this state.  Necessary
        # because those Refs need to be notified when their dependencies
        # change.  This is first so that __setattr__ will work.
        self.__dict__["_State__issued_refs"] = weakref.WeakValueDictionary()

        # If true, we write a log entry every time this state finalizes.
        self.__save_log = save_log

        # The custom name for this state.
        self._name = name

        # Whether or not this state blocks in the context of a Parallel parent.
        self._blocking = blocking

        # Dict of initial Ref values to evaluate at enter time
        self._refs_for_init_attrs = {}

        # This is a convenience argument for automatically setting the end time
        # relative to the start time.  If it evaluates to None, it has no
        # effect.
        self._init_duration = duration

        # Start and end time for the state.  Start time is set at enter time.
        # End time must be set before leave time.  End time will be set
        # automatically at enter time if a duration is provided.
        self._start_time = None
        self._end_time = None

        # Started and ended flags for the state.  These indicate whether the
        # user-facing effect of the state has begun and ended, respectively.
        # This is used to determine what should be done for cancellation.
        self._started = False
        self._ended = False

        # Record of enter time, leave time, and finalize time at and after the
        # most recent enter.
        self._enter_time = None
        self._leave_time = None
        self._finalize_time = None

        # This flag is set True at enter time and False at finalize time.  It
        # indicates that it is not safe to enter this instance for a new
        # execution of the state.  If the instance is active a new clone of the
        # state can be constructed and that one entered instead.
        self._active = False

        # This flag is set False at enter time and True at leave time.
        # It indicates that it is safe for subsequent states in a series to
        # enter.
        self._following_may_run = False

        # This indicates the correct indentation level for this state in trace
        # output.
        self.__depth = 0

        # This flag indicates that trace output should be generated.
        self.__tracing = False

        # Record which source file and line number this constructor was called
        # from.
        # Associate this state with the most recently instantiated Experiment.
        from .experiment import Experiment
        try:
            self._exp = Experiment._last_instance()
            self._debug = self._exp._debug
        except AttributeError:
            self._exp = None
            self._debug = False

        self._instantiation_filename = "Turn on Debug Mode for this information"
        self._instantiation_lineno = 0

        if self._debug:
            self.set_instantiation_context()

        # Determine the parent for this state...
        if parent is None:
            if self._exp is None:
                # If there is no explicit parent and no associated experiment,
                # set parent to None.
                self._parent = None
            else:
                # If there is not explicit parent, use the state at the top of
                # the associated experiment's parent stack.
                self._parent = self._exp._parents[-1]
        elif parent is self._exp:
            # If the associated experment is passed in as the parent, set this
            # state as the associated experiment's root state.
            # Needed to handle the Meanwhile and UntilDone at top of experiment
            self._parent = None
            self._exp._root_state = self
        else:
            self._parent = parent

        # Callbacks to call when the state finalizes.
        # Required for cleanup for Done states.
        self.__finalize_callbacks = []

        # Raise an error if we are non-blocking, but not the child of a
        # Parallel...
        # TODO: check this any time self._blocking is assigned!
        if not self._blocking and not isinstance(self._parent, Parallel):
            raise StateConstructionError(
                "A state which is not a child of a Parallel cannot be "
                "non-blocking.")

        # If this state has a parent, add this state to its parent's children.
        if self._parent:
            self._parent._children.append(self)

        # These are the names of attributes (minus leading underscores) which
        # will be logged at finalization time.  Subclasses should extend this
        # list to cause additional attributes to be logged.
        self._log_attrs = ['instantiation_filename', 'instantiation_lineno',
                           'name', 'start_time', 'end_time', 'enter_time',
                           'leave_time', 'finalize_time']

        # Concerning state cloning...

        # List of attributes that should be deep copied during cloning.
        # Subclasses should extend this list as needed.
        self._deepcopy_attrs = []

        # This will allows be the originally constructed state, even in cloned
        # copies.
        self.__original_state = self

        # This is only valid in the original state.  It is the most recent
        # clone of the state (which could be the original itself) to have been
        # entered.  This is used to seemlessly evaluate Refs to values from the
        # most recently started execution of a state.
        self.__most_recently_entered_clone = self

        # Initialize with empty Ref context.
        self._ref_context = {}

    def __repr__(self):
        """String representation.
        """
        # Include the class name, the instantiation filename and line number,
        # the custome name, and the object ID (in hex)...
        return "<%s file=%r, line=%d, name=%r, id=%x>" % (
            type(self).__name__,
            self._instantiation_filename,
            self._instantiation_lineno,
            self._name,
            id(self))

    def __reduce__(self):
        """Don't try to pickle state objects, just string repr."""
        # PBS: Ideally do this without str
        return (str, (self.__repr__(),))

    def __setattr__(self, name, value):
        # First, set the sttribute value as normal.
        super(State, self).__setattr__(name, value)

        # If the attribute is not named with a leading underscore, no further
        # action is taken...
        if name[0] != "_":
            return

        # If we've issued a Ref for this attribute, notify the Ref that its
        # dependencies have changed.
        try:
            ref = self.__issued_refs[name[1:]]
        except KeyError:
            return
        ref.dep_changed()

    def set_instantiation_context(self, obj=None):
        """Set this state's instantiation filename and line number to be the
        place where the supplied object was instantiated.
        """
        # If no object is provide as the source of the context, use self.
        if obj is None:
            obj = self

        # Find the highest frame on the call stack whose function is not an
        # "__init__" for a parent class

        mro = inspect.getmro(type(obj))
        for (frame, filename, lineno,
             fname, fcode, index) in inspect.stack()[1:]:
            if fname == "__init__" and type(frame.f_locals["self"]) in mro:
                continue

            # Record the filename and line number found.  This will be the
            # place where this state was instantiated by the user because it
            # excludes calls to constructors State subclasses.
            self._instantiation_filename = filename
            self._instantiation_lineno = lineno
            break
        else:
            raise StateConstructionError(
                "Can't figure out where instantiation took place!")


    def override_instantiation_context(self, depth=0):
        """Set this state's instantiation filename and line number to be the
        place where the calling function was called.
        """
        # Get the desired frame from the call stack.
        if self._debug:
            (frame,
             filename,
             lineno,
             function,
             code_context,
             index) = inspect.stack()[depth + 2]

            # Record the source filename and line number from the stack frame.
            self._instantiation_filename = filename
            self._instantiation_lineno = lineno

    def begin_log(self):
        """Prepare the per-class state logs.
        """
        if self.__save_log:
            # Use the state logger facily of the associated Experiment so that
            # only one state log is produced for the state class (rather than
            # one per instance).
            self._exp.setup_state_logger(type(self)._state_class.__name__)

    def end_log(self, to_csv=False):
        """Close the per-class state logs.
        """
        # The associated Experiment cleans up its own state loggers.
        pass

    def tron(self, depth=0):
        """Active trace output.
        """
        # set the tracing flag
        self.__tracing = True

        # set the tracing depth (indentation level)
        self.__depth = depth

    def troff(self):
        """Deactivate trace output.
        """
        # clear the tracing flag
        self.__tracing = False

    def print_trace_msg(self, msg):
        """Print a one line message as part of trace output.
        """
        # Create list of strings to identify this state (which will appear
        # comma-separated).  Name is included only if name is not None...
        id_strs = [
            "file: %r" % self._instantiation_filename,
            "line: %d" % self._instantiation_lineno
            ]
        if self._name is not None:
            id_strs.append("name: %s" % self._name)

        # Print the trace message.
        print("*** %s%s (%s): %s" %
              ("  " * self.__depth,
               type(self).__name__,
               ", ".join(id_strs),
               msg))

    def print_traceback(self, child=None, t=None):
        """Print a SMILE traceback on the console.
        """
        # Use the current time, if none is provided.
        if t is None:
            t = clock.now()
        if self._parent is None:
            # If we are the root of the state tree, print the header.
            print(" SMILE Traceback:")
        else:
            # Otherwise, let our parent print its traceback first.
            self._parent.print_traceback(self, t)

        # Get a string for the parenthesized state name, or an empty string if
        # the state has no custom name...
        if self._name is None:
            name_spec = ""
        else:
            name_spec = " (%s)" % self._name

        # Nested function to format time values as strings...
        def tstr(tm):
            if (isinstance(tm, dict) and
                len(tm) == 2 and
                "time" in tm and "error" in tm):
                if tm["error"] is None:
                    error = ""
                else:
                    error = ", error=%fs" % tm["error"]
                tm = tm["time"]
            else:
                error = ""
            if type(tm) not in (float, int):
                return repr(tm)
            offset = t - tm
            if offset < 0.0:  # TODO: display time relative to experiment start
                return "%fs from now%s" % (-offset, error)
            else:
                return "%fs ago%s" % (offset, error)

        # Print traceback state header.
        print("   %s%s - file: %s, line: %d" %
              (type(self).__name__,
               name_spec,
               self._instantiation_filename,
               self._instantiation_lineno))

        # Print out log attributes...
        for attr_name in self._log_attrs:
            try:
                value = val(getattr(self, "_" + attr_name))
            except NotAvailableError:
                value = NotAvailable
            if attr_name.endswith("_time"):
                print("     %s: %s" % (attr_name, tstr(value)))
            else:
                print("     %s: %r" % (attr_name, value))

    def claim_exceptions(self):
        # TODO: make this a context manager instead?
        # TODO: rename and change doc string
        # (used for finding current clone now too)
        """Until another state 'claims exceptions', any uncaught exception will
        be attributed to this state in the SMILE traceback.
        """
        if self._exp is not None:
            # Set self as "current_state" in associated Experiment.
            self._exp._current_state = self

    def get_log_fields(self):
        """Get the field names for the state log.

        Returns
        -------
        list
            A list of string attribute names from this state

        """
        return self._log_attrs

    @property
    def current_clone(self):  # TODO: new doc string!
        # if we are a clone, just return self
        if self.__original_state != self:
            # we must be a clone, so return self
            return self

        # otherwise look for the most recent clone of self
        ancestor = self._exp._current_state
        while ancestor is not None:
            try:
                # this should also find self if we're a clone
                return ancestor._ref_context[self.__original_state]
            except KeyError:
                ancestor = ancestor._parent

        raise RuntimeError("No current clone of %r found!" % self)

    @property
    def original_builder(self):
        return self.__original_state

    def get_current_attribute_value(self, name):
        """Get the value of an attribute from the current clone of this state.

        """
        # Return the named attribute from the current clone.
                #@FIX added if statement, if Ref
        if (type(name)) == tuple:
            for n in name:
                return getattr(self.current_clone, n)
        return getattr(self.current_clone, name)

    def get_attribute_ref(self, name):
        internal_name = "_" + name
        if internal_name not in self.__dict__:
            raise NameError
        try:
            # If we already issued such a Ref, return that preexisting Ref.
            return self.__issued_refs[name]
        except KeyError:
            # Otherwise, create the Ref, store it, and return it.
            ref = Ref(self.get_current_attribute_value, "_" + name,
                      _parent_state=self)
            self.__issued_refs[name] = ref
            return ref

    def attribute_update_state(self, name, value, index=None):
        """Produce a state that updates an attribute of this state.

        """
        raise NotImplementedError

    def _schedule_start(self):
        pass

    def _unschedule_start(self):
        pass

    def _schedule_end(self):
        pass

    def _unschedule_end(self):
        pass

    def _enter(self):
        """Custom method to call at enter time.  Optionally overridden in
        subclasses.

        """
        pass

    def enter(self, start_time):
        """This function is called by our back end.  It does everything
        that needs to be done before the state even starts.  The back end will
        work ahead and run *enter* well before the state needs to start.

        Parameters
        ----------
        start_time : float
            When the state will start, some time in the future.

        """
        # set trace
        self.claim_exceptions()

        # Clear finalize callbacks
        # We want a new list specific to this clone
        self.__finalize_callbacks = []

        # set the start time
        self._start_time = start_time

        # record the end time
        self._enter_time = clock.now()

        # Clear the started and ended flags
        self._started = False
        self._ended = False

        # the leave and finalize times start out as NotAvailable
        self._leave_time = NotAvailable
        self._finalize_time = NotAvailable

        # set self as the most recently entered clone of the original
        self.__original_state.__dict__[
            "_State__most_recently_entered_clone"] = self

        # say we're active
        self._active = True
        self._following_may_run = False

        if self._parent:
            # if we have a parent, notify parent that we entered
            clock.schedule(partial(self._parent.child_enter_callback, self))

        # if we don't have the exp reference, get it now
        if self._exp is None:
            from .experiment import Experiment
            self._exp = Experiment._last_instance()

        # evaluate the '_init_' Refs...
        for name, value in self._refs_for_init_attrs.items():
            try:
                #@FIX: added if statement to evaluate Ref immediately
                if (type(self._name) == Ref):
                    self._name=val(self._name)
                setattr(self, name, val(value))
            except NotAvailableError:
                raise NotAvailableError(
                    ("Attempting to use unavailable value (%r) "
                     "for attribute %r of %r.  Do you need to use a Done "
                     "state?") % (value, name, self))

        # propagate self to ancestors' ref contexts...
        ancestor = self._parent
        while ancestor is not None:
            ancestor._ref_context[self.__original_state] = self
            ancestor = ancestor._parent

        # apply the duration, if supplied...
        if self._duration is None:
            self._end_time = None
        else:
            self._end_time = self._start_time + self._duration

        # custom enter code
        self._enter()

        # schedule start
        self._schedule_start()

        # schedule end, if end time available
        if self._end_time is not None:
            self._schedule_end()

        if self.__tracing:
            # print trace line, if tracing...
            call_time = self._enter_time - self._exp._root_executor._start_time
            call_duration = clock.now() - self._enter_time
            start_time = (self._start_time -
                          self._exp._root_executor._start_time)
            self.print_trace_msg(
                "ENTER time=%fs, duration=%fs, start_time=%fs" %
                (call_time, call_duration, start_time))

    def _add_finalize_callback(self, func, *pargs, **kwargs):
        self.__finalize_callbacks.append((func, pargs, kwargs))

    def _leave(self):
        """Custom method to call at leave time.  Optionally overridden in
        subclasses.
        """
        pass

    def leave(self):
        """Allow subsequent states to enter.
        """
        # ignore leave call if not active
        if self._following_may_run or not self._active:
            return

        self.claim_exceptions()

        # record leave time
        self._leave_time = clock.now()

        # set following_may_run flag
        self._following_may_run = True

        if self._parent:
            # notify parent that we are leaving
            clock.schedule(partial(self._parent.child_leave_callback, self))

        # call custom leave code
        self._leave()

        if self.__tracing:
            # print trace line if tracing...
            call_time = self._leave_time - self._exp._root_executor._start_time
            call_duration = clock.now() - self._leave_time
            if self._end_time is None:
                 self.print_trace_msg(
                    "LEAVE time=%fs, duration=%fs, perpetual" %
                    (call_time, call_duration))
            else:
                end_time = (self._end_time -
                            self._exp._root_executor._start_time)
                self.print_trace_msg(
                    "LEAVE time=%fs, duration=%fs, end_time=%fs" %
                    (call_time, call_duration, end_time))

    def cancel(self, cancel_time):
        """Force the state to end (possibly prematurely) at a specified time.

        Parameters
        ----------
        cancel_time : float
            The time you want this state to end, regardless of if it has
            reached its end time.


        """
        if not self._active:
            return
        if not self._started and cancel_time < self._start_time:
            self._unschedule_start()
            if self._end_time is not None:
                self._unschedule_end()
            self._start_time = cancel_time
            self._end_time = cancel_time
            clock.schedule(self.leave)
            clock.schedule(self.finalize)
        elif not self._ended and self._end_time is None:
            self._end_time = cancel_time
            self._schedule_end()
        elif not self._ended and cancel_time < self._end_time:
            self._unschedule_end()
            self._end_time = cancel_time
            self._schedule_end()
        elif self._ended and cancel_time < self._end_time:
            # Oops!  We already ended.  Just revise the end time.
            self._end_time = cancel_time

        if self.__tracing:
            # print trace line if tracing...
            call_time = cancel_time - self._exp._root_executor._start_time
            call_duration = clock.now() - cancel_time
            if self._end_time is None:
                self.print_trace_msg(
                    "CANCEL time=%fs, duration=%fs, perpetual" %
                    (call_time, call_duration))
            else:
                end_time = (self._end_time -
                            self._exp._root_executor._start_time)
                self.print_trace_msg(
                    "CANCEL time=%fs, duration=%fs, end_time=%fs" %
                    (call_time, call_duration, end_time))

    def save_log(self):
        """Write a record to the state log for the current execution of the
        state.
        """
        self._exp.write_to_state_log(
            type(self).__name__,
            {name : getattr(self, "_" + name) for name in self._log_attrs})

    def finalize(self):  #TODO: call a _finalize method?
        """Deactivate the state and perform any state logging.
        """
        if not self._active:
            return

        self.claim_exceptions()

        self._finalize_time = clock.now()
        self._active = False
        if self.__save_log:
            self.save_log()
        if self._parent:
            clock.schedule(partial(self._parent.child_finalize_callback, self))
        for func, pargs, kwargs in self.__finalize_callbacks:
            clock.schedule(partial(func, *pargs, **kwargs))
        self.__finalize_callbacks = []
        if self.__tracing:
            call_time = (self._finalize_time -
                         self._exp._root_executor._start_time)
            call_duration = clock.now() - self._finalize_time
            self.print_trace_msg("FINALIZE time=%fs, duration=%fs" %
                                 (call_time, call_duration))


class AutoFinalizeState(State):
    """Base class for states that automatically finalize immediately after
    leaving.
    """
    def leave(self):
        super(AutoFinalizeState, self).leave()
        clock.schedule(self.finalize)


class ParentState(State):
    """Base state for parents that can hold other states as children.

    This base class has all of the methods for dealing with child states.  When
    leaving, it will tell all of its children to leave. When logging, it will
    tell all of its children to log as well.

    Parameters
        ----------
        children : list (None)
            A list containing any *States* that you wish to be the children of
            **ParentState**.
        parent : ParentState (None)
            The state that is the parent of this state. Defaults to whatever
            **ParentState** this state exists within.
        duration : float
            The duration you would like the state to last in seconds.
        save_log : boolean (False)
            If set to True, will save a .slog with all of the information
            from this state.
        name : string
            The unique name you give this state.
        blocking : boolean (True)
            If True, this state will prevent a **Parallel** state from ending.
            If False, this state will be canceled if its **ParallelParent**
            finishes running. Only relevant if within a **ParallelParent**.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state-specific log. Refer to State class
    docstring for additional logged parameters.

    """
    def __init__(self, children=None, parent=None, duration=None,
                 save_log=True, name=None, blocking=True):
        # keep track of references issued for user variables
        self.__dict__["_ParentState__issued_refs"] = \
            weakref.WeakValueDictionary()

        super(ParentState, self).__init__(parent=parent,
                                          duration=duration,
                                          save_log=save_log,
                                          name=name,
                                          blocking=blocking)

        # process children
        if children is None:
            children = []
        elif isinstance(children, State):
            children = [children]
        self._children = []
        for c in children:
            self.claim_child(c)

        # keep track of children that enter from this parent
        self.__unfinalized_children = set()

        # cancel time (None if not cancelled)
        self._cancel_time = None

    def get_attribute_ref(self, name):
        """Return a Ref for a user variable of this ParentState.
        """
        try:
            return super(ParentState, self).get_attribute_ref(name)
        except NameError:
            if "__" in name:
                raise NameError
            try:
                return self.__issued_refs[name]
            except KeyError:
                ref = Ref(self.get_var, name, _parent_state=self)
                self.__issued_refs[name] = ref
                return ref

    def attribute_update_state(self, name, value, index=None):
        state = ParentSet(self, name, value, index=index)
        return state

    def get_var(self, name):
        """Get a user variable of this ParentState.
        """
        return self.current_clone._vars[name]

    def set_var(self, name, value, index=None):
        """Set a user variable of this ParentState.
        """
        if index is None:
            self.current_clone._vars[name] = value
        else:
            # use the index
            self.current_clone._vars[name][index] = value

        try:
            ref = self.__issued_refs[name]
        except KeyError:
            return
        ref.dep_changed()

    def tron(self, depth=0):
        """Activate trace output for this state and all its children.

        Parameters
        ----------
        depth : integer (0)
            The print depth for trace output. If depth = 1, the Child's
            Child will be traced.

        """
        super(ParentState, self).tron(depth)
        child_depth = depth + 1
        for child in self._children:
            child.tron(child_depth)

    def troff(self):
        """Deactivate trace output for this state and all its children.
        """
        super(ParentState, self).troff()
        for child in self._children:
            child.troff()

    def begin_log(self):
        """Prepare per-class state logs for this state and all its children.
        """
        super(ParentState, self).begin_log()
        for child in self._children:
            #@FIX: added if else statement to check for Ref 
            #@FIX: might need to double check on the bound method check --> may need to change to Ref
            if ('LogBuilder' in str(type(child))) and ('bound method' in str(child)):
                pass
            else:
                child.begin_log()

    def end_log(self, to_csv=False):
        """Close per-class state logs for this state and all its children.
        """
        super(ParentState, self).end_log(to_csv)
        for child in self._children:
            child.end_log(to_csv)

    def claim_child(self, child):
        """Add a state to this state's list of children, removing it from any
        prior parent.
        """
        if child._parent is not None:
            child._parent._children.remove(child)
        child._parent = self
        self._children.append(child)

    def child_enter_callback(self, child):
        """Notify this state that one of its children has entered.
        """
        self.__unfinalized_children.add(child)
        if self._cancel_time is not None:
            child.cancel(self._cancel_time)

    def child_leave_callback(self, child):
        """Notify this state that one of its children has left.
        """
        pass

    def child_finalize_callback(self, child):
        """Notify this state that one of its children has finalized.
        """
        self.__unfinalized_children.discard(child)
        if self._following_may_run and not len(self.__unfinalized_children):
            # we have no more unfinalized children,
            # so this parent can finalize
            self.finalize()

    def _enter(self):
        self.__unfinalized_children = set()
        self.__cancel_time = None
        self._vars = {}

    def _leave(self):
        if not len(self._children) or not len(self.__unfinalized_children):
            clock.schedule(self.finalize)

    def __enter__(self):
        # push self as current parent
        if self._exp is not None:
            self._exp._parents.append(self)
        return self

    def __exit__(self, type, value, tb):
        # pop self off
        if self._exp is not None:
            state = self._exp._parents.pop()

    def cancel(self, cancel_time):
        """Force the state to end (possibly prematurely) at a specified time.

        Parameters
        ----------
        cancel_time : float
            The time you want this state to end, regardless of if it has
            reached its end time.

        """
        if not self._active:
            return
        for child in self.__unfinalized_children:
            child.cancel(cancel_time)
        if self._end_time is None or cancel_time < self._end_time:
            self._end_time = cancel_time
        self._cancel_time = cancel_time


class ParentSet(AutoFinalizeState):
    """State that sets a user attribute value on a ParentState.
    """
    def __init__(self, state, var_name, value, index=None, parent=None,
                 save_log=True, name=None):
        super(ParentSet, self).__init__(parent=parent,
                                        save_log=save_log,
                                        name=name,
                                        duration=0.0)
        self.__state = state
        self._state_name = state._name
        self._init_var_name = var_name
        self._init_value = value
        self._init_index = index

        self._log_attrs.extend(['state_name', 'var_name', 'value', 'index'])

    def _enter(self):
        self.__state.set_var(self._var_name, self._value, self._index)
        clock.schedule(self.leave)


class Parallel(ParentState):
    """A State used to run other States simultaneously.

    A **ParentState** that runs all of its children in parallel. A Parallel
    will not end until all of its children are finished running. The only
    exception to this rule is *blocking* parameter. By default, all states have
    *blocking* set to true, but if an experimenter sets *blocking* to False,
    then SMILE will ignore that state when deciding when to end a Parallel. If
    a Parallel state has 3 children, and one of them is non-blocking, then this
    Parallel will only end if the other two states have ended, regardless of
    what the non-blocking state is doing.

    If there are all *non-blocking* children in a Parallel, then the Parallel
    will end when any of its children have ended. This is mainly used in SMILE
    when an experimenter is waiting for one of multiple things to happen, like
    whether a key on the keyboard or a mouse button will be pushed first. Below
    is a short example depicting just that.

    Parallel has the unique ability to add in more children during Run Time.
    Putting a Paralle.insert call inside of a loop will create and add as many
    states as you want to an already preexisting Parallel. An example follows
    below where an experimenter wants to spawn some number of rectangles right
    next to each other. Below is a short example depicting just that.

    Parameters
    ----------
    children : list (None)
        A list containing any *States* that you wish to be the children of
        *ParentState*.
    parent : ParentState (None)
        The state that is the parent of this state. Defaults to whatever
        *ParentState* this state exists within.
    save_log : boolean (True)
        If set to True, will save a .slog with all of the information
        from this state.
    name : string
        The unique name you give this state.
    blocking : boolean (True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevant if within a *ParallelParent*.

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

        # This Parallel will end after 3s because the
        # 5s duration Label is non-blocking
        with Parallel():

            Label(text="I will remain here the longest!", duration=3)
            Label(text="My duration will be cut short.", duration=5,
                  center_x=exp.screen.center_x+200, blocking=False)
            Label(text="I will disappear first!", duration=2,
                  center_x=exp.screen.center_x-200)

        # This Parallel will end after either a mouse press occurs or a key
        # press occurs.
        with Parallel():
            mp = MousePress(blocking=False)
            kp = KeyPress(blocking=False)

        with Parallel() as par:
        # Loop.i is the is the number representing the ith iteration through
        # the loop.
        with Loop(10) as rec_loop:
            with par.insert():
                Rectangle(center_x=rec_loop.i*70, width=60, height=60,
                          duration=1)

        exp.run()


    """
    def __init__(self, children=None, parent=None, save_log=True, name=None,
                 blocking=True):
        super(Parallel, self).__init__(children=children,
                                       parent=parent,
                                       save_log=save_log,
                                       name=name,
                                       blocking=blocking)
        self.__my_children = []
        self.__blocking_children = []
        self.__remaining = set()
        self.__blocking_remaining = set()

    def print_traceback(self, child=None, t=None):
        super(Parallel, self).print_traceback(child, t)
        if child is not None:
            if child._blocking:
                print("     Blocking child...")
            else:
                print("     Non-blocking child...")

    def _enter(self):
        super(Parallel, self)._enter()
        # empty the children lists on enter
        self.__blocking_children = []
        self.__my_children = []
        self.__remaining = set()
        self.__blocking_remaining = set()
        if len(self._children):
            # process each child
            for child in self._children:
                self._insert_child(child, self._start_time)
        else:
            self._end_time = self._start_time
            clock.schedule(self.leave)

    def _insert_child(self, child, start_time):
        # clone the child
        child = child._clone(self)
        # add it to the list of running children
        self.__my_children.append(child)
        # if it's blocking append to the blocking children
        if child._blocking:
            self.__blocking_children.append(child)
            self.__blocking_remaining.add(child)
        # set of all non-run cloned children
        self.__remaining.add(child)
        # schedule the state to run
        clock.schedule(partial(child.enter, start_time))
        # return the child
        return child

    def insert(self, children=None, parent=None, save_log=True, name=None,
               blocking=True):
        return ParallelInsertState(self, children=children, parent=parent,
                                   save_log=save_log, name=name,
                                   blocking=blocking)

    def child_leave_callback(self, child):
        # called when any child leaves
        super(Parallel, self).child_leave_callback(child)

        # remove the child from remaining
        self.__remaining.discard(child)
        if len(self.__blocking_remaining):
            # remove that child if it's in the blocking list
            self.__blocking_remaining.discard(child)
            if not len(self.__blocking_remaining):
                # there are none still blocking
                self._set_end_time()
                if self._end_time is not None:
                    # we have an end time, so cancel
                    self.cancel(self._end_time)
        elif not len(self.__blocking_children):
            # there are no blocking children, so end on first
            # get the time from this first complete child
            self._end_time = child._end_time
            if self._end_time is not None:
                # we have an end time, so cancel
                self.cancel(self._end_time)

        if not len(self.__remaining):
            # there are no more children to finish, so leave
            self.leave()

    def _set_end_time(self):
        # check all end times for each blocking child
        end_times = [c._end_time for c in self.__blocking_children]
        if any([et is None for et in end_times]):
            # if any are None, then no end time
            self._end_time = None
        else:
            # otherwise, set to max end time
            self._end_time = max(end_times)


class ParallelInsertState(ParentState):
    def __init__(self, parallel_state, children=None, parent=None,
                 save_log=True, name=None, blocking=True):
        super(ParallelInsertState, self).__init__(children=children,
                                                  parent=parent,
                                                  save_log=save_log,
                                                  name=name,
                                                  blocking=blocking)
        self.__parallel_state = parallel_state
        self._inserted = []

    def _enter(self):
        super(ParallelInsertState, self)._enter()
        parallel_state = self.__parallel_state.current_clone
        self._inserted = []
        for child in self._children:
            self._inserted.append(StateHandle(
                parallel_state._insert_child(child, self._start_time)))
        self._end_time = self._start_time
        clock.schedule(self.leave)

    @property
    def first(self):
        return self.inserted[0]

    @property
    def last(self):
        return self.inserted[-1]


class StateHandle(object):
    def __init__(self, state):
        self.__state = state

    def __getattr__(self, name):
        try:
            return self.__state.get_attribute_ref(name)
        except NameError:
            # PBS: I doubt this code will ever get hit
            try:
                return getattr(self.__state, name)
            except AttributeError:
                try:
                    return getattr(self.__state, "_" + name)
                except AttributeError:
                    raise AttributeError(name)


@contextmanager
def _ParallelWithPrevious(name=None, parallel_name=None, blocking=True):
    """States added in this context will be added to a Serial which is in
    Parallel with the state preceding this call.

    """
    # get the exp reference
    from .experiment import Experiment
    try:
        exp = Experiment._last_instance()
    except AttributeError:
        raise StateConstructionError(
            "You must first instantiate an Experiment.")

    # find the parent
    parent = exp._parents[-1]

    # find the previous child state (-1 because this is not a state)
    try:
        prev_state = parent._children[-1]
        parallel_parent = parent
    except IndexError:
        prev_state = parent
        if parent._parent is None:
            parallel_parent = parent._exp
        else:
            parallel_parent = parent._parent

    # build the new Parallel state
    with Parallel(name=parallel_name, parent=parallel_parent,
                  blocking=blocking) as p:
        p.override_instantiation_context(3)
        p.claim_child(prev_state)
        with Serial(name=name) as s:
            s.override_instantiation_context(3)
            yield p


@contextmanager
def Meanwhile(name=None, blocking=True):
    """A context State used to run its children until a previous state is finished

    States created in this context will run in serial during the execution
    of the previous state, but will be canceled when the previous state ends.
    If there is no previous state in the current parent, this will apply to the
    parent in lieu of the previous state.

    Example
    -------

    ::

        Wait(3)
        with Meanwhile():
            Label(text='On the screen for 3 seconds, the Wait's Duration')

    This Example will display the *Label* for as long as the state previous to
    the `Meanwhile()` is running. In this case, the duration of the *Meanwhile*
    is the same as the duration of the *Wait*. The moment the *Wait* finishes,
    the *Label* will disappear from the screen.

    Under the hood, this state is creating a ParallelWithPrevious state. Then,
    it sets the previous state as blocking and the rest of the states are set
    to non-blocking.

    """
    with _ParallelWithPrevious(name=name, parallel_name="MEANWHILE",
                               blocking=blocking) as p:
        yield p
    # set the new serial as non-blocking
    p._children[1]._blocking = False


@contextmanager
def UntilDone(name=None, blocking=True):
    """A context state used to run a previous state till its children are finished

    States created in this context will run in serial during the execution
    of the previous state, and the previous state will be canceled when the
    states in the context end.  If there is no previous state, this will apply
    to the parent in lieu of the previous state.

    Example
    -------

    ::

        Label(text='On the screen for 6 seconds, the 2 Waits' duration')
        with UntilDone():
            Wait(3)
            Wait(3)

    In this example, the *Label* will display for 6 seconds, which is the time
    that it takes for both *Wait* states to finish running. The moment that the
    last *Wait* state ends, the *Label* will be canceled and disappear from the
    screen.

    Under the hood, this state is creating a ParallelWithPrevious state. Then,
    it sets the previous state as non-blocking and the rest of the states are
    set to blocking.

    """
    with _ParallelWithPrevious(name=name, parallel_name="UNTILDONE",
                               blocking=blocking) as p:
        yield p
    # set the previous state as non-blocking
    p._children[0]._blocking = False


class SequentialState(ParentState):
    """Base state for parents that run a sequence of child states back to back.

    This state takes children, like the Parent state, but on *enter* it clones
    all of the children and schedules them in the correct sequential order.

    """
    def __init__(self, children=None, parent=None, save_log=True, name=None,
                 blocking=True):
        super(SequentialState, self).__init__(children=children,
                                              parent=parent,
                                              save_log=save_log,
                                              name=name,
                                              blocking=blocking)

    def _enter(self):
        super(SequentialState, self)._enter()
        self.__child_iterator = self._get_child_iterator()
        self.__current_child = None
        try:
            # clone the children as they come, so just clone the first
            self.__current_child = (
                #-- @FIX: python3 .next() changed
                #self.__child_iterator.next()._clone(self))
                next(self.__child_iterator)._clone(self))
            # schedule the child based on the current start time
            clock.schedule(partial(self.__current_child.enter,
                                   self._start_time))
        except StopIteration:
            # if there are no children, we're done and can leave
            self._end_time = self._start_time
            clock.schedule(self.leave)

    def _get_child_iterator(self):
        raise NotImplementedError

    def child_leave_callback(self, child):
        # gets called anytime a child leaves
        super(SequentialState, self).child_leave_callback(child)
        # get the time for the next state based on the end_time of the
        # current child
        next_time = self.__current_child._end_time
        if next_time is None:
            # no need to schedule the next b/c there is no end time
            # for the previous state, so we can leave
            self.leave()
        elif (self._cancel_time is not None and
              next_time >= self._cancel_time):
            # if there is a cancel time and the next is going to be after
            # the cancel, then just use the cancel time
            self._end_time = self._cancel_time
            self.leave()
        else:
            try:
                # clone the next child and schedule it
                self.__current_child = (
                    #-- @FIX: Python3 .next() changed
                    #self.__child_iterator.next()._clone(self))
                    next(self.__child_iterator)._clone(self))
                clock.schedule(partial(self.__current_child.enter, next_time))
            except StopIteration:
                # there are no more children, so set our end time and leave
                self._end_time = next_time
                clock.schedule(self.leave)


class Serial(SequentialState):
    """*ParentState* that runs its children in serial, one after another.

    This is a state used to section off states to be run in serial.  Usually,
    it is only used while using another state, like *Parallel* or *UntilDone*,
    but *Experiment* puts all states in a long *Serial* state by default.

    Parameters
    ----------
    children : list (None)
        A list containing any *States* that you wish to be the children of
        *ParentState*
    parent : ParentState (None)
        The state that is the parent of this state. Defaults to whatever
        *ParentState* this state exists within.
    save_log : boolean (True)
        If set to True, will save a .slog with all of the information from this
        state.
    name : string
        The unique name you give this state.
    blocking : boolean (True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevant if within a *ParallelParent*.

    Logged Attributes
    -----------------
    All parameters above are available to be accessed and manipulated within
    the experiment code, and will be automatically recorded in the
    state-specific log. Refer to State class docstring for additional logged
    parameters.

    Example
    -------

    The default state that an experiment is in is a Serial state.  That means
    that the following two examples are equal and will run exactly the same.

    ::

        exp = Experiment()

        Label(text='Hello,', duration=1)
        Label(text='Hello, W', duration=1)
        Label(text='Hello, World', duration=1)

        exp.run()

    ::

        exp = Experiment()

        with Serial():
            Label(text='Hello,', duration=1)
            Label(text='Hello, W', duration=1)
            Label(text='Hello, World', duration=1)

        exp.run()

    These examples will display 3 labels in serial and then the experiment will
    end.

    Another example that would be helpful is to use Serial within a **Parallel**
    state.  Say you want 2 sequences of states to run at the same time. The
    easiest way to accomplish this is to use 2 Serial states within a Parallel
    state.

    ::

        exp = Experiment()

        with Parallel():
            with Serial():
                Label(text='Im on the Left!', duration=2,
                      center_x=exp.screen.center_x-400)
                Wait(2)
                Label(text='Now Im on the Left again!!!', duration=2,
                      center_x=exp.screen.center_x-400)

            with Serial():
                Wait(2)
                Label(text='Now Im on the Right!', duration=2,
                      center_x=exp.screen.center_x+400)
                Wait(2)
                Label(text='Now Im on the Right again!!!', duration=2,
                      center_x=exp.screen.center_x400)

        exp.run()

    This example will take turns displaying Labels on either side of the
    screen. In reality it each Serial state will run at the same time, but to
    the eye it will look like they are taking turns.

    """
    def _get_child_iterator(self):
        return iter(self._children)


class Subroutine(object):
    """A Subroutine is a decorator for making reusable bits of state-machine.

    A decorator for functions that build reusable, encapsulated portions of
    state machine. You can pass in any number of keywords and keyword arguments
    when defining your own **Subroutine**. The first argument you need to pass
    into your **Subroutine** when defining it is always **self**.

    Example
    -------

    ::

        @Subroutine
        def Example_Subroutine(self,
                               num_loop=10,
                               input=0,
                               mult=2):

            self.mult_temp = input
            with Loop(num_loop):
                Label(text=self.mult_temp, duration=3)
                self.mult_temp = self.mult_temp*mult

    This will create a **Subroutine** that your experiment can call. The
    **Subroutine** will then run during experimental runtime just like any other
    state. The call would look something like what follows.

    ::

        Example_Subroutine(num_loop=15, input=200, mult=7)

    And just like that, the Example_Subroutine is added to the **ParentState's**
    children.
    """
    def __init__(self, func):
        self._func = func
        self.__doc__ = func.__doc__

    def __call__(self, *pargs, **kwargs):
        with SubroutineState(subroutine=self._func.__name__,
                             parent=kwargs.pop("parent", None),
                             save_log=kwargs.pop("save_log", True),
                             name=kwargs.pop("name", None),
                             blocking=kwargs.pop("blocking", True)) as state:
            retval = self._func(state, *pargs, **kwargs)
            if retval is None:
                result = state
            elif isinstance(retval, GeneratorType):
                @contextmanager
                def context():
                    with state:
                        with contextmanager(lambda : retval)():
                            yield state
                result = context()
            else:
                raise ValueError(
                    "Invalid return value from Subroutine function: %r" %
                    retval)
        state.override_instantiation_context()
        return result


class SubroutineState(Serial):
    """Serial-like state at the top-level of a deployment of a Subroutine.

    """
    def __init__(self, subroutine, parent=None, save_log=True, name=None,
                 blocking=True):
        super(SubroutineState, self).__init__(parent=parent,
                                              save_log=save_log,
                                              name=name,
                                              blocking=blocking)
        self._subroutine = subroutine

        self._log_attrs.extend(['subroutine'])


class If(SequentialState):
    """The way you do branching paths in a state machine.

    Parent state to implement conditional branching. **If** state is
    used in lieu of a traditional Python if statement. The SMILE
    **If** state will create a position linked list of *conditionals*
    and *states*.  It will then loop through the conditions, and when
    it finds a conditional that evaluates to True, it runs the
    corresponding state. The last *conditional* in the list is always
    a True boolean, which then corresponds to an **Else** state that
    you can define in your experiment.

    Under the hood, the If state will create 2 Serial states when it
    initializes. During experimental run time, it decides which state
    to actually run. If the next state is an Elif state then it will
    add itself to the possible states to run of the If state. If the
    next state is an Else state, then it will overwrite the Serial
    Else state that the If state creates at initialization.

    Parameters
    ----------
    conditional : logical
        You may only use logical operators in this conditional statement,
        that means you may not use **and** or **or**. You must use *&* and
        *|* in order to do **and** and **or** respectively.
    true_state : ParentState (optional)
        If given a ParentState, and the conditional is evaluated to be
        True, then the given state will run. If a true_state is not
        defined, it will be created as a *Serial* state with this state's
        children.
    false_state : ParentState (optional)
        If given a ParentState, and the conditional is evaluated to be
        False, then the given state will run. If a false_state is not
        defined, it will be created as a *Serial* state that will do
        Nothing.
    parent : ParentState (optional)
        The parent to this state.
    save_log : boolean (optional, defaults = True)
        If True, this state will save all of its information into a .slog
        file.
    name : string (optional)
        The unique name of this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevant if within a *ParallelParent*.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and
    manipulated within the experiment code, and will be automatically
    recorded in the state-specific log. Refer to State class
    docstring for additional logged parameters.

    outcome_index : integer
        The index pointing to which condition evaluated to True. Where 0 is the
        *If* conditional and n, the max number it could be, means none of the
        conditionals evaluated to true and it is running the *Else* state.

    Example
    -------

    ::

        with If(trial.current['condition1'] == 0 &
                trial.current['condition2'] == 2):
            Label(text=trial.current['stim'],
                  color=trial.current['color1'], duration=3)
        with Elif(trial.current['condition1'] == 1 &
                  trial.current['condition2'] == 0):
            Label(text=trial.current['stim'],
                  color=trial.current['color2'], duration=3)
        with Elif(trial.current['condition1'] == 1 &
                  trial.current['condition2'] == 0):
            Label(text=trial.current['stim'],
                  color=trial.current['color3'], duration=3)
        with Else():
            Label(text='No conditionals were true!', color='RED', duration=3)

    When we call `with Elif():` we are adding to the *If* state's internal list
    of **conditionals** and **states**. When you call `with Else():` you are
    adding to the children of the default **false_state**, which only runs if
    all the other conditionals evaluate to *False*.

    """
    def __init__(self, conditional, true_state=None, false_state=None,
                 parent=None, save_log=True, name=None, blocking=True):

        # init the parent class
        super(If, self).__init__(parent=parent, save_log=save_log, name=name,
                                 blocking=blocking)

        # save a list of conds to be evaluated (last one always True,
        # acts as the Else)
        self._init_cond = [conditional, True]
        self._outcome_index = None
        self.__true_state = true_state
        self.__false_state = false_state

        if self.__true_state:
            # make sure to set this as the parent of the true state
            self.claim_child(self.__true_state)
        else:
            # create the true state
            self.__true_state = Serial(parent=self, name="IF BODY")
            self.__true_state._instantiation_filename = self._instantiation_filename
            self.__true_state._instantiation_lineno = self._instantiation_lineno

        # process the false state similarly
        if self.__false_state:
            self.claim_child(self.__false_state)
        else:
            # create the false state
            self.__false_state = Serial(parent=self, name="DO NOTHING")
            self.__false_state._instantiation_filename = self._instantiation_filename
            self.__false_state._instantiation_lineno = self._instantiation_lineno

        # save the out_states
        self._out_states = [self.__true_state, self.__false_state]

        # append outcome to log
        self._log_attrs.append('outcome_index')

    def _get_child_iterator(self):
        # evaluate each cond with Python if for consistency
        cond_bool = [True if x else False for x in self._cond]
        self._outcome_index = cond_bool.index(True)
        yield self._out_states[self._outcome_index]

    def __enter__(self):
        # push self.__true_state as current parent
        if self._exp is not None:
            self._exp._parents.append(self.__true_state)
        return self


class Elif(Serial):
    """State to attach an elif to and **If** state. See **If**
    """
    def __init__(self, conditional, parent=None, save_log=True, name=None,
                 blocking=True):
        # init the parent class
        super(Elif, self).__init__(parent=parent, save_log=save_log, name=name,
                                   blocking=blocking)

        # we now know our parent, so ensure the previous child is
        # either and If or Elif state
        if self._parent is None:
            raise StateConstructionError("The parent of Elif can not be None.")

        # grab the previous child (-2 because we are -1)
        try:
            prev_state = self._parent._children[-2]
        except IndexError:
            raise StateConstructionError("No previous state for Elif.")
        if not isinstance(prev_state, If):
            raise StateConstructionError(
                "The previous state must be an If or Elif state.")

        # have that previous If state grab this one
        prev_state.claim_child(self)

        # insert the conditional and state
        prev_state._init_cond.insert(-1, conditional)
        prev_state._out_states.insert(-1, self)


def Else(name="ELSE BODY"):
    """Returns the else clause of the preceding If state. See *If*
    """
    # get the exp reference
    from .experiment import Experiment
    try:
        exp = Experiment._last_instance()
    except AttributeError:
        raise StateConstructionError(
            "You must first instantiate an Experiment.")

    # find the parent
    parent = exp._parents[-1]

    # find the previous child state (-1 because this is not a state)
    try:
        prev_state = parent._children[-1]
    except IndexError:
        raise StateConstructionError("No previous state for Else.")

    # make sure it's the If
    if not isinstance(prev_state, If):
        raise StateConstructionError(
            "The previous state must be an If or Elif state.")

    # return the false_state (the last out_state)
    false_state = prev_state._out_states[-1]
    false_state._name = name
    false_state.override_instantiation_context()
    return false_state


class Loop(SequentialState):
    """Repeat section of state-machine.

    A *Loop* can be setup to run like the python **for**, **while**, or
    **do while** depending on what parameters you send into it.


    Parameters
    ----------
    iterable : iterable (default = None, optional)
        This is any iterable class. i.e. List, Seq, String, Tuple.  If this
        variable is set, then it will be looped over. *iterable* can also
        be an integer. If so, the *Loop* will loop a set number of times.
    shuffle : Boolean (default = False, optional)
        If shuffle is set to True, then your passed in iterable will be
        shuffled before it is presented.
    conditional : Boolean (default = True, optional)
        At the beginning of each iteration of the loop, it checks that
        conditional evaluates to true. In conjunction with an iterable, it
        will end early if the conditional every evaluates to False. Without
        an iterable, the loop will function as a while loop.
    parent : ParentState (optional)
        The parent to this state.
    save_log : boolean (optional, defaults = True)
        If True, this state will save all of its information into a .slog
        file.
    name : string (optional)
        The unique name of this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevant if within a *ParallelParent*.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and manipulated
    within the experiment code, and will be automatically recorded in the
    state-specific log. Refer to State class docstring for additional logged
    parameters.

    i : integer
        The index of the currect iterable.  If **iterable** was given an
        integer, then *i* will
        be the loop number in experimental run time.
    current : Ref
        A reference to the current iteration of the looping variable in
        experimental run time.
    outcome : boolean
        A reference to the current iteration of the loop, telling the user what
        the conditional evaluated out to be, True or False.

    Example
    -------
    the command most used with *Loop* is `with Loop(trials) as trial:`. This
    will loop over the list **trials**.  You are able to access the current
    iteration of the loop by accessing the attribute `trial.current`. The
    following is an example that loops over a list of dictionaries and presents
    the name of a person and their favorite food.

    ::

        words = [{'name':'bob',    'food':'pringle'},
                 {'name':'tom',    'food':'prune'},
                 {'name':'paul',   'food':'potato'},
                 {'name':'chelsea','food':'dooughnut'},
                 {'name':'dinese', 'food':'corn'},
                 {'name':'emily',  'food':'pizza'}]

        with Loop(words) as trial:

            with Parallel():
                Label(text=trial.current['name'], duration=3,
                      center_x=exp.screen.center_x/2)
                Label(text=trial.current['food'], duration=3,
                      center_x=exp.screen.center_x*3/2)

    The following is an example on how to loop X number of times. To access
    what the current iteration number is, you must call `trial.i`.

    ::

        X = 15
        with Loop(X) as trial:
            Label(text=trial.i, duration=1)

    The following is an example of a **while** kind of *Loop*. All you have to
    do is set the conditional.

    ::

        exp.X = 15
        with Loop(conditional = exp.X < 20):
            Label(text=exp.X, duration=3)
            exp.X += 1

    """
    def __init__(self, iterable=None, shuffle=False, conditional=True,
                 parent=None, save_log=True, name=None, blocking=True):
        super(Loop, self).__init__(parent=parent, save_log=save_log, name=name,
                                   blocking=blocking)

        if shuffle:
            self._init_iterable = ref.shuffle(iterable)
        else:
            self._init_iterable = iterable
        self._cond = conditional
        self._outcome = True

        self._i = NotAvailable
        self._current = NotAvailable

        self.__body_state = Serial(parent=self, name="LOOP BODY")
        self.__body_state._instantiation_filename = self._instantiation_filename
        self.__body_state._instantiation_lineno = self._instantiation_lineno
        self.__current_child = None
        self.__cancel_time = None

        self._log_attrs.extend(['outcome', 'i', 'current'])

    def iter_i(self):
        """Generate successive values of i for this loop, setting 'outcome'
        value as appropriate.
        """
        self._outcome = val(self._cond)
        if self._iterable is None:
            i = 0
            while self._outcome:
                yield i
                i += 1
                self._outcome = val(self._cond)
        else:
            if not self._outcome:
                return

            if isinstance(self._iterable, int):
                count = self._iterable
            else:
                count = len(self._iterable)

            #--@FIX: xrange to range --
            for i in range(count):
                yield i

    def _get_child_iterator(self):
        self._outcome = NotAvailable
        for i in self.iter_i():
            self._i = i
            if self._iterable is None or isinstance(self._iterable, int):
                self._current = i
            else:
                self._current = self._iterable[i]
            yield self.__body_state

    def __enter__(self):
        # push self.__body_state as current parent
        if self._exp is not None:
            self._exp._parents.append(self.__body_state)
        return self


class Record(State):
    """A **Record** records any changes in passed in Refs.

    A **Record** state is something you can use to record the changes in a
    **Reference** variable.  See **Ref**. If any of the Reference objects
    changed, it will record all of them to a .slog file. Pass in Reference
    arguments by using keyword argument.

    Parameters
        ----------
        duration : float (optional)
            The duration of the state in seconds, if no duration is set, it
            will last until canceled.
        parent : ParentState (optional)
            The state you would like this state to be a child of. If not set,
            the *Experiment* will make it a child of a ParentState or the
            Experiment automatically.
        name : string (optional)
            The unique name of this state.
        blocking : boolean (optional, default = True)
            If True, this state will prevent a *Parallel* state from ending. If
            False, this state will be canceled if its Parallel Parent finishes
            running. Only relevant if within a *Parallel* Parent.
        triggers : list
            List of strings matching key word arg names to trigger on. This
            makes it possible to only save out all values when a certain set
            of references change values
        kwargs : (keyword = parameter)
            This is where you add what variables to check to see if they
            change. Give *Record* a parameter name and then make that equal to
            a Ref variable. An example is below. You may ask *Record* to check
            as many *Ref* variables as you would like.

    Example
    -------
    This is an example of a *Record* used in parallel with Video to track the
    flip time for each frame.

    ::

        with Parallel():
            vd = Video(source='test_video.mp4')
            Record(name='flips', blocking=False,
                   flip_time=exp.screen.last_flip['time'])


    """
    def __init__(self, duration=None, parent=None, name=None, blocking=True,
                 triggers=None, **kwargs):
        super(Record, self).__init__(parent=parent,
                                     duration=duration,
                                     save_log=False,
                                     name=name,
                                     blocking=blocking)

        self.__refs = kwargs
        self.__triggers = triggers
        #@FIX: changed "none" to "None"
        self.__log_filename = None
        self.__log_writer = None

    def begin_log(self):
        """Set up per-class AND per-instance logs.
        """
        super(Record, self).begin_log()
        if self._name is None:
            title = "record_%s_%d" % (
                os.path.splitext(
                    os.path.basename(self._instantiation_filename))[0],
                self._instantiation_lineno)
        else:
            title = "record_%s" % self._name

        if self.__log_filename is not None:
            os.remove(self.__log_filename)
        self.__log_filename = self._exp.reserve_data_filename(title, "slog")

        if self.__log_writer is not None:
            self.__log_writer.close()
        self.__log_writer = LogWriter(self.__log_filename)

    def end_log(self, to_csv=False):
        """Close logs.
        """
        super(Record, self).end_log(to_csv)
        if self.__log_writer is not None:
            self.__log_writer.close()
            self.__log_writer = None
            if to_csv:
                csv_filename = (os.path.splitext(self.__log_filename)[0] +
                                ".csv")
                log2csv(self.__log_filename, csv_filename)

    def _schedule_start(self):
        clock.schedule(self.leave, event_time=self._start_time)

    def _schedule_end(self):
        clock.schedule(self.finalize, event_time=self._end_time)

    def _unschedule_start(self):
        clock.unschedule(self.leave)

    def _unschedule_end(self):
        clock.unschedule(self.finalize)

    def _leave(self):
        # starts at leave time
        self._started = True

        # starts recording changes for each ref
        for name, ref in self.__refs.items():
            # only add in refs that trigger
            if self.__triggers and name not in self.__triggers:
                continue

            # start changing anytime it changes
            if hasattr(ref, 'add_change_callback'):
                ref.add_change_callback(self.record_change)

        # get current value
        self.record_change()

    def finalize(self):
        # ends at finalize time
        self._ended = True

        # we're done
        super(Record, self).finalize()

        # stop tracking changes for each ref
        for name, ref in self.__refs.items():
            # only stop refs that trigger
            if self.__triggers and name not in self.__triggers:
                continue

            # must be a ref to stop callbacks
            if hasattr(ref, 'remove_change_callback'):
                ref.remove_change_callback(self.record_change)

    def record_change(self):
        """Record a change in the track Refs.
        """
        # if anything (or just triggers) changed, write everything
        try:
            record = val(self.__refs)
        except NotAvailableError:
            raise NotAvailableError(
                "One or more recorded values not available!")
        record["record_time"] = self._exp._app.event_time
        self.__log_writer.write_record(record)


class Log(AutoFinalizeState):
    """Used to log any variables during experimental run time.

    A *Log* state is used to log any number of variables that you want to
    record to a .slog file.  Where ever it appears in your experiment, it will
    save out the values of all of the arguments you give it at that point in
    your experiment.  Each call to *Log* will save to a separate file. If used
    within a *Loop* state, it will write a row to the .slog for each iteration
    of the loop.

    Parameters
    ----------
    log_dict : dictionary (optional)
        Use case for this parameter is to pass in `trial.current`, as long
        as `trial.current` is a dictionary. This will save out all of the
        values of the the current iteration of your looping variable into
        different columns, like `log_dict_stim, log_dict_duration`.
    parent : ParentState (optional)
        The state you would like this state to be a child of. If not set,
        the *Experiment* will make it a child of a ParentState or the
        Experiment automatically.
    name : string (optional)
        The unique name of this state
    kwargs : (keyword = argument)
        As many arguments as you would like to pass in. Use the format
        `keyword = variable_name` and *Log* will log the value of
        **variable_name** into a column called **keyword**.

    Example
    -------
    This is an example of using *Log* in a *Loop*. Refer to the individual
    state's Doc Strings if something doesn't make sense, because this example
    brings a lot of different ideas together.

    ::

        from smile.common import *

        exp = Experiment()

        words = [{'name':'bob',    'food':'pringle'},
                 {'name':'tom',    'food':'prune'},
                 {'name':'paul',   'food':'potato'},
                 {'name':'chelsea','food':'dooughnut'},
                 {'name':'dinese', 'food':'corn'},
                 {'name':'emily',  'food':'pizza'}]

        with Loop(words) as trial:
            with Parallel():
                Label(text=trial.current['name'],
                      center_x=exp.screen.center_x/2)
                Label(text=trial.current['food'],
                      center_x=exp.screen.center_x*3/2)
                Label(text='Press J if the person should like the food,
                            Press K if the person shouldn't like the food.',
                      center_y=exp.screen.center_y/2)
            with UntilDone():
                kp = KeyPress(keys=['F', 'J'], duration=3)
            Log(trial.current,
                key_reaction_time=kp.rt
                key_pressed=kp.pressed)

        exp.run()

    This example will save out 4 columns to a .slog, **log_dict_name**,
    **log_dict_food**, **key_reaction_time**, and **key_pressed**.

    """
    def __init__(self, log_dict=None, parent=None, name=None, **kwargs):
        # init the parent class
        super(Log, self).__init__(parent=parent,
                                  name=name,
                                  duration=0.0,
                                  save_log=False)
        self._init_log_dict = log_dict
        self._init_log_items = kwargs
        self.__log_filename = None
        self.__log_writer = None

    def begin_log(self):
        """Set up per-class AND per-instance logs.
        """
        super(Log, self).begin_log()
        # set the filename, depends on whether name was passed in
        if self._name is None:
            title = "log_%s_%d" % (
                os.path.splitext(
                    os.path.basename(self._instantiation_filename))[0],
                self._instantiation_lineno)
        else:
            title = "log_%s" % self._name

        if self.__log_writer is not None:
            self.__log_writer.close()
        if self.__log_filename is not None:
            os.remove(self.__log_filename)

        self.__log_filename = self._exp.reserve_data_filename(title, "slog")
        self.__log_writer = LogWriter(self.__log_filename)

    def end_log(self, to_csv=False):
        """Close logs.
        """
        super(Log, self).end_log(to_csv)
        if self.__log_writer is not None:
            self.__log_writer.close()
            self.__log_writer = None
            if to_csv:
                csv_filename = (os.path.splitext(self.__log_filename)[0] +
                                ".csv")
                log2csv(self.__log_filename, csv_filename)

    def _enter(self):
        record = self._log_items.copy()
        record["log_time"] = self._start_time
        if self._log_dict is None:
            #self.__log_writer.write_record(record)
            #@FIX: added try/except block
            try:
                self.__log_writer.write_record(record)
            except AttributeError:
                #The file doesn't exist (is a Ref), then create the file and log
                self.begin_log()
                self.__log_writer.write_record(record)
                 #Custom end_log since this is not a child of the ParentState
                self.end_log()
        elif isinstance(self._log_dict, dict):
            #record.update(self._log_dict)
            #self.__log_writer.write_record(record)
            #@FIX added try/except block
            try:
                record.update(self._log_dict)
                self.__log_writer.write_record(record)
            except AttributeError:
                self.begin_log()
                record.update(self._log_dict)
                self.__log_writer.write_record(record)
                self.end_log()
        elif type(self._log_dict) in (tuple, list):
            for dict_ in self._log_dict:
                if not isinstance(dict_, dict):
                    raise ValueError(
                        "log_dict list/tuple must contain only dicts.")
                #record.update(dict_)
                #self.__log_writer.write_record(record)
                #@FIX: add try/except block
                try:
                    record.update(dict_)
                    self.__log_writer.write_record(record)
                except:
                    self.begin_log()
                    record.update(dict_)
                    self.__log_writer.write_record(record)
                    self.end_log()
        else:
            raise ValueError("Invalid log_dict value: %r" % self._log_dict)
        self._started = True
        self._ended = True
        clock.schedule(self.leave)


class _DelayedValueTest(State):
    """Internal class for testing the Done state.

    """
    def __init__(self, delay, value, parent=None, save_log=True, name=None,
                 blocking=True):
        # init the parent class
        super(_DelayedValueTest, self).__init__(parent=parent,
                                                duration=0.0,
                                                save_log=save_log,
                                                name=name,
                                                blocking=blocking)
        self._init_delay = delay
        self._init_value = value
        self._value_out = None

    def _enter(self):
        self._value_out = NotAvailable
        clock.schedule(self._set_value_out,
                       event_time=self._start_time+self._delay)
        self.leave()

    def _set_value_out(self):
        self._value_out = self._value
        self.finalize()


class Done(AutoFinalizeState):
    """Waits until a state is finished or a ref is evaluated.

    A *Done* state will block the experiment from continuing until a
    state is finalized. This is mainly only used when the
    timing of something like **disappear_time** needs to be logged.

    Parameters
    ----------
    states : list of states (optional)
        You can pass is a list of states, and if so, the *Done* will
        wait until all of the given states are finished running.

    Example
    -------

    ::

        lb = Label(text='Hello, World', duration=3)
        Done(lb)
        Log(label_off=lb.disappear_time['time'])

    """
    def __init__(self, *states, **kwargs):
        # init the parent class
        super(Done, self).__init__(parent=kwargs.pop("parent", None),
                                   duration=0.0,
                                   save_log=kwargs.pop("save_log", True),
                                   name=kwargs.pop("name", None),
                                   blocking=kwargs.pop("blocking", True))
        if len(kwargs):
            raise ValueError("Invalid keyword arguments for Done: %r" %
                             kwargs.keys())
        self.__states = states

    def _enter(self):
        clones = [state.current_clone for state in self.__states]
        self.__some_active = Ref(lambda : any(state._active for
                                              state in clones))
        for state in clones:
            state._add_finalize_callback(self.__some_active.dep_changed)
        self.__some_active.add_change_callback(self._check)
        clock.schedule(self._check)
        self._started = True
        self._ended = True

    def _check(self):
        some_active = self.__some_active.eval()
        if not some_active:
            self.__some_active.remove_change_callback(self._check)
            self.leave()


class Wait(State):
    """Waits an amount of seconds during experimental run time.

    A *Wait* state will wait for the duration that you give it, only then
    will it continue on to the next state.

    Parameters
    ----------
    duration : float
        The duration in seconds that you would like to wait.
    jitter : float (optional)
        **jitter** is will be randomly added to the duration of this wait,
        somewhere between 0 and **jitter** seconds.
    until : Ref (optional)
        Waits *until* the passed in *Ref* variable is not None.
    parent : ParentState (optional)
        The state you would like this state to be a child of. If not set,
        the *Experiment* will make it a child of a ParentState or the
        Experiment automatically.
    save_log : boolean (default = True, optional)
        If True, save out a .slog file containing all of the information
        for this *Wait* state.
    name : string (optional)
        The unique name of this state.
    blocking : boolean (optional, default = True)
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevant if within a *ParallelParent*.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and manipulated
    within the experiment code, and will be automatically recorded in the
    state-specific log. Refer to State class docstring for additional logged
    parameters.

    event_time : dictionary
        Keys are *time* and *error*, where *time* refers to the time the *Wait*
        state ends when the until is evaluated as true, and *error* gives you
        the maximum value that the error could be when setting the *time*.
    until_value : Ref
        A reference to the *until*.  This will be evaluated at a later time.
        Once the state is finalized, the value of the until will be logged
        here.

    Example
    -------

    ::

        from smile.common import *

        exp = Experiment()

        with Parallel():
            with Serial():
                Wait(duration=3, jitter=2)
                lb16 = Label(text="Im on the screen now", duration=2)
            with Serial():
                Wait(until=lb1.appear_time['time']!=None)
                lb2 = Label(text="Me Too!", duration=2,
                            center_y=exp.screen.center_y-100)

        exp.run()

    """
    def __init__(self, duration=None, jitter=None, until=None, parent=None,
                 save_log=True, name=None, blocking=True):
        if duration is not None and jitter is not None:
            duration = ref.jitter(duration, jitter)

        # init the parent class
        super(Wait, self).__init__(parent=parent,
                                   duration=duration,
                                   save_log=save_log,
                                   name=name,
                                   blocking=blocking)

        self.__until = until  # TODO: make sure until is Ref or None
        self._until_value = None
        self._event_time = {"time": None, "error": None}

        self._log_attrs.extend(['until_value', 'event_time'])

    def _schedule_start(self):
        if self.__until is None:
            clock.schedule(self.leave, event_time=self._start_time)
        else:
            clock.schedule(self.schedule_check_until,
                           event_time=self._start_time)

    def _unschedule_start(self):
        if self.__until is None:
            clock.unschedule(self.leave)
        else:
            clock.unschedule(self.schedule_check_until)

    def _schedule_end(self):
        if self.__until is not None:
            clock.schedule(self.leave, event_time=self._end_time)
        clock.schedule(self._finish, event_time=self._end_time)

    def _unschedule_end(self):
        if self.__until is not None:
            clock.unschedule(self.leave)
        clock.unschedule(self._finish)

    def _enter(self):
        self._event_time = {"time": None, "error": None}
        self._until_value = None

    def _leave(self):
        if self.__until is None:
            self._started = True
        else:
            # must ensure we clean up NotAvailable to avoid log error
            if self._until_value == NotAvailable:
                self._until_value = None
            self.__until.remove_change_callback(self.check_until)
            clock.unschedule(self.schedule_check_until)

    def _finish(self):
        self._ended = True
        self.finalize()

    def schedule_check_until(self):
        """Setup until condition.
        """
        self.claim_exceptions()
        self._started = True
        try:
            self._until_value = self.__until.eval()
        except NotAvailableError:
            self._until_value = NotAvailable
        #print(self._until_value, NotAvailable, type(NotAvailable), type(self._until_value))
        if self._until_value:
            clock.schedule(partial(self.cancel, self._start_time))
        else:
            self.__until.add_change_callback(self.check_until)

    def check_until(self):
        """Callback to process a change to the until value.
        """
        self.claim_exceptions()
        try:
            self._until_value = self.__until.eval()
        except NotAvailableError:
            self._until_value = NotAvailable
        if self._until_value:
            # PBS: We need to evaluate whether this is the correct
            # event_time to be using. Do we need to add in another
            # based on the clock.tick times?
            self._event_time = self._exp._app.event_time
            clock.schedule(partial(self.cancel, self._event_time["time"]))


def When(condition, body=None, name="WHEN", blocking=True):
    """Construct states to wait until a Ref value becomes True and then start
    another state.
    """
    if body is None:
        body = Serial(name="WHEN_BODY")
        body.override_instantiation_context()
    with Serial(name=name, blocking=blocking) as s:
        Wait(until=condition)
    s.claim_child(body)
    s.override_instantiation_context()
    return body


def While(condition, body=None, name="WHILE", blocking=True):
    """Construct states to wait until a Ref value becomes True and then start
    another state.  Then cancel that state when the Ref value becomes False.
    """
    if body is None:
        body = Serial(name="WHILE_BODY")
        body.override_instantiation_context()
    with Serial(name=name, blocking=blocking) as s:
        Wait(until=condition, name="WAIT_TO_START")
        with Parallel(name=name) as p:
            Wait(until=Ref.not_(condition), name="WAIT_TO_STOP")
    p.claim_child(body)
    body._blocking = False
    p.override_instantiation_context()
    s.override_instantiation_context()
    return body


class ResetClock(AutoFinalizeState):
    """State to arbitrarily set the start time of the subsequent state.

    This state is used when the timing of stimuli is extremely important to the
    end user, to the extreme that they need to know the exact moment when a key
    was pressed after the stimuli was on the screen.  When calling the
    *ResetClock* state, you have to pass in a **new_time**, and then the next
    state's start time will be the same as the time that you reset the
    clock to.

    Parameters
    ----------
    new_time : Ref
        The time you would like the next state's start time to be.
    parent : ParentState
        The state that this state is a child of.
    save_log : boolean
        If True, this state will log all of its important variables out to
        a .slog file.
    name : string
        The unique name given to this state.
    blocking : boolean

    """
    def __init__(self, new_time=None, parent=None, save_log=True, name=None,
                 blocking=True):
        # init the parent class
        super(ResetClock, self).__init__(parent=parent,
                                         save_log=save_log,
                                         name=name,
                                         blocking=blocking)
        if new_time is None:
            self._init_new_time = Ref(clock.now, use_cache=False)
        else:
            self._init_new_time = new_time

    def _enter(self):
        self._end_time = self._new_time
        self._started = True
        self._ended = True
        clock.schedule(self.leave)


class CallbackState(AutoFinalizeState):
    """Base state that calls a callback method starting at the states start
    time.
    """
    def __init__(self, repeat_interval=None, duration=0.0, parent=None,
                 save_log=True, name=None, blocking=True):
        super(CallbackState, self).__init__(duration=duration, parent=parent,
                                            save_log=save_log, name=name,
                                            blocking=blocking)
        self._init_repeat_interval = repeat_interval

    def _schedule_start(self):
        clock.schedule(self.callback, event_time=self._start_time,
                       repeat_interval=self._repeat_interval)

    def _schedule_end(self):
        clock.schedule(self.leave, event_time=self._end_time)

    def _unschedule_start(self):
        clock.unschedule(self.callback)

    def _unschedule_end(self):
        clock.unschedule(self.leave)

    def _leave(self):
        clock.unschedule(self.callback)
        self._ended = True

    def _callback(self):
        """Custom method that gets called at start time.  To be overridden by
        subclasses.
        """
        pass

    def callback(self):
        """Call the custom callback method.
        """
        self.claim_exceptions()
        self._start = True
        self._callback()


class Func(CallbackState):
    """The way you call and run a function during experimental run time

    A *Func* is a state that calls a function during experimental run time. The
    first argument is always the name of the function and the rest of the
    arguments are the arguments that are sent to the function.

    Parameters
    ----------
    func : function
        Whatever function you would like to run as experimental run time.
    pargs : positional arguments (argument, argument, argument)
        This just means you can send in parameters to *func* without
        setting the keyword.
    kwargs : (keyword = argument, keyword2 =argument2, ...)
        Whatever keyword arguments you need to send to *func*.
    parent : ParentState
        The parent state that this state is contained within.
    duration : float
        The duration you would like the state to last in seconds.
    save_log : Boolean (False)
        If set to True, will save a .slog with all of the information from
        this state.
    name : string, optional, default = None
        The unique name you give this state.
    blocking : boolean. defualt = True, optional
        If True, this state will prevent a *Parallel* state from ending. If
        False, this state will be canceled if its *ParallelParent* finishes
        running. Only relevant if within a *ParallelParent*.

    Logged Attributes
    -----------------
    All parameters above and below are available to be accessed and manipulated
    within the experiment code, and will be automatically recorded in the
    state-specific log. Refer to State class docstring for additional logged
    parameters.

    result : Ref
        A reference to the return value of this function, to be evaluated at
        experimental run time.

    Example
    -------

    ::

        def add_num(input, additive):
            input += additive
            return input

        Y = 15
        X = Func(add_num, input=Y, additive=5)
        Label(text=Ref(str, X.result), duration=2)

    This example will add 5 to `exp.X`. Very simple, but without using the
    *Func* state, you would be running **add_num** outside of experiment
    runtime.
    """
    def __init__(self, func, *pargs, **kwargs):
        # init the parent class
        super(Func, self).__init__(
            parent=kwargs.pop("parent", None),
            repeat_interval=kwargs.pop("repeat_interval", None),
            duration=kwargs.pop("duration", 0.0),
            save_log=kwargs.pop("save_log", True),
            name=kwargs.pop("name", None),
            blocking=kwargs.pop("blocking", True))

        # set up the state (these will get processed at enter)
        self._init_func = func
        self._init_pargs = pargs
        self._init_kwargs = kwargs
        self._result = NotAvailable

        self._log_attrs.extend(['result'])

    def _callback(self):
        self._result = self._func(*self._pargs, **self._kwargs)


class Debug(CallbackState):
    """Used to send debug messages to the console during experimental run time.

    You can give a **Debug** state a *name* to distinguish it from other
    **Debugs** that you might be running. **Debugs** work on with keyword
    arguments. Below is an example for how to properly use the **Debug** state
    and the sample output that it produces.

    Parameters
    ----------
    parent : ParentState
        The parent state that this state is contained within
    save_log : Boolean (False)
        If set to True, will save a .slog with all of the information
        from this state.
    name : string
        The unique name you give this state.
    kwargs : (keyword = argument)
        *Debug* will print out the value of all of the arguments at the time it
        is called during experiment run time, as well as a time-stamp.

    Example
    -------

    ::

        from smile.common import *

        exp = Experiment()

        lbl = Label(text="Hello, World", duration=2)
        Wait(until=lbl.disappear_time)
        Debug(name="Label appear debug", appear=lbl.appear_time['time'],
              disappear=lbl.disappear_time['time'])

        exp.run()


    """
    def __init__(self, parent=None, save_log=False, name=None, **kwargs):
        # init the parent class
        super(Debug, self).__init__(parent=parent,
                                    save_log=save_log,
                                    name=name)

        # set up the state
        self._init_kwargs = kwargs

    def _callback(self):
        id_strs = [
            "file: %r" % self._instantiation_filename,
            "line: %d" % self._instantiation_lineno
            ]
        if self._name is not None:
            id_strs.append("name: %s" % self._name)
        lag = clock.now() - self._start_time
        print("DEBUG (%s) - lag=%fs" % (", ".join(id_strs), lag))
        for name, value in self._kwargs.items():
            print("  %s: %r" % (name, value))


class PrintTraceback(CallbackState):
    """State that prints a SMILE traceback on the console.
    """
    def __init__(self, parent=None, save_log=False, name=None):
        # init the parent class
        super(PrintTraceback, self).__init__(parent=parent,
                                             save_log=save_log,
                                             name=name)

    def _callback(self):
        self.print_traceback()


if __name__ == '__main__':
    from .experiment import Experiment

    def print_actual_duration(target):
        print(val(target.end_time - target.start_time))

    def print_periodic():
        print("PERIODIC!")

    @Subroutine
    def DoTheThing(self, a, b, c=7, d="ssdfsd"):
        PrintTraceback(name="inside DoTheThing")
        self.foo = c * 2
        Wait(1.0)
        Debug(a=a, b=b, c=c, d=d, foo=self.foo,
              screen_size=self.exp.screen.size, name="inside DoTheThing")

    @Subroutine
    def DoTheOtherThing(self):
        Debug(name="before the yield")
        with Serial():
            yield
        with Meanwhile():
            PrintTraceback(name="during the yield")
        Debug(name="after the yield")

    exp = Experiment()

    #with UntilDone():
    #    Wait(5.0)
    with Meanwhile():
        with Loop():
            Wait(5.0)
            Func(print_periodic)

    Debug(width=exp.screen.width, height=exp.screen.height)

    with Loop(5) as loop:
        Log(a=1, b=2, c=loop.i, name="aaa")
    Log({"q": loop.i, "w": loop.i}, x=4, y=2, z=1, name="bbb")
    Log([{"q": loop.i, "w": n} for n in range(5)], x=4, y=2, z=1, name="ccc")
    #Log("sdfsd")  # This should cause an error

    exp.for_the_thing = 3
    dtt = DoTheThing(3, 4, name="first")
    Debug(foo=dtt.foo, name="outside DoTheThing")
    dtt = DoTheThing(3, 4, d="bbbbbbb", c=exp.for_the_thing)
    Debug(foo=dtt.foo, name="outside DoTheThing")

    with DoTheOtherThing():
        PrintTraceback(name="top of body")
        Wait(2.0)
        PrintTraceback(name="bottom of body")

    Wait(1.0)
    dvt = _DelayedValueTest(1.0, 42)
    Done(dvt)
    Debug(dvt_out=dvt.value_out)

    exp.bar = False
    with Parallel():
        with Serial():
            Wait(2.0)
            Func(lambda: None)  # force variable assignment to wait until correct time
            exp.bar = True
            Wait(2.0)
            Func(lambda: None)  # force variable assignment to wait until correct time
            exp.bar = False
            Wait(1.0)
        When(exp.bar, Debug(name="when test"))
        with While(exp.bar):
            with Loop():
                Wait(0.2)
                Debug(name="while test")
        with Loop(blocking=False):
            Wait(0.5)
            Debug(name="non-blocking test")

    exp.foo=1
    Record(foo=exp.foo)#, name="rectest")
    with UntilDone():
        Debug(name="FOO!")
        Wait(1.0)
        Debug(name="FOO!")
        exp.foo = 2
        Debug(name="FOO!")
        Wait(1.0)
        Debug(name="FOO!")
        exp.foo = 3
        Debug(name="FOO!")
        Wait(1.0)
        Debug(name="FOO!")

    with Parallel():
        with Serial():
            Debug(name="FOO!")
            Wait(1.0)
            Debug(name="FOO!")
            exp.foo = 4
            Debug(name="FOO!")
            Wait(1.0)
            Debug(name="FOO!")
            exp.foo = 5
            Debug(name="FOO!")
            Wait(1.0)
            Debug(name="FOO!")
        with Serial():
            Debug(name="FOO!!!")
            Wait(until=exp.foo==5, name="wait until")
            Debug(name="foo=5!")

    with Loop(10) as loop:
        with If(loop.current > 6):
            Debug(name="True")
        with Elif(loop.current > 4):
            Debug(name="Trueish")
        with Elif(loop.current > 2):
            Debug(name="Falsish")
        with Else():
            Debug(name="False")

    # with implied parents
    block = [{'val': i} for i in range(3)]
    exp.not_done = True
    with Loop(conditional=exp.not_done) as outer:
        Debug(i=outer.i)
        with Loop(block, shuffle=True) as trial:
            Debug(current_val=trial.current['val'])
            Wait(1.0)
            If(trial.current['val']==block[-1],
               Wait(2.0))
        with If(outer.i >= 3):
            exp.not_done = False

    block = range(3)
    with Loop(block) as trial:
        Debug(current=trial.current)
        Wait(1.0)
        If(trial.current==block[-1],
           Wait(2.))


    If(True,
       Debug(name="True"),
       Debug(name="False"))
    Wait(1.0)
    If(False,
       Debug(name="True"),
       Debug(name="False"))
    Wait(2.0)
    If(False, Debug(name="ACK!!!")) # won't do anything
    Debug(name="two")
    Wait(3.0)
    with Parallel():
        with Serial():
            Wait(1.0)
            Debug(name='three')
        Debug(name='four')
    Wait(2.0)

    block = [{'text':'a'},{'text':'b'},{'text':'c'}]
    with Loop(block) as trial:
        Debug(current_text=trial.current['text'])
        Wait(1.0)

    Debug(name='before meanwhile 1')
    Wait(1.0)
    with Meanwhile(name="First Meanwhile") as mw:
        Wait(15.0)
    Debug(name='after meanwhile 1')
    Func(print_actual_duration, mw)

    Debug(name='before meanwhile 2')
    Wait(5.0)
    with Meanwhile() as mw:
        PrintTraceback()
        Wait(1.0)
    Debug(name='after meanwhile 2')
    Func(print_actual_duration, mw)

    Debug(name='before untildone 1')
    Wait(15.0)
    with UntilDone(name="UntilDone #1") as ud:
        Wait(1.0)
        PrintTraceback()
    Debug(name='after untildone 1')
    Func(print_actual_duration, ud)

    Debug(name='before untildone 2')
    Wait(1.0)
    with UntilDone() as ud:
        Wait(5.0)
    Debug(name='after untildone 2')
    Func(print_actual_duration, ud)

    with Serial() as s:
        with Meanwhile():
            Wait(100.0)
        Wait(1.0)
    Func(print_actual_duration, s)
    with Serial() as s:
        with UntilDone():
            Wait(1.0)
        Wait(100.0)
    Func(print_actual_duration, s)

    Debug(name='before parallel')
    with Parallel() as p:
        Debug(name='in parallel')
        with Loop(5) as l:
            with p.insert():
                with Serial():
                    Wait(l.i)
                    Debug(name='in insert after n second wait', n=l.i)
                with Serial():
                    Wait(2.0)
                    Debug(name='in insert after 2s wait', n=l.i)
                Debug(name='in insert', n=l.i)
            p.insert(Debug(name='in insert #2', n=l.i))
    Debug(name='after parallel')

    Wait(2.0)

    exp.run(trace=False)
