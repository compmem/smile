=======================
What Are State Machines
=======================

What is A Hierarchical State Machine?
=====================================

A Hierarchical State Machine is a state machine that relies on both the input
and all the previous states' information in order to make a decision as to
which state to go to next. It takes context information from the previous
states and the input parameters of the current state in order to pick the next
state. Another property of a HSM is the parent-child relationship that some
states have.  In the traffic light example, the green state and the yellow
state could be children of the vehiclesGo state, as in when vehiclesGo enters
it would run green state followed by yellow state after a set time. This
parent-child relationship allows a HSM to give control of several different
states to a single parent, allowing for the running of several states at once
and a higher level of logical progression between states.

SMILE possesses both of these qualities. SMILE takes care of the linking of
children and parents by creating pythonic contexts and using the *with* keyword.
Back to the traffic light example, in SMILE you could create your own
ParentState called *vehiclesGo*. In your experiment you would write the
following lines to tell SMILE to treat the *green* and *yellow* states as
children to the *vehiclesGo* state.

::

    with vehiclesGo():
        green(duration = 10)
        yellow(duration = 3)
    red(duration = 14)

Using parental context in SMILE is that easy. SMILE also allows you to build
your experiments easier by compartmentalizing an experiment into 3 different
parts.  These parts are List Generation, Experimental Build Time, and
Experimental Run Time. By keeping your stimulus generation confined to the
List Generation part of your experiment code, you greatly simplify the logic
required to program your experiment. The **most important** idea to realize
about SMILE is the difference between *Experimental Build Time* and
*Experimental Run Time*.

.. _run_build_time:

Build Time V.S. Run Time
========================

The difference between **BT** and **RT** is the most important concept to
understand when learning to SMILE. The SMILE code that you type out in your
experiment is being run before the experiment even starts. There are 2 lines of
code that designate the start of **BT** and then the start of **RT**. Those
lines are `exp = Experiment()` and `exp.run()` respectively.

`exp = Experiment()` initializes your instance of an :py:class:`~smile.experiment.Experiment`. All calls to a
state must take place after this line in your code! Once this line is run,
**BT** starts.  **BT**, or Experimental Build Time, is the section of your
code that sets up how your experiment will run.

.. note::

    Any functions called in **BT** will not be run during **RT** unless run
    through the proper channel. See *Calling functions in RT*.

During Experimental Build Time, you are setting up all of the states in your
experiment by passing in the information they would need to run correctly.
Primarily these information are things like *duration* and *pos* or *x* and *y*
coordinates. Other information your states might need is the kind of stimulus
they are presenting. Typically, we store stimulus information in a list of
dictionaries to be looped over in a SMILE :py:class:`~smile.state.Loop` state, where each key of the
dictionary is a different piece of stimulus information that was generated
during the List Generation step.

In building your experiment, you may need access to a variable that isn't
available until the experiment is actually running. As an example, imagine that
you would like to create a :py:class:`~smile.video.Label` just 200 pixels to the left of the screen
center. The screen property of Experiment won't be initialized until
`exp.run()`, so we need a way to give :py:class:`~smile.video.Label` a placeholder variable that
points to `exp.screen.center_x - 200`. In order to do that, SMILE creates a
**reference**. Our reference to `exp.screen.center_x - 200` will be evaluated
during **RT**, making sure that our :py:class:`~smile.video.Label` has all of the information it needs
to run correctly.

During **RT** any calls to any functions that aren't the setting up of a state
will not be run during **RT**. In SMILE, if you would like a function to run
during **RT**, you need to utilize the :py:class:`~smile.state.Func` state. The :py:class:`~smile.state.Func` state will
create a call to a function and run that call at the correct place in the
experiment during **RT**.

Another thing to look out for when programming your experiment is the setting
and using of variables in **BT**. You cannot set a local variable in between
`exp = Experiment()` and `exp.run()` and expect it to actually set during
**RT**.  In order to *set* and *get* local variables during **RT**, you must
*set* and *get* them through your local :py:class:`~smile.experiment.Experiment` variable. Just like
setting any other variable, you just use the equal sign. The only difference is
you must add `exp.` to the beginning of your variable name. If you do this, it
creates a :py:class:`~smile.experiment.Set` in SMILE that will run in **RT**.  An example is as
follows.

::

    exp.variableName = lbl.appear_time['time']

For more information about setting in **RT** see the :ref:`Setting a Variable in RT <setting_in_rt>`
section of **Advanced SMILEing**

.. _ref_def:

What are References?
====================

The second most important things to understand about SMILE is how References
work. The definition of a SMILE reference is a variable whose value is to be
evaluated later. Without the *Reference* we would not be able to separate the
Experimental Build Time and Experimental Run Time as easily. A :py:class:`~smile.ref.Ref` is a
class that holds any kind of value from a function call and parameters to an
expression of several variables like `fu + bar - coocoo`. In relation to
expressions, References are recursive. Every Reference has a method called
:py:func:`~smile.ref.Ref.eval` which will attempt to evaluate the value of each part of the
expression. If one part of the expression is a Reference, then that Reference
will be recursively evaluated as well. If the Reference is to a list of values,
each value in the list will be evaluated. Same with any other list.

Another interesting thing a Reference can do is create a Reference object that
contains a conditional expression to be evaluated later. These are important
when building SMILE :py:class:`~smile.state.If` states. Say for instance you would like to present
"CONGRATS" if they answered in less than 3 seconds, but otherwise present
"NO GOOD BRO". You would need to rely on a Referenced conditional statement,
where `Ref.cond(cond, true_val, false_val)` can return any kind of object if
true or false. For an example, check the :py:class:`~smile.ref.Ref.cond` docstring.

References will also generate a list of their dependencies. For recursive
structures like References, there is a chance that they won't be able to be
evaluated. This will only happen if one of the dependencies is a
:py:class:`~smile.ref.NotAvailable` object. :py:class:`~smile.ref.NotAvailable` is the default value of a Reference
that isn't ready to be evaluated. During :py:class:`~smile.ref.Ref.eval`, if one of the dependencies
are :py:class:`~smile.ref.NotAvailable` your experiment will raise a :py:class:`~smile.ref.NotAvailableError`. If you
run into one of these errors while coding your experiment, the easiest way to
fix it is to create a :py:class:`~smile.state.Done` state.

A :py:class:`~smile.state.Done` state is a fancy state that will wait until the value of a reference
is made available.

.. warning::

    This state is not for regular use. Only use it if you encounter a
    NotAvailableError. If you misuse the *Done* state, your experiment will
    have hang-ups in the framerate or running of the experiment.

You shouldn't run into *NotAvaiableError*'s unless you are trying to time
a state based off the disappear time of something.

For more information about :py:class:`~smile.ref.Ref` and :py:class:`~smile.state.Func`
please see :ref:`Preforming Functions and Operations in RT <func_ref_def>`

