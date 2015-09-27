#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from contextlib import contextmanager
from functools import partial
from types import GeneratorType
import copy
import inspect
import weakref
import os.path

import kivy_overrides
import ref
from ref import Ref, val, NotAvailable, NotAvailableError
from utils import rindex, get_class_name
from log import LogWriter, log2csv
from clock import clock


class StateConstructionError(RuntimeError):
    """
    An error with constructing a SMILE state machine.
    """
    pass


class State(object):
    """
    """
    def __init__(self, parent=None, duration=None, save_log=True, name=None,
                 blocking=True):
        # Weak value dictionary to track Refs issued by this state.  Necessary
        # because those Refs need to be notified when their dependencies
        # change.  This is first so that __setattr__ will work.
        self.__issued_refs = weakref.WeakValueDictionary()

        # If true, we write a log entry every time this state finalizes.
        self.__save_log = save_log

        # The custom name for this state.
        self._name = name

        # Whether or not this state blocks in the context of a Parallel parent.
        self._blocking = blocking

        # This is a convenience argument for automatically setting the end time
        # relative to the start time.  If it evaluates to None, it has no
        # effect.
        self._init_duration = duration

        # Start and end time for the state.  Start time is set at enter time.
        # End time must be set before leave time.  End time will be set
        # automatically at enter time if a duration is provided.
        self._start_time = None
        self._end_time = None

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
        self.set_instantiation_context()

        # Associate this state with the most recently instantiated Experiment.
        from experiment import Experiment
        try:
            self._exp = Experiment._last_instance()
        except AttributeError:
            self._exp = None

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
            self._parent = None
            self._exp._root_state = self
        else:
            self._parent = parent

        # Raise an error if we are non-blocking, but not the child of a
        # Parallel...
        #TODO: check this any time self._blocking is assigned!
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

    def __repr__(self):
        return "<%s file=%r, line=%d, name=%r, id=%x>" % (
            type(self).__name__,
            self._instantiation_filename,
            self._instantiation_lineno,
            self._name,
            id(self))

    def set_instantiation_context(self, obj=None):
        # If no object is provide as the source of he context, use self.
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
        # Get the desired frame from the call stack.
        (frame,
         filename,
         lineno,
         function,
         code_context,
         index) = inspect.stack()[depth + 2]

        # Record the source filename and line number from the stack frame.
        self._instantiation_filename = filename
        self._instantiation_lineno = lineno

    def clone(self, parent):
        # Make a shallow copy of self.
        new_clone = copy.copy(self)

        # Replace certain attributes with deep copies of themselves.
        for attr in self._deepcopy_attrs:
            setattr(new_clone, attr, copy.deepcopy(getattr(self, attr)))

        # Set the clone inactive.
        new_clone._active = False

        # Set the parent of the clone.
        new_clone._parent = parent

        return new_clone

    def get_inactive_state(self, parent):
        if self._active or self._parent is not parent:
            # If the state is active or has the wrong parent, return a clone.
            return self.clone(parent)
        else:
            # Otherwise, return the state as is.
            return self

    def tron(self, depth=0):
        self.__tracing = True
        self.__depth = depth

    def troff(self):
        self.__tracing = False

    def print_trace_msg(self, msg):
        # Create list of strings to identify this state (which will appear
        # comma-separated).  Name is included only if name is not None...
        id_strs = [
            "file: %r" % self._instantiation_filename,
            "line: %d" % self._instantiation_lineno
            ]
        if self._name is not None:
            id_strs.append("name: %s" % self._name)

        # Print the trace message.
        print "*** %s%s (%s): %s" % (
            "  " * self.__depth,
            type(self).__name__,
            ", ".join(id_strs),
            msg
            )

    def print_traceback(self, child=None, t=None):
        # Use the current time, if none is provided.
        if t is None:
            t = clock.now()
        if self._parent is None:
            # If we are the root of the state tree, print the header.
            print " SMILE Traceback:"
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
            if offset < 0.0:
                return "%fs from now%s" % (-offset, error)
            else:
                return "%fs ago%s" % (offset, error)

        # Print traceback state header.
        print "   %s%s - file: %s, line: %d" % (
            type(self).__name__,
            name_spec,
            self._instantiation_filename,
            self._instantiation_lineno)

        # Print out log attributes...
        for attr_name in self._log_attrs:
            try:
                value = val(getattr(self, attr_name))
            except NotAvailableError:
                value = NotAvailable
            if attr_name.endswith("_time"):
                print "     %s: %s" % (attr_name, tstr(value))
            else:
                print "     %s: %r" % (attr_name, value)

    def claim_exceptions(self):
        if self._exp is not None:
            # Set self as "current_state" in associated Experiment.
            self._exp._current_state = self

    def get_log_fields(self):
        return self._log_attrs

    def begin_log(self):
        if self.__save_log:
            # Use the state logger facily of the associated Experiment so that
            # only one state log is produced for the state class (rather than
            # one per instance).
            self._exp.setup_state_logger(type(self).__name__, self.get_log_fields())

    def end_log(self, to_csv=False):
        # The associated Experiment cleans up its own state loggers.
        pass

    @property
    def current_clone(self):
        # This will be called in the process of setting up
        # self,__original_state and self._most_recently_entered_clone, so it
        # has to work without those...
        if ("_State__original_state" in self.__dict__ and
            "_State__most_recently_entered_clone" in self.__dict__):
            # Return the most recently entered clone of the original state.
            return self.__original_state.__most_recently_entered_clone
        else:
            # If those attributes are not set up yet, assume self is the
            # current clone, since no clones could have been created yet.
            return self

    def get_current_attribute_value(self, name):
        # Return the named attribute from the current clone.
        return getattr(self.current_clone, name)

    def attribute_update_state(self, name, value):
        raise NotImplementedError

    def __getattr__(self, name):
        internal_name = "_" + name
        if hasattr(self, internal_name):
            # If we have an internal attribute by this name, produce a Ref that
            # evaluates to the attribute's current value.
            try:
                # If we already issued such a Ref, return that preexisting Ref.
                return self.__issued_refs[name]
            except KeyError:
                # Otherwise, create the Ref, store it, and return it.
                ref = Ref(self.get_current_attribute_value, internal_name)
                self.__issued_refs[name] = ref
                return ref
        else:
            # If we don't have an internal attribute by this name, try normal
            # attribute retrieval method.
            return super(State, self).__getattribute__(name)

    def __setattr__(self, name, value):
        # If this isn't an internal value (with a leading underscore), create
        # an attribute update state or raise an error...
        if name[0] != "_":
            try:
                self.__original_state.attribute_update_state(name, value)
                return
            except NotImplementedError:
                raise AttributeError("State does not support attribute setting!")

        # First, set the sttribute value as normal.
        super(State, self).__setattr__(name, value)

        # If this state is not the current clone of the original state, no
        # further action is taken...
        if self.current_clone is not self:
            return

        # If the name has the prefix "_init_" create a corresponding internal
        # attribute without that prefix.  Set it to None for now.  At enter
        # time it will be set to that val of the "_init_" value (resolving any
        # Refs)...
        if name[:6] == "_init_":
            setattr(self, name[5:], None)

        # If we've issued a Ref for this attribute, notify the Ref that its
        # dependencies have changed.
        try:
            ref = self.__issued_refs[name[1:]]
        except KeyError:
            return
        ref.dep_changed()

    def __dir__(self):
        lst = super(State, self).__dir__()
        return lst + self._log_attrs

    def _enter(self):
        pass

    def enter(self, start_time):
        self.claim_exceptions()
        self._start_time = start_time
        self._enter_time = clock.now()
        self._leave_time = NotAvailable
        self._finalize_time = NotAvailable
        self.__original_state.__most_recently_entered_clone = self

        # say we're active
        self._active = True
        self._following_may_run = False

        if self._parent:
            clock.schedule(partial(self._parent.child_enter_callback, self))

        # if we don't have the exp reference, get it now
        if self._exp is None:
            from experiment import Experiment
            self._exp = Experiment._last_instance()

        for name, value in self.__dict__.items():
            if name[:6] == "_init_":
                try:
                    setattr(self, name[5:], val(value))
                except NotAvailableError:
                    raise NotAvailableError(
                        ("Attempting to use unavailable value (%r) "
                         "for attribute %r of %r.  Do you need to use a Done "
                         "state?") % (value, name[6:], self))

        if self._duration is None:
            self._end_time = None
        else:
            self._end_time = self._start_time + self._duration

        # custom enter code
        self._enter()

        if self.__tracing:
            call_time = self._enter_time - self._exp._root_state._start_time
            call_duration = clock.now() - self._enter_time
            start_time = self._start_time - self._exp._root_state._start_time
            self.print_trace_msg(
                "ENTER time=%fs, duration=%fs, start_time=%fs" %
                (call_time, call_duration, start_time))

    def _leave(self):
        pass

    def leave(self):
        """
        Gets the end time of the state (logs current time)
        """
        # ignore leave call if not active
        if self._following_may_run or not self._active:
            return

        self.claim_exceptions()

        self._leave_time = clock.now()

        self._following_may_run = True
        if self._parent:
            clock.schedule(partial(self._parent.child_leave_callback, self))

        # call custom leave code
        self._leave()

        if self.__tracing:
            call_time = self._leave_time - self._exp._root_state._start_time
            call_duration = clock.now() - self._leave_time
            if self._end_time is None:
                 self.print_trace_msg(
                    "LEAVE time=%fs, duration=%fs, perpetual" %
                    (call_time, call_duration))
            else:
                end_time = self._end_time - self._exp._root_state._start_time
                self.print_trace_msg(
                    "LEAVE time=%fs, duration=%fs, end_time=%fs" %
                    (call_time, call_duration, end_time))

    def cancel(self, cancel_time):
        if self._active and not self._following_may_run:
            clock.schedule(self.leave, event_time=cancel_time)
            #QUESTION: Should this do anything in the base class at all?
            if self._end_time is None or cancel_time < self._end_time:
                self._end_time = cancel_time

    def save_log(self):
        self._exp.write_to_state_log(
            type(self).__name__,
            {name : getattr(self, "_" + name) for name in self._log_attrs})

    def finalize(self):  #TODO: call a _finalize method?
        if not self._active:
            return

        self._finalize_time = clock.now()
        self._active = False
        if self.__save_log:
            self.save_log()
        if self._parent:
            clock.schedule(partial(self._parent.child_finalize_callback, self))
        if self.__tracing:
            call_time = self._finalize_time - self._exp._root_state._start_time
            call_duration = clock.now() - self._finalize_time
            self.print_trace_msg("FINALIZE time=%fs, duration=%fs" %
                                 (call_time, call_duration))


