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

import kivy_overrides
import ref
from ref import Ref, val
from utils import rindex, get_class_name
from log import dump
from clock import clock


class StateConstructionError(RuntimeError):
    pass


class State(object):
    def __init__(self, parent=None, duration=None, save_log=True, name=None):
        self.__issued_refs = weakref.WeakValueDictionary()
        self._state_time = None  #????????????????????????????????????????????????????????????????????
        self._start_time = None
        self._end_time = None
        self._enter_time = None
        self._leave_time = None
        self._finalize_time = None

        self._init_duration = duration
        self._active = False
        self._following_may_run = False
        self.__save_log = save_log
        self._name = name
        self.__depth = 0
        self.__tracing = False

        # get instantiation context
        self.set_instantiation_context()

        # get the exp reference
        from experiment import Experiment
        try:
            self._exp = Experiment.last_instance()
        except AttributeError:
            self._exp = None

        # try and set the current parent
        if parent is None:
            if self._exp is None:
                self._parent = None
            else:
                self._parent = self._exp._parents[-1]
        elif parent is self._exp:
            self._parent = None
            self._exp.root_state = self
        else:
            self._parent = parent

        # add self to children if we have a parent
        if self._parent:
            # append to children
            self._parent._children.append(self)

        # start the log
        self._log_attrs = ['state_time', 'start_time', 'end_time', 'enter_time',
                           'leave_time', 'finalize_time', 'name']

        # cloning stuff
        self._deepcopy_attrs = []  #TODO: extend this for subclasses!
        self.__original_state = self
        self.__most_recently_entered_clone = self

    def set_instantiation_context(self, obj=None):
        if obj is None:
            obj = self
        base_inits = {}
        for base in inspect.getmro(type(obj)):
            if base is not object and hasattr(base, "__init__"):
                init = base.__init__
                filename = inspect.getsourcefile(init)
                lines, start_lineno = inspect.getsourcelines(init)
                base_inits.setdefault(filename, []).extend(
                    range(start_lineno, start_lineno + len(lines)))
        for (frame, filename, lineno,
             function, code_context, index) in inspect.stack()[1:]:
            if filename in base_inits and lineno in base_inits[filename]:
                continue
            self._instantiation_filename = filename
            self._instantiation_lineno = lineno
            break
        else:
            raise StateConstructionError(
                "Can't figure out where instantiation took place!")

    def override_instantiation_context(self, depth=0):
        (frame,
         filename,
         lineno,
         function,
         code_context,
         index) = inspect.stack()[depth + 2]
        self._instantiation_filename = filename
        self._instantiation_lineno = lineno

    def clone(self, parent):
        new_clone = copy.copy(self)
        for attr in self._deepcopy_attrs:
            setattr(new_clone, attr, copy.deepcopy(getattr(self, attr)))
        new_clone._active = False
        new_clone._parent = parent
        return new_clone

    def get_inactive_state(self, parent):
        if self._active or self._parent is not parent:
            return self.clone(parent)
        else:
            return self

    def tron(self, depth=0):
        self.__tracing = True
        self.__depth = depth

    def troff(self):
        self.__tracing = False

    def print_trace_msg(self, msg):
        id_strs = [
            "file: %r" % self._instantiation_filename,
            "line: %d" % self._instantiation_lineno
            ]
        if self._name is not None:
            id_strs.append("name: %s" % self._name)
        print "*** %s%s (%s): %s" % (
            "  " * self.__depth,
            type(self).__name__,
            ", ".join(id_strs),
            msg
            )

    def print_traceback(self, child=None, t=None):
        if t is None:
            t = clock.now()
        if self._parent is None:
            print " SMILE Traceback:"
        else:
            self._parent.print_traceback(self, t)
        if self._name is None:
            name_spec = ""
        else:
            name_spec = " (%s)" % self._name
        def tstr(tm):
            if (isinstance(tm, dict) and
                len(tm) == 2 and
                "time" in tm and "error" in tm):
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
        print "   %s%s - file: %s, line: %d" % (
            type(self).__name__,
            name_spec,
            self._instantiation_filename,
            self._instantiation_lineno)
        for attr_name in self._log_attrs:
            value = val(getattr(self, attr_name))
            if attr_name.endswith("_time"):
                print "     %s: %s" % (attr_name, tstr(value))
            else:
                print "     %s: %r" % (attr_name, value)

    def claim_exceptions(self):
        if self._exp is not None:
            self._exp.current_state = self

    def get_log(self):
    	"""
        Evaluate all the log attributes and generate a dict.
        """
        
        keyvals = [(a,val(getattr(self,a))) if hasattr(self,a) 
                   else (a,None) for a in self._log_attrs]
        return dict(keyvals)

    def get_log_stream(self):
    	"""
    	Gets log stream for the current experiment
    	"""
        if self._exp is None:
            return None
        else:
            return self._exp.state_log_stream

    @property
    def current_clone(self):
        if ("_State__original_state" in self.__dict__ and
            "_State__most_recently_entered_clone" in self.__dict__):
            return self.__original_state.__most_recently_entered_clone
        else:
            return None

    def get_current_attribute_value(self, name):
        return getattr(self.current_clone, name)

    def __getattr__(self, name):
        internal_name = "_" + name
        if hasattr(self, internal_name):
            try:
                return self.__issued_refs[name]
            except KeyError:
                ref = Ref(self.get_current_attribute_value, internal_name)
                self.__issued_refs[name] = ref
                return ref
        else:
            return super(State, self).__getattribute__(name)

    def __setattr__(self, name, value):
        super(State, self).__setattr__(name, value)
        if name[0] != "_":
            return
        if name[:6] == "_init_":
            setattr(self, name[5:], None)
        if self.current_clone is not self:
            return
        try:
            ref = self.__issued_refs[name[1:]]
        except KeyError:
            return
        ref.dep_changed()

    def __dir__(self):
        lst = super(State, self).__dir__()
        return lst + self._log_attrs

    def get_parent_state_time(self):
    	"""
    	Returns state time for the parent. If no parent, logs current time. 
    	"""
        if self._parent:
            return self._parent._state_time
        else:
            return clock.now()

    def _enter(self):
        pass

    def enter(self):
        """
        Gets the starting time from the parent state
        """
        self.claim_exceptions()
        self._state_time = self.get_parent_state_time()
        self._start_time = self._state_time
        self._enter_time = clock.now()
        self._leave_time = None
        self._finalize_time = None
        self.__original_state.__most_recently_entered_clone = self

        # say we're active
        self._active = True
        self._following_may_run = False

        if self._parent:
            clock.schedule(partial(self._parent.child_enter_callback, self))

        # if we don't have the exp reference, get it now
        if self._exp is None:
            from experiment import Experiment
            self._exp = Experiment.last_instance()

        for name, value in self.__dict__.iteritems():
            if name[:6] == "_init_":
                setattr(self, name[5:], val(value))

        if self._duration is None:
            self._end_time = None
        else:
            self._end_time = self._start_time + self._duration

        # custom enter code
        self._enter()

        if self.__tracing:
            call_time = self._enter_time - self._exp.root_state._start_time
            call_duration = clock.now() - self._enter_time
            start_time = self._start_time - self._exp.root_state._start_time
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

        self.set_end_time()

        self._following_may_run = True
        if self._parent:
            clock.schedule(partial(self._parent.child_leave_callback, self))

        # call custom leave code
        self._leave()

        if self.__tracing:
            call_time = self._leave_time - self._exp.root_state._start_time
            call_duration = clock.now() - self._leave_time
            if self._end_time is None:
                 self.print_trace_msg(
                    "LEAVE time=%fs, duration=%fs, perpetual" %
                    (call_time, call_duration))
            else:
                end_time = self._end_time - self._exp.root_state._start_time
                self.print_trace_msg(
                    "LEAVE time=%fs, duration=%fs, end_time=%fs" %
                    (call_time, call_duration, end_time))

    def cancel(self, cancel_time):
        if self._active and not self._following_may_run:
            clock.schedule(self.leave, event_time=cancel_time)
            #QUESTION: Should this do anything in the base class at all?
            if self._end_time is None or cancel_time < self._end_time:
                self._end_time = cancel_time

    def finalize(self):  #TODO: call a _finalize method?
        if not self._active:
            return

        self._finalize_time = clock.now()
        self._active = False
        if self.__save_log:
            dump([self.get_log()],self.get_log_stream())
        if self._parent:
            clock.schedule(partial(self._parent.child_finalize_callback, self))
        if self.__tracing:
            call_time = self._finalize_time - self._exp.root_state._start_time
            call_duration = clock.now() - self._finalize_time
            self.print_trace_msg("FINALIZE time=%fs, duration=%fs" %
                                 (call_time, call_duration))

    def set_end_time(self):
        pass


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
                 save_log=True, name=None):
        super(ParentState, self).__init__(parent=parent,
                                          duration=duration,
                                          save_log=save_log,
                                          name=name)
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
    def __init__(self, children=None, parent=None, save_log=True, name=None):
        super(Parallel, self).__init__(children=children,
                                       parent=parent,
                                       save_log=save_log,
                                       name=name)
        self._children_blocking = []

        self.__my_children = []
        self.__blocking_children = []
        self.__remaining = set()
        self.__blocking_remaining = set()

    def print_traceback(self, child=None, t=None):
        super(Parallel, self).print_traceback(child, t)
        self._normalize_children_blocking()
        if child is not None:
            if self._children_blocking[self._children.index(child)]:
                print "     Blocking child..."
            else:
                print "     Non-blocking child..."

    def _normalize_children_blocking(self):
        for _n in range(len(self._children_blocking), len(self._children)):
            self._children_blocking.append(True)

    def set_child_blocking(self, n, blocking):
        self._normalize_children_blocking()
        self._children_blocking[n] = blocking

    def _enter(self):
        super(Parallel, self)._enter()
        self._normalize_children_blocking()
        self.__blocking_children = []
        self.__my_children = []
        if len(self._children):
            for child, blocking in zip(self._children, self._children_blocking):
                inactive_child = child.get_inactive_state(self)
                self.__my_children.append(inactive_child)
                if blocking:
                    self.__blocking_children.append(inactive_child)
                clock.schedule(inactive_child.enter)
            self.__remaining = set(self.__my_children)
            self.__blocking_remaining = set(self.__blocking_children)
        else:
            clock.schedule(self.leave)

    def child_leave_callback(self, child):
        super(Parallel, self).child_leave_callback(child)
        self.__remaining.discard(child)
        if len(self.__blocking_remaining):
            self.__blocking_remaining.discard(child)
            if not len(self.__blocking_remaining):
                self.set_end_time()
                if self._end_time is not None:
                    self.cancel(self._end_time)
        if not len(self.__remaining):
            self.leave()

    def cancel(self, cancel_time):
        if self._active:
            for child in self.__my_children:
                child.cancel(cancel_time)

    def set_end_time(self):
        if len(self.__blocking_children):
            end_times = [c._end_time for c in self.__blocking_children]
            if any([et is None for et in end_times]):
                self._end_time = None
            else:
                self._end_time = max(end_times)
        else:
            self._end_time = self._start_time


