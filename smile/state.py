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
import copy
import inspect
import weakref
import os.path

import kivy_overrides
import ref
from ref import Ref, val, NotAvailable, on_available, cancel_on_available
from utils import rindex, get_class_name
from log import LogWriter, log2csv
from clock import clock, event_time


class StateConstructionError(RuntimeError):
    """
    An error with constructing a SMILE state machine.
    """
    pass


class State(object):
    def __init__(self, parent=None, duration=None, save_log=True, name=None,
                 blocking=True):
        # Weak value dictionary to track Refs issued by this state.  Necessary
        # because those Refs need to be notified when their dependencies
        # change.  This is first so that __setattr__ will work.
        self.__issued_refs = weakref.WeakValueDictionary()

        # Set of attributes to be evaluated at enter time.
        self.__init_attrs = set()

        # Set of attribute names to be made available as Refs and to be
        # cleared to NotAvailable on enter.
        self.__ref_attrs = set()

        # List of attributes (minus a leading "_log") to be written to the
        # state log at leave time.
        self.__log_attrs = []

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
        self._log_start_time = NotAvailable
        self._log_end_time = NotAvailable

        # Record of enter time and leave time at and after the most recent
        # enter.
        self._log_enter_time = NotAvailable
        self._log_leave_time = NotAvailable

        # This flag is set True at enter time and False at finalize time.  It
        # indicates that it is not safe to enter this instance for a new
        # execution of the state.  If the instance is active a new clone of the
        # state can be constructed and that one entered instead.
        self._active = False

        #...
        self.__scheduled_enter = None

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
            self._log_instantiation_filename = filename
            self._log_instantiation_lineno = lineno
            break
        else:
            raise StateConstructionError(
                "Can't figure out where instantiation took place!")

    def __repr__(self):
        return "<%s file=%r, line=%d, name=%r>" % (
            type(self).__name__,
            self._instantiation_filename,
            self._instantiation_lineno,
            self._name)

    def override_instantiation_context(self, depth=0):
        # Get the desired frame from the call stack.
        (frame,
         filename,
         lineno,
         function,
         code_context,
         index) = inspect.stack()[depth + 2]

        # Record the source filename and line number from the stack frame.
        self._log_instantiation_filename = filename
        self._log_instantiation_lineno = lineno

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

        #...
        new_clone.__scheduled_enter = None

        return new_clone

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
        for attr_name in ([target_name for name, target_name in
                           self.__init_attrs] +
                          [target_name for name, target_name, field_name in
                           self.__log_attrs] +
                          list(self.__ref_attrs)):
            value = val(getattr(self, attr_name))
            if attr_name.endswith("_time"):
                print "     %s: %s" % (attr_name[1:], tstr(value))
            else:
                print "     %s: %r" % (attr_name[1:], value)

    def claim_exceptions(self):
        if self._exp is not None:
            # Set self as "current_state" in associated Experiment.
            self._exp._current_state = self

    def get_log_fields(self):
        return [field_name for name, target_name, field_name in
                self.__log_attrs]

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

        # First, set the attribute value as normal.
        super(State, self).__setattr__(name, value)

        #...
        if name[:6] == "_init_":
            target_name = name[5:]
            self.__init_attrs.add((name, target_name))
            self.__dict__[target_name] = NotAvailable
        elif name[:5] == "_log_":
            target_name = name[4:]
            field_name = name[5:]
            item = name, target_name, field_name
            if item not in self.__log_attrs:
                self.__log_attrs.append(item)
            self.__dict__[target_name] = value
        elif value is NotAvailable:
            self.__ref_attrs.add(name)
        #TODO: after state machine construction, replace __setattr__ with alternative that omits this part (for efficiency)?

        # If this state is not the current clone of the original state, no
        # further action is taken...
        if self.current_clone is not self:
            return

        # If we've issued a Ref for this attribute, notify the Ref that its
        # dependencies have changed.
        try:
            ref = self.__issued_refs[name[1:]]
        except KeyError:
            return
        ref.dep_changed()

    def __dir__(self):
        lst = super(State, self).__dir__()
        return (lst +
                [field_name for name, target_name, field_name in
                 self.__log_attrs] +
                [target_name[1:] for name, target_name in self.__init_attrs] +
                [name[1:] for name in self.__ref_attrs])

    def schedule(self, start_time, callback):
        def avail_cb(start_time=start_time, callback=callback):
            start_time = val(start_time)
            if start_time is not None:
                earliest_enter = start_time - 5.0
                clock.schedule(partial(self.enter, start_time),
                               event_time=earliest_enter)
                clock.schedule(callback, event_time=earliest_enter)
        self._active = True#???
        self.__scheduled_enter = on_available(
            (start_time, [self.__dict__[name] for name, target_name in
                          self.__init_attrs]), avail_cb)
        if self.__tracing:
            call_time = clock.now() - self._exp._root_state._start_time
            self.print_trace_msg("SCHEDULE time=%fs" % call_time)

    def _enter(self):
        pass

    def enter(self, start_time):
        self.claim_exceptions()
        self.__original_state.__most_recently_entered_clone = self

        #...
        for name, target_name in self.__init_attrs:
            self.__dict__[target_name] = val(self.__dict__[name])

        #...
        for name, target_name, field_name in self.__log_attrs:
            self.__dict__[target_name] = self.__dict__[name]

        #...
        for name in self.__ref_attrs:
            self.__dict__[name] = NotAvailable

        #...
        self._start_time = val(start_time)
        self._enter_time = clock.now()

        # say we're active
        self._active = True

        if self._parent:
            clock.schedule(partial(self._parent.child_enter_callback, self))

        # if we don't have the exp reference, get it now
        if self._exp is None:
            from experiment import Experiment
            self._exp = Experiment._last_instance()

        #...
        if self._duration is None:
            self._end_time = NotAvailable
        else:
            self._end_time = self._start_time + self._duration

        # custom enter code
        self._enter()

        if self.__tracing:
            call_time = self._enter_time - self._exp._root_state._start_time
            call_duration = clock.now() - self._enter_time
            start_time = val(self._start_time - self._exp._root_state._start_time)
            self.print_trace_msg(
                "ENTER time=%fs, duration=%fs, start_time=%fs" %
                (call_time, call_duration, start_time))

    def _leave(self):
        pass

    def leave(self):
        # ignore leave call if not active
        if not self._active:
            return

        self.claim_exceptions()

        self._leave_time = clock.now()

        self._active = False

        if self.__save_log:
            self.save_log()

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
                end_time = val(self._end_time - self._exp._root_state._start_time)
                self.print_trace_msg(
                    "LEAVE time=%fs, duration=%fs, end_time=%fs" %
                    (call_time, call_duration, end_time))

    def _cancel(self, cancel_time):
        pass

    def cancel(self, cancel_time):
        if self._active:
            cancel_time = max(cancel_time, self._start_time)
            end_time = val(self.end_time)
            if end_time in (None, NotAvailable) or cancel_time < end_time:
                if end_time is not NotAvailable:
                    self._end_time = cancel_time
                self._cancel(cancel_time)
        else:
            cancel_on_available(self.__scheduled_enter)
            self.__scheduled_enter = None

    def save_log(self):
        record = {}
        for name, target_name, field_name in self.__log_attrs:
            value = val(self.__dict__[target_name])
            if value is NotAvailable:
                raise RuntimeError(
                    "Field %r is not available for saving to log!" %
                    field_name)
            record[field_name] = value
        self._exp.write_to_state_log(type(self).__name__, record)