class AutoFinalizeState(State):
    def leave(self):
        super(AutoFinalizeState, self).leave()
        clock.schedule(self.finalize)


class ParentState(State):
    """
    Base state for parents that can hold children states. 

    Only parent states can contain other states.

    Implicit hierarchies can be generated using the `with` syntax.
    
    Parameters
    ----------
    children: object
    	Children States (objects) contained within the Parent State
    parent: object
    	Parent state object
    duration: float
    	Duration of the parent state. An interval of 0 means enter the state once, 
    	-1 means every frame.
    	Defaults to -1
    save_log: bool
        If set to 'True,' details about the parent state will be automatically saved 
        in the log files.

    """
    def __init__(self, children=None, parent=None, duration=None,
                 save_log=True, name=None, blocking=True):
        super(ParentState, self).__init__(parent=parent,
                                          duration=duration,
                                          save_log=save_log,
                                          name=name,
                                          blocking=blocking)
        # process children
        if children is None:
            children = []
        self._children = []
        for c in children:
            self.claim_child(c)
        
        self.__unfinalized_children = set()

    def tron(self, depth=0):
        super(ParentState, self).tron(depth)
        child_depth = depth + 1
        for child in self._children:
            child.tron(child_depth)

    def troff(self):
        super(ParentState, self).troff()
        for child in self._children:
            child.troff()

    def begin_log(self):
        super(ParentState, self).begin_log()
        for child in self._children:
            child.begin_log()

    def end_log(self, to_csv=False):
        super(ParentState, self).end_log(to_csv)
        for child in self._children:
            child.end_log(to_csv)

    def claim_child(self, child):
        if not child._parent is None:
            child._parent._children.remove(child)
        child._parent = self
        self._children.append(child)

    def child_enter_callback(self, child):
        self.__unfinalized_children.add(child)

    def child_leave_callback(self, child):
        pass

    def child_finalize_callback(self, child):
        self.__unfinalized_children.discard(child)
        if self._following_may_run and not len(self.__unfinalized_children):
            self.finalize()

    def _enter(self):
        self.__unfinalized_children = set()

    def _leave(self):
        if not len(self._children) or not len(self.__unfinalized_children):
            clock.schedule(self.finalize)

    def __enter__(self):
        # push self as current parent
        if not self._exp is None:
            self._exp._parents.append(self)
        return self

    def __exit__(self, type, value, tb):
        # pop self off
        if not self._exp is None:
            state = self._exp._parents.pop()