@contextmanager
def _ParallelWithPrevious(name=None, parallel_name=None):
    # get the exp reference
    from experiment import Experiment
    try:
        exp = Experiment.last_instance()
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
    with Parallel(name=parallel_name, parent=parallel_parent) as p:
        p.override_instantiation_context(3)
        p.claim_child(prev_state)
        with Serial(name=name) as s:
            s.override_instantiation_context(3)
            yield p


@contextmanager
def Meanwhile(name=None):
    with _ParallelWithPrevious(name=name, parallel_name="MEANWHILE") as p:
        yield p
    p.set_child_blocking(1, False)

@contextmanager
def UntilDone(name=None):
    with _ParallelWithPrevious(name=name, parallel_name="UNTILDONE") as p:
        yield p
    p.set_child_blocking(0, False)


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
            clock.schedule(self.__current_child.enter)
        except StopIteration:
            clock.schedule(self.leave)

    def child_enter_callback(self, child):
        super(Serial, self).child_enter_callback(child)
        if self.__cancel_time is not None:
            clock.schedule(partial(child.cancel, self.__cancel_time))

    def child_leave_callback(self, child):
        super(Serial, self).child_leave_callback(child)
        self._state_time = self.__current_child._end_time
        if self._state_time is None:
            self.leave()
        elif (self.__cancel_time is not None and
            self._state_time >= self.__cancel_time):
            self.leave()
        else:
            try:
                self.__current_child = (
                    self.__child_iterator.next().get_inactive_state(self))
                clock.schedule(self.__current_child.enter)
            except StopIteration:
                clock.schedule(self.leave)

    def cancel(self, cancel_time):
        if self._active:
            clock.schedule(partial(self.__current_child.cancel, cancel_time))
            self.__cancel_time = cancel_time

    def set_end_time(self):
        if self.__current_child is None:
            self._end_time = self._start_time
        else:
            self._end_time = self._state_time

    
