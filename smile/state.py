#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from pyglet import clock
now = clock._default.time
import random

from ref import Ref, val
from utils import rindex, get_class_name
from log import dump

# custom schedule functions (add delays)
def _schedule_interval_callback(dt, func, interval, *args, **kwargs):
    """
    Schedule a callback with specified interval.
    
    Parameters
    ----------
    dt : float
        The number of seconds since the last function call.
    func : function
        The function to call when the timer lapses.
    interval : float
    	The number of seconds to wait between each call
    
    Example
    -------
    
    _schedule_interval_callback(dt, function, 1.0)
    	The function will be called one second after it
    	was last called.

    """
    # schedule it
    if interval > 0:
        clock.schedule_interval(func, interval, *args, **kwargs)
    # call it
    func(dt, *args, **kwargs)

def schedule_delayed_interval(func, delay, interval, *args, **kwargs):
    """
    Schedule a callback with specified interval to begin after the
    specified delay.
    
    Parameters
    ----------
    func : function
        The function to call when the timer lapses.
    delay : float
    	The number of seconds after the interval before the function
    	begins.
    interval : float
    	The number of seconds to wait between each call
    
    Example
    -------
    schedule_delayed_interval(function, 2.0, 1.0)
    	The function will be called every second starting after 
        2 seconds

    """
    clock.schedule_once(_schedule_interval_callback, delay, func, interval, *args, **kwargs)
    
def _schedule_callback(dt, func, *args, **kwargs):
    """
    Schedule a callback to occur every event loop with no delay or interval
    
    Parameters
    ----------
    dt: float
        The number of seconds since the last function call.
    func:function
        The function to call when the timer lapses.

    Example
    -------    
    _schedule_callback(dt, function)
    	The function will be called immediately after the previous
    	event loop
    	
    """
    # schedule it
    clock.schedule(func, *args, **kwargs)
    # call it
    func(dt, *args, **kwargs)

def schedule_delayed(func, delay, *args, **kwargs):
    """
    Schedule a callback to occur every event loop after the specified
    initial delay.
    
    Parameters
    ----------
    func:function
        The function to call when the timer lapses.
    delay: float
    	The number of seconds after the interval before the function
    	begins.
    	
    Example
    -------    
    schedule_delay(function, 3.0)
    	The function will be called on every loop starting 
        after 3.0 seconds.    	
    """
    clock.schedule_once(_schedule_callback, delay, func, *args, **kwargs)


class RunOnEnter():
    """Inherited class to indicate to a state that it should run
    immediately upon entering the state (instead of waiting until the
    state time specified by the parent). This ensures that parent
    states do not disturb the timing of their children.
    """
    pass