class Parallel(ParentState):
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
                print "     Blocking child..."
            else:
                print "     Non-blocking child..."

    def _enter(self):
        super(Parallel, self)._enter()
        self.__blocking_children = []
        self.__my_children = []
        if len(self._children):
            for child in self._children:
                inactive_child = child.get_inactive_state(self)
                self.__my_children.append(inactive_child)
                if child._blocking:
                    self.__blocking_children.append(inactive_child)
                clock.schedule(partial(inactive_child.enter, self._start_time))
            self.__remaining = set(self.__my_children)
            self.__blocking_remaining = set(self.__blocking_children)
        else:
            self._end_time = self._start_time
            clock.schedule(self.leave)

    def child_leave_callback(self, child):
        super(Parallel, self).child_leave_callback(child)
        self.__remaining.discard(child)
        if len(self.__blocking_remaining):
            self.__blocking_remaining.discard(child)
            if not len(self.__blocking_remaining):
                self._set_end_time()
                if self._end_time is not None:
                    self.cancel(self._end_time)
        if not len(self.__remaining):
            self.leave()

    def cancel(self, cancel_time):
        if self._active:
            for child in self.__my_children:
                child.cancel(cancel_time)

    def _set_end_time(self):
        end_times = [c._end_time for c in self.__blocking_children]
        if any([et is None for et in end_times]):
            self._end_time = None
        else:
            self._end_time = max(end_times)