class If(ParentState):
    def __init__(self, conditional, true_state=None, false_state=None, 
                 parent=None, save_log=True, name=None):

        # init the parent class
        super(If, self).__init__(parent=parent, save_log=save_log, name=name)

        # save a list of conds to be evaluated (last one always True, acts as the Else)
        self._init_cond = [conditional, True]
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
        self._log_attrs.append('cond')
        
    def _enter(self):
        super(If, self)._enter()

        self.__selected_child = (
            self._out_states[self._cond.index(True)].get_inactive_state(self))
        clock.schedule(self.__selected_child.enter)

    def child_leave_callback(self, child):
        super(If, self).child_leave_callback(child)
        self.leave()

    def __enter__(self):
        # push self.__true_state as current parent
        if not self._exp is None:
            self._exp._parents.append(self.__true_state)
        return self

    def cancel(self, cancel_time):
        if self._active:
            self.__selected_child.cancel(cancel_time)

    def set_end_time(self):
        if self.__selected_child is None:
            self._end_time = self._start_time
        else:
            self._end_time = self.__selected_child._end_time


class Elif(Serial):
    """State to attach an elif to and If state.

    """
    def __init__(self, conditional, parent=None, save_log=True, name=None):
        # init the parent class
        super(Elif, self).__init__(parent=parent, save_log=save_log, name=name)

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
        exp = Experiment.last_instance()
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
                 parent=None, save_log=True, name=None):
        super(Loop, self).__init__(parent=parent, save_log=save_log, name=name)

        if shuffle:
            self._init_iterable = ref.shuffle(iterable)
        else:
            self._init_iterable = iterable
        self._cond = conditional
        self._outcome = True

        self._i = None

        self.__body_state = Serial(parent=self, name="LOOP BODY")
        self.__body_state._instantiation_filename = self._instantiation_filename
        self.__body_state._instantiation_lineno = self._instantiation_lineno
        self.__current_child = None
        self.__cancel_time = None

        self._log_attrs.extend(['outcome', 'i'])

    def __current(self):
        loop = self.current_clone
        if loop._iterable is None or isinstance(loop._iterable, int):
            return loop._i
        else:
            return loop._iterable[loop._i]

    @property
    def current(self):
        return Ref(self.__current)

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
                # dump log
                dump([self.get_log()],self.get_log_stream())  #???

                yield i

    def _enter(self):
        # get the parent enter
        super(Loop, self)._enter()

        self._outcome = None
        self.__current_child = None
        self.__cancel_time = None
        self.__i_iterator = self.iter_i()
        self.start_next_iteration()

    def start_next_iteration(self):
        try:
            self._i = self.__i_iterator.next()
        except StopIteration:
            clock.schedule(self.leave)
            return
        self.__current_child = self.__body_state.get_inactive_state(self)
        clock.schedule(self.__current_child.enter)

    def child_enter_callback(self, child):
        super(Loop, self).child_enter_callback(child)
        if self.__cancel_time is not None:
            child.cancel(self.__cancel_time)

    def child_leave_callback(self, child):
        super(Loop, self).child_leave_callback(child)
        self._state_time = self.__current_child._end_time
        if self._state_time is None:
            self.leave()
        elif (self.__cancel_time is not None and
              self._state_time >= self.__cancel_time):
            self.leave()
        else:
            self.start_next_iteration()

    def cancel(self, cancel_time):
        if self._active:
            self.__current_child.cancel(cancel_time)
            self.__cancel_time = cancel_time

    def __enter__(self):
        # push self.__body_state as current parent
        if not self._exp is None:
            self._exp._parents.append(self.__body_state)
        return self

    def set_end_time(self):
        if self.__current_child is None:
            self._end_time = self._start_time
        else:
            self._end_time = self.__current_child._end_time