class State(object):
    """
    Base State object for the hierarchical state machine.

    Provides framework for entering, processing, and leaving states.

    Subclasses can customize behavior by implementing the _enter,
    _callback, and _leave methods.

    Parameters
    ----------
    interval : {0, -1, float}
        The number of seconds between each call, 0 means once, 
        -1 means every frame.
    parent : {None, ``ParentState``}
        Parent state to attach to. Will search for experiment if None.
    duration : {0.0, float}
        Duration of the state.
    save_log : bool
        Whether the state logs itself.
    
    """
    def __init__(self, interval=0, parent=None, duration=0.0, 
                 save_log=True):
        """
        """
        self.state_time = None
        self.start_time = None
        self.end_time = None
        self.first_call_time = None
        self.first_call_error = None
        self.last_call_time = None
        self.last_call_error = None
        self.dt = None
        self.interval = interval
        self.raw_duration = duration
        self.duration = 0.0
        self.parent = parent
        self.active = False
        self.done = False
        self.save_log = save_log

        # get the exp reference
        from experiment import Experiment
        try:
            self.exp = Experiment.last_instance()
        except AttributeError:
            self.exp = None

        # try and set the current parent
        if self.parent is None and not self.exp is None:
            # try and get it from the exp
            self.parent = self.exp._parents[-1]

        # add self to children if we have a parent
        if self.parent:
            # append to children
            self.parent.children.append(self)

        # start the log
        self.state = self.__class__.__name__
        self.log_attrs = ['state','state_time','start_time','end_time',
                          'first_call_time','first_call_error',
                          'last_call_time','last_call_error',
                          'duration']

    def get_log(self):
    	"""
        Evaluate all the log attributes and generate a dict.
        """
        
        keyvals = [(a,val(getattr(self,a))) if hasattr(self,a) 
                   else (a,None) for a in self.log_attrs]
        return dict(keyvals)

    def get_log_stream(self):
    	"""
    	Gets log stream for the current experiment
    	"""
        if self.exp is None:
            return None
        else:
            return self.exp.state_log_stream
        
    def __getitem__(self, index):
    	"""
    	Returns a reference object for the specified attribute.
    	"""
        if hasattr(self, index):
            return Ref(self, index)
        else:
            class_name = get_class_name(self)[0]
            raise ValueError('%s state does not have attribute "%s".' % 
                             (class_name, index))

    # PBS: Must eventually check for specific attrs for this to work
    #def __getattribute__(self, name):
    #    return Ref(self, name)

    def _callback(self, dt):
        # Subclasses of State must implement the callback.
        pass
        
    def callback(self, dt):
    	"""
    	Run at the scheduled state time.
    	"""

        self.last_call_time = now()
        self.last_call_error = self.last_call_time - self.state_time
        if self.first_call_time is None:
            self.first_call_time = self.last_call_time
            self.first_call_error = self.last_call_error

        # call the user-defined callback
        self._callback(dt)

        # save the dt
        self.dt = dt

        # see if done (check to make sure we didn't already call leave)
        if not self.done and self.interval == 0:
            # we're done
            self.leave()

    def get_parent_state_time(self):
    	"""
    	Returns state time for the parent. If no parent, logs current time. 
    	"""
        if self.parent:
            return self.parent.get_state_time()
        else:
            return now()

    def advance_parent_state_time(self, duration):
        if self.parent:
            self.parent.advance_state_time(duration)

    def _enter(self):
        pass

    def enter(self):
        """
        Gets the starting time from the parent state
        """
        
        self.state_time = self.get_parent_state_time()
        self.start_time = self.state_time

        # add the callback to the schedule
        delay = self.state_time - now()
        if delay < 0 or issubclass(self.__class__,RunOnEnter):
            # parents states (and states like Logging) run immediately
            delay = 0
        if self.interval < 0:
            # schedule it for every event loop
            schedule_delayed(self.callback, delay)
        else:
            # schedule the interval (0 means once)
            schedule_delayed_interval(self.callback, delay, self.interval)

        # say we're active
        self.active = True

        # if we don't have the exp reference, get it now
        if self.exp is None:
            from experiment import Experiment
            self.exp = Experiment.last_instance()

        # compute the duration
        self.duration = val(self.raw_duration)
            
        # custom enter code
        self._enter()

        # update the parent time if necessary
        # moved to after _enter in case we update duration
        if self.duration > 0:
            self.advance_parent_state_time(self.duration)

        pass

    def _leave(self):
        pass

    def leave(self):
        """
        Gets the end time of the state (logs current time)
        """
        
        self.end_time = now()
        
        # update the parent state time to actual elapsed time if necessary
        if self.duration < 0:
            if issubclass(self.__class__,ParentState): #isinstance(self, ParentState):
                # advance the duration the children moved the this parent
                duration = self.state_time-self.start_time
            else:
                # advance the duration of this state
                duration = self.end_time-self.start_time
            self.advance_parent_state_time(duration)

        # remove the callback from the schedule
        clock.unschedule(self.callback)

        # notify the parent that we're done
        self.active = False
        self.done = True
        if self.parent:
            self.parent.check = True

        # call custom leave code
        self._leave()

        # write log to the state log
        #print self.get_log()
        if self.save_log:
            dump([self.get_log()],self.get_log_stream())
        pass
    

class ParentState(State, RunOnEnter):
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
    def __init__(self, children=None, parent=None, duration=-1, save_log=True):
        super(ParentState, self).__init__(interval=-1, parent=parent, 
                                          duration=duration, 
                                          save_log=save_log)
        # process children
        if children is None:
            children = []
        self.children = []
        for c in children:
            self.claim_child(c)
        
        self.check = False

    def get_state_time(self):
        return self.state_time

    def advance_state_time(self, duration):
        self.state_time += duration

    def claim_child(self, child):
        if not child.parent is None:
            ind = rindex(child.parent.children,child)
            del child.parent.children[ind]
        child.parent = self
        self.children.append(child)

    def _enter(self):
        # set all children to not done
        for c in self.children:
            c.done = False
        self.check = True
        self._advanced = 0 # for Parallel children

    def __enter__(self):
        # push self as current parent
        if not self.exp is None:
            self.exp._parents.append(self)
        return self

    def __exit__(self, type, value, tb):
        # pop self off
        if not self.exp is None:
            state = self.exp._parents.pop()
        pass