class ParentState(State):
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
        pass

    def child_leave_callback(self, child):
        pass

    def _enter(self):
        if not len(self._children):
            clock.schedule(self.leave)

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
        self.__my_children = set()

    def print_traceback(self, child=None, t=None):
        super(Parallel, self).print_traceback(child, t)
        if child is not None:
            if child._blocking:
                print "     Blocking child..."
            else:
                print "     Non-blocking child..."

    def _enter(self):
        super(Parallel, self)._enter()
        blocking_children = []
        self.__my_children = set()
        if len(self._children):
            for child in self._children:
                inactive_child = child.clone(self)
                self.__my_children.add(inactive_child)
                if child._blocking:
                    blocking_children.append(inactive_child)
                clock.schedule(partial(inactive_child.enter, self._start_time))
            self._end_time = Ref(max, [child._end_time for child in
                                       blocking_children])
            on_available(self._end_time, self._end_time_callback)
        else:
            self._end_time = self._start_time

    def _end_time_callback(self):
        self.cancel(val(self._end_time))

    def child_leave_callback(self, child):
        self.__my_children.discard(child)
        if not len(self.__my_children):
            self.leave()

    def _cancel(self, cancel_time):
        for child in self.__my_children:
            child.cancel(cancel_time)


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


class SequentialState(ParentState):
    def __init__(self, children=None, parent=None, save_log=True, name=None,
                 blocking=True):
        super(SequentialState, self).__init__(children=children,
                                              parent=parent,
                                              save_log=save_log,
                                              name=name,
                                              blocking=blocking)
        self.__active_children = set()

    def _enter(self):
        super(SequentialState, self)._enter()
        self.__child_iterator = self._get_child_iterator()
        self.__current_child = None
        self.__state_time = self._start_time
        self.__cancel_time = None
        self._schedule_next()

    def _get_child_iterator(self):
        raise NotImplementedError

    def _schedule_next(self):
        try:
            self.__current_child = (
                self.__child_iterator.next().clone(self))
            self.__current_child.schedule(self.__state_time, self._schedule_next)
            self.__state_time = self.__current_child.end_time
        except StopIteration:
            self._end_time = self.__state_time
            self.__current_child = None

    def child_enter_callback(self, child):
        super(SequentialState, self).child_enter_callback(child)
        self.__active_children.add(child)
        if self.__cancel_time is not None:
            clock.schedule(partial(child.cancel, self.__cancel_time))

    def child_leave_callback(self, child):
        self.__active_children.discard(child)
        if self.__current_child is None and not len(self.__active_children):
            self.leave()

    def _cancel(self, cancel_time):
        for child in self.__active_children:
            child.cancel(cancel_time)
        self.__cancel_time = cancel_time