class Record(State):
    def __init__(self, duration=None, parent=None, save_log=False, name=None,
                 **kwargs):
        super(Record, self).__init__(parent=parent, 
                                     duration=duration, 
                                     save_log=save_log,
                                     name=name)

        self.__refs = kwargs

    def _enter(self):
        clock.schedule(self.leave, event_time=self._start_time)
        if self._end_time is not None:
            clock.schedule(self.finalize, event_time=self._end_time)

    def _leave(self):
        for name, ref in self.__refs.iteritems():
            self.record_change(name, ref)
            ref.add_change_callback(self.record_change, name, ref)

    def finalize(self):
        super(Record, self).finalize()
        for name, ref in self.__refs.iteritems():
            ref.remove_change_callback(self.record_change, name, ref)

    def record_change(self, name, ref):
        print "TODO: log value of ref %r: %r." % (name, val(ref))

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


class Wait(State):
    def __init__(self, duration=None, jitter=None, until=None, parent=None,
                 save_log=True, name=None):
        if duration is not None and jitter is not None:
            duration = ref.jitter(duration, jitter)

        # init the parent class
        super(Wait, self).__init__(parent=parent, 
                                   duration=duration, 
                                   save_log=save_log,
                                   name=name)

        self.__until = until  #TODO: make sure until is Ref or None
        self._until_value = None
        self._event_time = None

        self._log_attrs.extend(['until_value', 'event_time'])

    def _enter(self):
        self._event_time = None
        if self.__until is None:
            clock.schedule(self.leave, event_time=self._start_time)
            if self._end_time is not None:
                clock.schedule(self.finalize, event_time=self._end_time)
        else:
            self._until_value = self.__until.eval()
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
        self._until_value = self.__until.eval()
        if self._until_value:
            self._event_time = self._exp.app.event_time
            clock.schedule(partial(self.cancel, self._event_time["time"]))

    def cancel(self, cancel_time):
        if self._active:
            cancel_time = max(cancel_time, self._start_time)
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