@contextmanager
def _ParallelWithPrevious(name=None, parallel_name=None, blocking=True):
    # get the exp reference
    from experiment import Experiment
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
    with _ParallelWithPrevious(name=name, parallel_name="MEANWHILE",
                               blocking=blocking) as p:
        yield p
    p._children[1]._blocking = False

@contextmanager
def UntilDone(name=None, blocking=True):
    with _ParallelWithPrevious(name=name, parallel_name="UNTILDONE",
                               blocking=blocking) as p:
        yield p
    p._children[0]._blocking = False


class Serial(ParentState):
    """Parent state that runs its children in serial.

    A Serial Parent State is done when the last state in the chain is
    finished.
    
    """
    def _enter(self):
        super(Serial, self)._enter()
        self.__child_iterator = iter(self._children)
        self.__current_child = None
        self.__cancel_time = None
        try:
            self.__current_child = (
                self.__child_iterator.next().get_inactive_state(self))
            clock.schedule(partial(self.__current_child.enter, self._start_time))
        except StopIteration:
            self._end_time = self._start_time
            clock.schedule(self.leave)

    def child_enter_callback(self, child):
        super(Serial, self).child_enter_callback(child)
        if self.__cancel_time is not None:
            clock.schedule(partial(child.cancel, self.__cancel_time))

    def child_leave_callback(self, child):
        super(Serial, self).child_leave_callback(child)
        next_time = self.__current_child._end_time
        if next_time is None:
            self.leave()
        elif (self.__cancel_time is not None and
            next_time >= self.__cancel_time):
            self._end_time = self.__cancel_time
            self.leave()
        else:
            try:
                self.__current_child = (
                    self.__child_iterator.next().get_inactive_state(self))
                clock.schedule(partial(self.__current_child.enter, next_time))
            except StopIteration:
                self._end_time = next_time
                clock.schedule(self.leave)

    def cancel(self, cancel_time):
        if self._active:
            clock.schedule(partial(self.__current_child.cancel, cancel_time))
            self.__cancel_time = cancel_time