class Parallel(ParentState):
    """
    Parent state that runs its children in parallel.

    A Parallel Parent State is done when all its children have
    finished.
    
    """        
    def _callback(self, dt):
        if self.check:
            self.check = False
            # process the children
            # start those that are not active and not done
            num_done = 0
            for c in self.children:
                if c.done:
                    num_done += 1
                    continue
                if not c.active:
                    c.enter()
            if num_done == len(self.children):
                # we're done
                #self.interval = 0
                # advance the state_time
                self.state_time += self._advanced
                self.leave()
        pass

    def advance_state_time(self, duration):
        # advance the longest duration
        to_advance = duration - self._advanced
        if to_advance > 0:
            #self.state_time += to_advance
            self._advanced += to_advance


class Serial(ParentState):
    """Parent state that runs its children in serial.

    A Serial Parent State is done when the last state in the chain is
    finished.
    
    """
    def _callback(self, dt):
        if self.check:
            self.check = False
            # process the children
            # start those that are not active and not done
            num_done = 0
            for i,c in enumerate(self.children):
                if c.done:
                    num_done += 1
                    continue
                if not c.active:
                    if i > 0 and \
                            not self.children[i-1].done and \
                            self.children[i-1].duration < 0:
                        # we have to wait until it's done
                        break

                    # start the next one
                    c.enter()
                    break

            if num_done == len(self.children):
                # we're done
                #self.interval = 0
                self.leave()
        pass

    
class If(ParentState):
    """
    Parent state to implement conditional branching. If state is used in lieu
    of a traditional Python if statement.
    
    Creates true and false states based on a specified conditional.
    
    Parameters
    ----------
    conditional: bool
    	Boolean statement that determines a true and false state
    true_state: object
    	State to enter if conditional evaluates to True
    false_state: object
    	State to enter if conditional evaluates to False
    parent: object
    	The parent state containing the If object
    save_log: bool
    	If set to 'True,' details about the If state will be automatically saved 
    	in the log files.
    
    Examples
    --------
    key = KeyResponse(['Y','N'])
    If((key['rt']>2.0)&(key['resp'] != None), stateA, stateB)
    
    State A is entered if conditional evaluates to True
    State B is entered if conditional evaluates to False

    True and false states are automatically created if they are not
    passed in.  This allows for the more natural use of the If state 
    as follows:

    with If((key['rt']>2.0)&(key['resp'] != None)):
        # fill the true state
        pass
    with Else():
        # fill the false state
        pass
    
    Log Parameters
    --------------
    outcome : outcome of the conditional evaluation. Appended to state.yaml
        and state.csv

    """
    def __init__(self, conditional, true_state=None, false_state=None, 
                 parent=None, save_log=True):

        # init the parent class
        super(If, self).__init__(parent=parent, duration=-1, 
                                 save_log=save_log)

        # save a list of conds to be evaluated (last one always True, acts as the Else)
        self.cond = [conditional, True]
        self.outcome = None
        self.true_state = true_state
        self.false_state = false_state

        if self.true_state:
            # make sure to set this as the parent of the true state
            self.claim_child(self.true_state)
        else:
            # create the true state
            self.true_state = Serial(parent=self)

        # process the false state similarly
        if self.false_state:
            self.claim_child(self.false_state)
        else:
            # create the true state
            self.false_state = Serial(parent=self)

        # save the out_states
        self.out_states = [self.true_state, self.false_state]
        
        # append outcome to log
        self.log_attrs.append('outcome')
        
    def _enter(self):
        # reset outcome so we re-evaluate if called in loop
        # this will evaluate each conditional, we'll enter the first one that
        # evaluates to True. Note that the last one is always True because it's
        # the Else
        # must evaluate each cond
        self.outcome = [not v is False for v in val(self.cond)]
        super(If, self)._enter()
        
    def _callback(self, dt):
        if self.check:
            self.check = False
            done = False

            # process the outcome
            # if self.outcome:
            #     # get the first state
            #     c = self.true_state
            # else:
            #     c = self.false_state
                
            # take the first one that evaluated to True
            c = self.out_states[self.outcome.index(True)]
            
            if c is None or c.done:
                done = True
            elif not c.active:
                # start the winning state
                c.enter()

            # check if done
            if done:
                #self.interval = 0
                self.leave()

    def __enter__(self):
        # push self.true_state as current parent
        if not self.exp is None:
            self.exp._parents.append(self.true_state)
        return self