class AutoFinalizeState(State):
    def leave(self):
        super(AutoFinalizeState, self).leave()
        clock.schedule(self.finalize)


class ResetClock(AutoFinalizeState):
    def __init__(self, new_time=None, parent=None, save_log=True, name=None):
        # init the parent class
        super(ResetClock, self).__init__(parent=parent,
                                         save_log=save_log,
                                         name=name)
        if new_time is None:
             self._init_new_time = Ref(clock.now, use_cache=False)
        else:
             self._init_new_time = new_time

    def _enter(self):
        clock.schedule(self.leave)

    def set_end_time(self):
        self._end_time = max(self._new_time, self._start_time)


class CallbackState(AutoFinalizeState):
    def __init__(self, repeat_interval=None, duration=0.0, parent=None,
                 save_log=True, name=None):
        super(CallbackState, self).__init__(duration=duration, parent=parent,
                                            save_log=save_log, name=name)
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
            name=kwargs.pop("name", None))

        # set up the state
        self._init_func = func
        self._init_pargs = pargs
        self._init_kwargs = kwargs
        self._result = None

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

    exp = Experiment()

    #with UntilDone():
    #    Wait(5.0)
    with Meanwhile():
        with Loop():
            Wait(5.0)
            Func(print_periodic)

    Debug(width=exp.screen.width, height=exp.screen.height)

    Set(foo=1)
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
            Wait(until=Get('foo')==5, name="wait until")
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