class Serial(SequentialState):
    def _get_child_iterator(self):
        return iter(self._children)


class Loop(SequentialState):
    def __init__(self, iterable=None, shuffle=False, conditional=True,
                 parent=None, save_log=True, name=None, blocking=True):
        super(Loop, self).__init__(parent=parent, save_log=save_log, name=name,
                                   blocking=blocking)

        if shuffle:
            self._init_iterable = ref.shuffle(iterable)
        else:
            self._init_iterable = iterable
        self._cond = conditional

        self._log_outcome = NotAvailable
        self._log_i = NotAvailable
        self._log_current = NotAvailable

        self.__body_state = Serial(parent=self, name="LOOP BODY")
        self.__body_state._log_instantiation_filename = self._instantiation_filename
        self.__body_state._log_instantiation_lineno = self._instantiation_lineno

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

    def _get_child_iterator(self):
        for self._i in self.iter_i():
            if self._iterable is None or isinstance(self._iterable, int):
                self._current = self._i
            else:
                self._current = self._iterable[self._i]
            yield self.__body_state

    def __enter__(self):
        # push self.__body_state as current parent
        if not self._exp is None:
            self._exp._parents.append(self.__body_state)
        return self

    
class If(ParentState):
    def __init__(self, conditional, true_state=None, false_state=None, 
                 parent=None, save_log=True, name=None, blocking=True):

        # init the parent class
        super(If, self).__init__(parent=parent, save_log=save_log, name=name,
                                 blocking=blocking)

        # save a list of conds to be evaluated (last one always True, acts as the Else)
        self._init_cond = [conditional, True]
        self._log_outcome_index = NotAvailable
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
        
    def _enter(self):
        super(If, self)._enter()

        self._outcome_index = self._cond.index(True)
        self.__selected_child = (
            self._out_states[self._outcome_index].clone(self))
        clock.schedule(partial(self.__selected_child.enter, self._start_time))
        self._end_time = self.__selected_child.end_time

    def child_leave_callbacl(self, child):
        self.leave()

    def __enter__(self):
        # push self.__true_state as current parent
        if not self._exp is None:
            self._exp._parents.append(self.__true_state)
        return self

    def _cancel(self, cancel_time):
        self.__selected_child.cancel(cancel_time)


class Elif(Serial):
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


class CallbackState(State):
    def __init__(self, repeat_interval=None, duration=0.0, parent=None,
                 save_log=True, name=None, blocking=True):
        super(CallbackState, self).__init__(duration=duration, parent=parent,
                                            save_log=save_log, name=name,
                                            blocking=blocking)
        self._init_repeat_interval = repeat_interval
        self.__on_end_time = None

    def _enter(self):
        clock.schedule(self.callback, event_time=self._start_time,
                       repeat_interval=self._repeat_interval)
        self.__on_end_time = on_available(self.end_time, self._schedule_finish)

    def _callback(self):
        pass

    def callback(self):
        self.claim_exceptions()
        self._callback()

    def _schedule_finish(self):
        end_time = val(self._end_time)
        if end_time is not None:
            clock.schedule(self.finish, event_time=end_time)

    def _finish(self):
        pass

    def finish(self):
        self.claim_exceptions()
        clock.unschedule(self.callback)
        self._finish()
        self.leave()

    def _cancel(self, cancel_time):
        cancel_on_available(self.__on_end_time)
        clock.unschedule(self.finish)
        clock.schedule(self.finish, event_time=cancel_time)