class Subroutine(object):
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
    def __init__(self, subroutine, parent=None, save_log=True, name=None,
                 blocking=True):
        super(SubroutineState, self).__init__(parent=parent,
                                              save_log=save_log,
                                              name=name,
                                              blocking=blocking)
        self._subroutine = subroutine
        self._vars = {}
        self.__issued_refs = weakref.WeakValueDictionary()
        
        self._log_attrs.extend(['subroutine'])

        self.__reserved_names = set(
            self.__dict__.keys() +
            [name[1:] for name in self.__dict__.keys() if name[0] == "_"])

    def get_var_ref(self, name):
        try:
            return self.__issued_refs[name]
        except KeyError:
            ref = Ref.getitem(self._vars, name)
            self.__issued_refs[name] = ref
            return ref

    def set_var(self, name, value):
        self._vars[name] = value
        try:
            ref = self.__issued_refs[name]
        except KeyError:
            return
        ref.dep_changed()

    def __getattr__(self, name):
        if ("_SubroutineState__reserved_names" not in self.__dict__ or
            name in self.__reserved_names):
            return super(SubroutineState, self).__getattr__(name)
        else:
            return self.get_var_ref(name)

    def __setattr__(self, name, value):
        if (name[0] == "_" or
            "_SubroutineState__reserved_names" not in self.__dict__ or
            name in self.__reserved_names):
            super(SubroutineState, self).__setattr__(name, value)
        else:
            return SubroutineSet(self, name, value)

    def __dir__(self):
        return super(SubroutineState, self).__dir__() + self._vars.keys()


class SubroutineSet(AutoFinalizeState):
    def __init__(self, subroutine, var_name, value, parent=None, save_log=True,
                 name=None):
        super(SubroutineSet, self).__init__(parent=parent,
                                            save_log=save_log,
                                            name=name,
                                            duration=0.0)
        self.__subroutine = subroutine
        self._subroutine_state = subroutine._name
        self._init_var_name = var_name
        self._init_value = value

        self._log_attrs.extend(['subroutine_state', 'var_name', 'value'])
        
    def _enter(self):
        self.__subroutine._vars[self._var_name] = self._value
        clock.schedule(self.leave)

    
class If(ParentState):
    def __init__(self, conditional, true_state=None, false_state=None, 
                 parent=None, save_log=True, name=None, blocking=True):

        # init the parent class
        super(If, self).__init__(parent=parent, save_log=save_log, name=name,
                                 blocking=blocking)

        # save a list of conds to be evaluated (last one always True, acts as the Else)
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
        
    def _enter(self):
        super(If, self)._enter()
        self._outcome_index = self._cond.index(True)
        self.__selected_child = (
            self._out_states[self._outcome_index].get_inactive_state(self))
        clock.schedule(partial(self.__selected_child.enter, self._start_time))

    def child_leave_callback(self, child):
        super(If, self).child_leave_callback(child)
        self._end_time = child._end_time
        self.leave()

    def __enter__(self):
        # push self.__true_state as current parent
        if not self._exp is None:
            self._exp._parents.append(self.__true_state)
        return self

    def cancel(self, cancel_time):
        if self._active:
            self.__selected_child.cancel(cancel_time)