class Elif(Serial):
    """State to attach an elif to and If state.

    """
    def __init__(self, conditional, parent=None, save_log=True):

        # init the parent class
        super(Elif, self).__init__(parent=parent, duration=-1, 
                                   save_log=save_log)

        # we now know our parent, so ensure the previous child is
        # either and If or Elif state
        if self.parent is None:
            raise ValueError("The parent can not be None.")

        # grab the previous child (-2 because we are -1)
        prev_state = self.parent.children[-2]
        if not isinstance(prev_state, If):
            raise ValueError("The previous state must be an If or Elif state.")

        # have that previous If state grab this one
        prev_state.claim_child(self)

        # insert the conditional and state
        prev_state.cond.insert(-1, conditional)
        prev_state.out_states.insert(-1, self)

        
def Else():
    """State to attach to the else of an If state.

    """

    # get the exp reference
    from experiment import Experiment
    try:
        exp = Experiment.last_instance()
    except AttributeError:
        raise AttributeError("You must first instantiate an Experiment.")

    # find the parent
    parent = exp._parents[-1]

    # find the previous child state (-1 because this is not a state)
    prev_state = parent.children[-1]
    
    # make sure it's the If
    if not isinstance(prev_state, If):
        raise ValueError("The previous state must be an If or Elif state.")

    # return the false_state (the last out_state)
    return prev_state.out_states[-1]

    
class Loop(Serial):
    """State that implements a loop.

    Loop over an iterable or run repeatedly while a conditional 
    evaluates to True. Loop is used in similar fashion to for 
    and while statements in Python.

    Parameters
    ----------
    iterable : object
    	Process to iterate through while a conditional evaluates to True
    shuffle : bool
        Whether to shuffle the iterable before the loop. Note that this will
        only work for iterables and will evaluate and make a shallow copy
        of the iterable in order to shuffle it.
    conditional : bool,Ref
    	Object that evaluates to a bool to determine whether to continue
    parent : object
    	The parent state
    save_log : bool
    	If set to 'True,' details about the If state will be automatically saved 
    	in the log files.

    Properties
    ----------
    i : int
        Iteration of the loop
    current : obj
        Current value of the iterable
    
    Example
    -------
    block = [{'image':'cow.jpg'},{'image':'octopus.jpg'}]
    with Loop(block) as trial:
        Show(Image(trial.current['image']), 2.0)
        Wait(.5)
    
    The Loop will iterate over the list of dictionaries, showing an
    image from trial.current for 2.0 seconds, unshow it, and wait for
    0.5 seconds. The Loop will continue to iterate over the list,
    running the Show and Wait states, until all the items from the
    list are traversed.

    """
    def __init__(self, iterable=None, shuffle=False,
                 conditional=True,
                 parent=None, save_log=True):
        super(Loop, self).__init__(parent=parent, duration=-1, 
                                   save_log=save_log)

        # otherwise, assume it's a list of dicts
        self.iterable = iterable
        self.shuffle = shuffle
        self.cond = conditional
        self.outcome = True

        # set to first in loop
        self.i = 0
        self._shuffled = False
                    
        # append outcome to log
        self.log_attrs.extend(['outcome','i'])

    @property
    def current(self):
        if self.iterable is None:
            return None # could possibly return self.i here
        else:
            return self['iterable'][self['i']]

    def _enter(self):
        # get the parent enter
        super(Loop, self)._enter()

        # reset outcome so we re-evaluate if called in loop
        self.outcome = val(self.cond)

        # see if shuffle
        if not self.iterable is None and \
           val(self.shuffle) and \
           not self._shuffled:
            # eval and make a shallow copy
            self.iterable = val(self.iterable, recurse=False)[:]
            random.shuffle(self.iterable)
            self._shuffled = True

    def _callback(self, dt):
        if self.check:
            self.check = False
            # check the outcome each time
            if not self.outcome:
                # we should stop now
                #self.interval = 0
                self.leave()
                return
                
            # process the children            
            # start those that are not active and not done
            num_done = 0
            for i,c in enumerate(self.children):
                if c.done:
                    num_done += 1
                    continue
                if not c.active:
                    if i > 0 and \
                            not self.children[i-1].done and \
                            self.children[i-1].duration < 0:
                        # we have to wait until it's done
                        break

                    # start the next one
                    c.enter()
                    break

            if num_done == len(self.children):
                # we're done with this sequence
                finished = False
                if not self.iterable is None:
                    # see if we're done with the loop
                    if self.i+1 >= len(val(self.iterable,recurse=False)):
                        # we're really done
                        finished = True
                        self.leave()
                        # reset to start if inside another loop
                        self.i = 0
                        self._shuffled = False
                    else:
                        # dump log
                        dump([self.get_log()],self.get_log_stream())

                        # set to next
                        self.i += 1
                else:
                    # conditional looping so just set to next
                    self.i += 1
                        
                # update everything for the next loop
                if not finished:
                    self._enter()
                    
        pass