class Record(CallbackState):
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

    def _callback(self):
        for name, ref in self.__refs.iteritems():
            self.record_change()
            ref.add_change_callback(self.record_change)

    def _finish(self):
        for name, ref in self.__refs.iteritems():
            ref.remove_change_callback(self.record_change)

    def record_change(self):
        record = val(self.__refs)
        record["timestamp"] = self._exp._app.event_time
        self.__log_writer.write_record(record)


class Log(State):
    #TODO: make this not block scheduling subsequent states at all
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


class Wait(CallbackState):
    def __init__(self, duration=None, jitter=None, until=None, timeout=None,
                 parent=None, save_log=True, name=None, blocking=True):
        if duration is None:
            if until is  None:
                raise StateConstructionError(
                    "Wait state cannot have both duration and until.")
        elif jitter is not None:
            duration = ref.jitter(duration, jitter)

        # init the parent class
        super(Wait, self).__init__(parent=parent, 
                                   duration=duration, 
                                   save_log=save_log,
                                   name=name,
                                   blocking=blocking)
        if until is None or isinstance(until, Ref):
            self.__until = until
        else:
            self.__until = Ref.object(until)
        self.__timeout = timeout
        self._log_until_value = NotAvailable
        self._log_event_time = NotAvailable

    def _callback(self):
        self._event_time = event_time()
        if self.__until is not None:
            self.__until.add_true_callback(self._until_callback)
            if self.__timeout is not None:
                self.__timeout_time = self._start_time + self.__timeout
                clock.schedule(self._timeout_callback,
                               event_time=self.__timeout_time)

    def _until_callback(self):
        self._event_time = self._exp._app.event_time
        self._end_time = self._event_time["time"]

    def _timeout_callback(self):
        print "Moo!"#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self._event_time = event_time()
        print self._end_time#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #import pdb; pdb.set_trace()#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self._end_time = self.__timeout_time
        print self._end_time#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    def _finish(self):
        if self.__until is None:
            self._until_value = None
        else:
            clock.unschedule(self._timeout_callback)
            self.__until.remove_true_callback(self._until_callback)
            self._until_value = val(self.__until)


def When(condition, body=None, name="WHEN", blocking=True):
    if body is None:
        body = Serial(name="WHEN_BODY")
        body.override_instantiation_context()
    with Serial(name=name, blocking=blocking) as s:
        w = Wait(until=condition)
    s.claim_child(body)
    s.override_instantiation_context()
    w.override_instantiation_context()
    return body


def While(condition, body=None, name="WHILE", blocking=True):
    if body is None:
        body = Serial(name="WHILE_BODY")
        body.override_instantiation_context()
    with Serial(name=name, blocking=blocking) as s:
        w1 = Wait(until=condition, name="WAIT_TO_START")
        with Parallel(name=name) as p:
            w2 = Wait(until=Ref.not_(condition), name="WAIT_TO_STOP")
    p.claim_child(body)
    body._blocking = False
    p.override_instantiation_context()
    s.override_instantiation_context()
    w1.override_instantiation_context()
    w2.override_instantiation_context()
    return body


class ResetClock(State):
    def __init__(self, new_time=None, parent=None, save_log=True, name=None,
                 blocking=True):
        # init the parent class
        super(ResetClock, self).__init__(parent=parent,
                                         save_log=save_log,
                                         name=name,
                                         blocking=blocking)
        if new_time is None:
            #TODO: use maximum of now and start time?
            self._init_new_time = Ref.now()
        else:
            self._init_new_time = new_time

    def _enter(self):
        self._end_time = self._new_time
        clock.schedule(self.leave)


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
        self._log_result = NotAvailable

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

    exp = Experiment()

    #with UntilDone():
    #    Wait(5.0)
    with Meanwhile():
        with Loop():
            Wait(5.0)
            Func(print_periodic)

    Debug(width=exp.screen.width, height=exp.screen.height)

    exp.bar = False
    with Parallel():
        with Serial():
            Wait(until=False, timeout=2.0)  # force variable assignment to wait until correct time
            exp.bar = True
            Wait(until=False, timeout=2.0)  # force variable assignment to wait until correct time
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

    exp.run(trace=True)