class Elif(Serial):
    """State to attach an elif to and If state.

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
    """State to attach to the else of an If state.

    """
    # get the exp reference
    from experiment import Experiment
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


class Loop(ParentState):
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

        self._i = None
        self._current = None

        self.__body_state = Serial(parent=self, name="LOOP BODY")
        self.__body_state._instantiation_filename = self._instantiation_filename
        self.__body_state._instantiation_lineno = self._instantiation_lineno
        self.__current_child = None
        self.__cancel_time = None

        self._log_attrs.extend(['outcome', 'i', 'current'])

    def iter_i(self):
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

            for i in xrange(count):
                yield i

    def _enter(self):
        # get the parent enter
        super(Loop, self)._enter()
        self._outcome = NotAvailable
        self.__current_child = None
        self.__cancel_time = None
        self.__i_iterator = self.iter_i()
        self.start_next_iteration(self._start_time)

    def start_next_iteration(self, next_time):
        try:
            self._i = self.__i_iterator.next()
            if self._iterable is None or isinstance(self._iterable, int):
                self._current = self._i
            else:
                self._current = self._iterable[self._i]
        except StopIteration:
            self._end_time = next_time
            clock.schedule(self.leave)
            return
        self.__current_child = self.__body_state.get_inactive_state(self)
        clock.schedule(partial(self.__current_child.enter, next_time))

    def child_enter_callback(self, child):
        super(Loop, self).child_enter_callback(child)
        if self.__cancel_time is not None:
            child.cancel(self.__cancel_time)

    def child_leave_callback(self, child):
        super(Loop, self).child_leave_callback(child)
        next_time = self.__current_child._end_time
        if next_time is None:
            self.leave()
        elif (self.__cancel_time is not None and
              next_time >= self.__cancel_time):
            self._end_time = self.__cancel_time
            self.leave()
        else:
            self.start_next_iteration(next_time)

    def cancel(self, cancel_time):
        if self._active:
            self.__current_child.cancel(cancel_time)
            self.__cancel_time = cancel_time

    def __enter__(self):
        # push self.__body_state as current parent
        if not self._exp is None:
            self._exp._parents.append(self.__body_state)
        return self


class Record(State):
    def __init__(self, duration=None, parent=None, name=None, blocking=True,
                 **kwargs):
        super(Record, self).__init__(parent=parent, 
                                     duration=duration, 
                                     save_log=False,
                                     name=name,
                                     blocking=blocking)

        self.__refs = kwargs

    def begin_log(self):
        super(Record, self).begin_log()
        title = "record_%s_%d_%s" % (
            os.path.splitext(
                os.path.basename(self._instantiation_filename))[0],
            self._instantiation_lineno,
            self._name)
        self.__log_filename = self._exp.reserve_data_filename(title, "smlog")
        self.__log_writer = LogWriter(self.__log_filename,
                                      self.__refs.keys() + ["timestamp"])

    def end_log(self, to_csv=False):
        super(Record, self).end_log(to_csv)
        if self.__log_writer is not None:
            self.__log_writer.close()
            self.__log_writer = None
            if to_csv:
                csv_filename = (os.path.splitext(self.__log_filename)[0] +
                                ".csv")
                log2csv(self.__log_filename, csv_filename)

    def _enter(self):
        clock.schedule(self.leave, event_time=self._start_time)
        if self._end_time is not None:
            clock.schedule(self.finalize, event_time=self._end_time)

    def _leave(self):
        for name, ref in self.__refs.iteritems():
            self.record_change()
            ref.add_change_callback(self.record_change)

    def finalize(self):
        super(Record, self).finalize()
        for name, ref in self.__refs.iteritems():
            ref.remove_change_callback(self.record_change)

    def record_change(self):
        try:
            record = val(self.__refs)
        except NotAvailableError:
            raise NotAvailableError(
                "One or more recorded values not available!")
        record["timestamp"] = self._exp._app.event_time
        self.__log_writer.write_record(record)

    def cancel(self, cancel_time):
        if self._active:
            if cancel_time < self._start_time:
                clock.unschedule(self.leave)
                clock.schedule(self.leave)
                clock.unschedule(self.finalize)
                clock.schedule(self.finalize)
                self._end_time = self._start_time
            elif self._end_time is None or cancel_time < self._end_time:
                clock.unschedule(self.finalize)
                clock.schedule(self.finalize, event_time=cancel_time)
                self._end_time = cancel_time


class Log(AutoFinalizeState):
    def __init__(self, parent=None, name=None, **kwargs):
        # init the parent class
        super(Log, self).__init__(parent=parent,
                                  name=name,
                                  duration=0.0,
                                  save_log=False)
        self._init_log_items = kwargs

    def begin_log(self):
        super(Log, self).begin_log()
        title = "log_%s_%d_%s" % (
            os.path.splitext(
                os.path.basename(self._instantiation_filename))[0],
            self._instantiation_lineno,
            self._name)
        self.__log_filename = self._exp.reserve_data_filename(title, "smlog")
        self.__log_writer = LogWriter(self.__log_filename,
                                      ["time"] + self._init_log_items.keys())

    def end_log(self, to_csv=False):
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
        record["time"] = self._start_time
        self.__log_writer.write_record(record)
        clock.schedule(self.leave)


class _DelayedValueTest(State):
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
    def __init__(self, *states, **kwargs):
        # init the parent class
        super(Done, self).__init__(parent=kwargs.pop("parent", None), 
                                   duration=0.0, 
                                   save_log=kwargs.pop("save_log", True),
                                   name=kwargs.pop("name", None),
                                   blocking=kwargs.pop("blocking", True))
        if len(kwargs):
            raise ValueError("Invalid keyword arguments for Done: %r" %
                             kwargs.iterkeys())
        self.__some_active = Ref(any, [state.active for state in states])

    def _enter(self):
        self.__some_active.add_change_callback(self._check)

    def _check(self):
        some_active = self.__some_active.eval()
        if not some_active:
            self.__some_active.remove_change_callback(self._check)
            self.leave()

    def cancel(self):
        pass


class Wait(State):
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

        self.__until = until  #TODO: make sure until is Ref or None
        self._until_value = None
        self._event_time = {"time": None, "error": None}

        self._log_attrs.extend(['until_value', 'event_time'])

    def _enter(self):
        self._event_time = {"time": None, "error": None}
        if self.__until is None:
            clock.schedule(self.leave, event_time=self._start_time)
            if self._end_time is not None:
                clock.schedule(self.finalize, event_time=self._end_time)
        else:
            try:
                self._until_value = self.__until.eval()
            except NotAvailableError:
                raise NotAvailableError("Until value (%r) was unavailable!" %
                                        self.__until)
            if self._until_value:
                clock.schedule(partial(self.cancel, self._start_time))
            else:
                clock.schedule(partial(self.__until.add_change_callback,
                                       self.check_until),
                               event_time=self._start_time)
                if self._end_time is not None:
                    clock.schedule(self.leave, event_time=self._end_time)
                    clock.schedule(self.finalize, event_time=self._end_time)

    def _leave(self):
        if self.__until is not None:
            self.__until.remove_change_callback(self.check_until)

    def check_until(self):
        try:
            self._until_value = self.__until.eval()
        except NotAvailableError:
            raise NotAvailableError("Until value (%r) was unavailable!" %
                                    self._until)
        if self._until_value:
            self._event_time = self._exp._app.event_time
            clock.schedule(partial(self.cancel, self._event_time["time"]))

    def cancel(self, cancel_time):
        if self._active:
            cancel_time = max(cancel_time, self._start_time)
            if self._end_time is not None:
                cancel_time = min(cancel_time, self._end_time)
            if self.__until is None:
                if self._end_time is None or cancel_time < self._end_time:
                    clock.unschedule(self.finalize)
                    clock.schedule(self.finalize, event_time=cancel_time)
                    self._end_time = cancel_time
            else:
                if self._end_time is None or cancel_time < self._end_time:
                    clock.unschedule(self.leave)
                    clock.unschedule(self.finalize)
                    clock.schedule(self.leave, event_time=cancel_time)
                    clock.schedule(self.finalize, event_time=cancel_time)
                    self._end_time = cancel_time


def When(condition, body=None, name="WHEN", blocking=True):
    if body is None:
        body = Serial(name="WHEN_BODY")
        body.override_instantiation_context()
    with Serial(name=name, blocking=blocking) as s:
        Wait(until=condition)
    s.claim_child(body)
    s.override_instantiation_context()
    return body


def While(condition, body=None, name="WHILE", blocking=True):
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
    def __init__(self, new_time=None, parent=None, save_log=True, name=None,
                 blocking=True):
        # init the parent class
        super(ResetClock, self).__init__(parent=parent,
                                         save_log=save_log,
                                         name=name,
                                         blocking=blocking)
        if new_time is None:
            #TODO: define "now" in ref.py
            #TODO: use maximum of now and start time?
            self._init_new_time = Ref(clock.now, use_cache=False)
        else:
            self._init_new_time = new_time

    def _enter(self):
        self._end_time = self._new_time
        clock.schedule(self.leave)


class CallbackState(AutoFinalizeState):
    def __init__(self, repeat_interval=None, duration=0.0, parent=None,
                 save_log=True, name=None, blocking=True):
        super(CallbackState, self).__init__(duration=duration, parent=parent,
                                            save_log=save_log, name=name,
                                            blocking=blocking)
        self._init_repeat_interval = repeat_interval

    def _enter(self):
        clock.schedule(self.callback, event_time=self._start_time,
                       repeat_interval=self._repeat_interval)
        if self._end_time is not None:
            clock.schedule(self.leave, event_time=self._end_time)

    def _leave(self):
        clock.unschedule(self.callback)

    def _callback(self):
        pass

    def callback(self):
        self.claim_exceptions()
        self._callback()

    def cancel(self, cancel_time):
        if self._active:
            cancel_time = max(cancel_time, self._start_time)
            if self._end_time is None or cancel_time < self._end_time:
                clock.unschedule(self.leave)
                clock.schedule(self.leave, event_time=cancel_time)
                self._end_time = cancel_time


class Func(CallbackState):
    def __init__(self, func, *pargs, **kwargs):
        # init the parent class
        super(Func, self).__init__(
            parent=kwargs.pop("parent", None),
            repeat_interval=kwargs.pop("repeat_interval", None),
            duration=kwargs.pop("duration", 0.0),
            save_log=kwargs.pop("save_log", True),
            name=kwargs.pop("name", None),
            blocking=kwargs.pop("blocking", True))

        # set up the state
        self._init_func = func
        self._init_pargs = pargs
        self._init_kwargs = kwargs
        self._result = NotAvailable

        self._log_attrs.extend(['result'])

    def _callback(self):
        self._result = self._func(*self._pargs, **self._kwargs)


class Debug(CallbackState):
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
        print "DEBUG (%s) - lag=%fs" % (", ".join(id_strs), lag)
        for name, value in self._kwargs.iteritems():
            print "  %s: %r" % (name, value)


class PrintTraceback(CallbackState):
    def __init__(self, parent=None, save_log=False, name=None):
        # init the parent class
        super(PrintTraceback, self).__init__(parent=parent,
                                             save_log=save_log,
                                             name=name)

    def _callback(self):
        self.print_traceback()


if __name__ == '__main__':
    from experiment import Experiment, Set, Get

    def print_actual_duration(target):
        print target._end_time - target._start_time

    def print_periodic():
        print "PERIODIC!"

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
    Record(foo=Get('foo'))
    with UntilDone():
        Debug(name="FOO!")
        Wait(1.0)
        Debug(name="FOO!")
        Set(foo=2)
        Debug(name="FOO!")
        Wait(1.0)
        Debug(name="FOO!")
        Set(foo=3)
        Debug(name="FOO!")
        Wait(1.0)
        Debug(name="FOO!")

    with Parallel():
        with Serial():
            Debug(name="FOO!")
            Wait(1.0)
            Debug(name="FOO!")
            Set(foo=4)
            Debug(name="FOO!")
            Wait(1.0)
            Debug(name="FOO!")
            Set(foo=5)
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
    Set(not_done=True)
    with Loop(conditional=Get('not_done')) as outer:
        Debug(i=outer.i)
        with Loop(block, shuffle=True) as trial:
            Debug(current_val=trial.current['val'])
            Wait(1.0)
            If(trial.current['val']==block[-1],
               Wait(2.0))
        If(outer.i>=3,Set(not_done=False))
        
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

    Wait(2.0)

    exp.run(trace=False)