class Wait(State):
    """
    State that will wait a specified time in seconds.  It is possible
    to keep the state active or simply move the parent's state time
    ahead.
    
    Parameters
    ----------
    duration: float
    	Time in seconds to remain in the wait state
    jitter: float
    	Creates the upper bound of a uniform distribution from which a jitter
    	is randomly drawn each time Wait is executed. The uniform distribution
    	takes the lower and upper bounds of (duration, duration + jitter)
    stay_active: bool
    	Determines whether the Wait state remains active, based on current time
    	compared with the duration parameter
    parent: object
    	The parent state    
    save_log: bool
    	If set to 'True,' details about the Wait state will be automatically saved 
    	in the log files.	
    
    Example
    -------
    Wait(2.0, 1.0)
    	The state will wait for a duration drawn from a uniform distribution with range
    	(2.0, 3.0)
    
    """
    def __init__(self, duration=0.0, jitter=0.0, stay_active=False, 
                 parent=None, save_log=True):
        # init the parent class
        super(Wait, self).__init__(interval=-1, parent=parent, 
                                   duration=duration, 
                                   save_log=save_log)
        self.stay_active = stay_active
        self.jitter = jitter
        self.wait_duration = duration

    def _enter(self):
        # get the parent enter
        super(Wait, self)._enter()

        # set the duration
        self.duration = random.uniform(val(self.wait_duration),
                                       val(self.wait_duration)+val(self.jitter))

    def _callback(self, dt):
        if not self.stay_active or now() >= self.state_time+self.duration:
            # we're done
            #self.interval = 0
            self.leave()


class ResetClock(State, RunOnEnter):
    """
    State that will reset the clock of its parent to a specific time
    (or now if not specified).
    
    Parameters
    ----------
    new_time: float
        New time to reset the clock of the parent state
    parent: object
        The parent state
    save_log: bool
    	If set to 'True,' details about the ResetClock state will be automatically saved 
    	in the log files.
    Examples
    --------
    ResetClock()
    
    Will reset the time of the parent state to now.
    """
    
    def __init__(self, new_time=None, parent=None, save_log=True):
        # init the parent class
        super(ResetClock, self).__init__(interval=0, parent=parent, 
                                         duration=0, 
                                         save_log=save_log)
        if new_time is None:
            # eval to now if nothing specified
            new_time = Ref(gfunc=lambda:now())
        self.new_time = new_time

    def _callback(self, dt):
        duration = val(self.new_time) - self.get_parent_state_time()
        if duration > 0:
            self.advance_parent_state_time(duration)
    

class Func(State):
    """
    State that will call a Python function, passing this state as the
    first argument.
    
    Parameters
    ----------
    func: function
        A python function to be applied to the State
    interval: float
        The number of seconds to wait between each call of the python function
    duration: float
        Duration of the parent state. An interval of 0 means enter the state once, 
        -1 means every frame. Defaults to 0
    parent: object
        The parent state
    save_log: bool
        If set to 'True,' details about the ResetClock state will be automatically saved 
        in the log files.
    
    Example
    -------
    Func(str(), StateA)
    Calls python function str(), converting the output of StateA into a string
    	
    """
    def __init__(self, func, args=None, kwargs=None, 
                 interval=0, parent=None, duration=0.0, 
                 save_log=True):
        # init the parent class
        super(Func, self).__init__(interval=interval, parent=parent, 
                                   duration=duration, 
                                   save_log=save_log)

        # set up the state
        self.func = func
        self.args = args
        if self.args is None:
            self.args = []
        self.kwargs = kwargs
        if self.kwargs is None:
            self.kwargs = {}

    def _callback(self, dt):
        # process the refs
        args = val(self.args)
        kwargs = val(self.kwargs)
        self.res = self.func(self, *args, **kwargs)
    

class Debug(State):
    """
    Evaluate the specified kwargs and print them to standard out.

    Useful for debugging a state machine as the name implies.
    
    Parameters
    ----------
    parent: object
    	The parent state
    save_log: bool
    	If set to 'True,' details about the Debug state will be automatically saved 
    	in the log files.
    kwargs : dict
        key, value pairs to be evaluated and printed to stdout
    
    Example
    -------
    Print out the show time of a Show state:
        Debug(show_time=txt['show_time'])

    """
    def __init__(self, parent=None, save_log=False, **kwargs):
        # init the parent class
        super(Debug, self).__init__(interval=0, parent=parent, 
                                   duration=0, 
                                   save_log=save_log)

        # set up the state
        self.kwargs = kwargs

    def _callback(self, dt):
        # process the refs
        #kwargs = {key: val(value) for (key, value) in self.kwargs}
        print 'DEBUG:', val(self.kwargs)


if __name__ == '__main__':

    from experiment import Experiment, Set, Get

    def print_dt(state, *txt):
        print txt, now()-state.state_time, state.dt

    exp = Experiment()

    Debug(width=exp['window'].width, height=exp['window'].height)

    with Loop(range(10)) as loop:
        with If(loop.current > 6):
            Func(print_dt, args=["True"])
        with Elif(loop.current > 4):
            Func(print_dt, args=["Trueish"])
        with Elif(loop.current > 2):
            Func(print_dt, args=["Falsish"])
        with Else():
            Func(print_dt, args=["False"])

    # with implied parents
    block = [{'val':i} for i in range(3)]
    Set('not_done',True)
    with Loop(conditional=Get('not_done')) as outer:
        Debug(i=outer['i'])
        with Loop(block, shuffle=True) as trial:
            Func(print_dt, args=[trial.current['val']])
            Wait(1.0)
            If(trial.current['val']==block[-1],
               Wait(2.))
        If(outer['i']>=3,Set('not_done',False))
        
    block = range(3)
    with Loop(block) as trial:
        Func(print_dt, args=[trial.current])
        Wait(1.0)
        If(trial.current==block[-1],
           Wait(2.))


    If(True, 
       Func(print_dt, args=["True"]),
       Func(print_dt, args=["False"]))
    Wait(1.0)
    If(False, 
       Func(print_dt, args=["True"]),
       Func(print_dt, args=["False"]))
    Wait(2.0)
    If(False, Func(print_dt, args=["True"])) # won't do anything
    Func(print_dt, args=["two"])
    Wait(3.0)
    with Parallel():
        with Serial():
            Wait(1.0)
            Func(print_dt, args=['three'])
        Func(print_dt, args=['four'])
    Wait(2.0)

    block = [{'text':'a'},{'text':'b'},{'text':'c'}]
    with Loop(block) as trial:
        Func(print_dt, args=[trial.current['text']])
        Wait(1.0)
        
    Wait(2.0, stay_active=True)

    exp.run()


    # # with explicit parents
    # If(True, 
    #    Func(print_dt, args=["True"], interval=0.0),
    #    Func(print_dt, args=["False"], interval=0.0),
    #    parent=exp)
    # Wait(1.0, parent=exp)
    # If(False, 
    #    Func(print_dt, args=["True"], interval=0.0),
    #    Func(print_dt, args=["False"], interval=0.0),
    #    parent=exp)
    # Wait(2.0, parent=exp)
    # Func(print_dt, args=["two"], interval=0.0, parent=exp)
    # Wait(3.0, parent=exp)
    # with Parallel(parent=exp) as trial:
    #     with Serial(parent=trial) as x:
    #         Wait(1.0, parent=x)
    #         Func(print_dt, args=['three'], interval=0.0, parent=x)
    #     Func(print_dt, args=['four'], interval=0.0, parent=trial)
    #     print trial.children
    # Wait(2.0, stay_active=True, parent=exp)

    
    pass

