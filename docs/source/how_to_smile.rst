What is SMILE?
--------------

SMILE is a State Machine Interface Library for Experiments. In broad terms, a
state machine is an abstract device that stores the current status of relevant
input events, then initiates an action depending on a predetermined set of
rules. The goal of a state machine is to build objects that can be in many
possible states and to define the rules for transitioning from one of those
states to another. A common example used to describe a state machine is
a stoplight: in this case, the three possible states are a red state, a green
state, and a yellow state. There is a set order of cycling through these
states; specifically, red transition so green, green transitions to yellow, and
yellow cycles back to red.

The goal of SMILE was to create an easy to use State Machine Interface where
the hardest part about coding an experiment would be the stimulus list
generation. Through SMILE, we have developed a state machine interface between
the experimenter and Kivy, a python library that specializes in creating and
displaying stimulus on the screen in the form of widgets. With Smile, you are
able to build a Psychology experiment without the hassle of handling any of the
timing, the logging of data, or the presenting of stimulus. SMILE is concidered
to be a hierarchical state machine.  This is because all of the states in
SMILE have a parent-child relationship that comes into play when dealing with
the timing of multiple states at the same time.

What is A Hierarchical State Machine?
-------------------------------------
A Hierarchical State Machine is a state machine that relies on both the input
and all the previous states' information in order to make a decition as to
which state to go to next. It takes context information from the previous
states and the input parameters of the current state in order to pick the next
state. Another property of a HSM is the parent-child relationship that some
states have.  In the traffic light example, the green state and the yellow
state could be children of the vehicalsGO state, as in when vehicalsGo enters
it would run green state followed by yellow state after a set time. This
parent-child relationship allows a HSM to give control of serveral different
states to a single parent, allowing for the running of several states at once
and a higher level of logical progression between states.

SMILE posesses both of these qualities. SMILE makes takes care of the linking
of children and parents by creating pythonic contexts and the *with* keyword.
Back to the Traffic light example, in SMILE you could create your own
ParentState called *vehicalsGo*. In your experiment you would write the
following lines to tell SMILE to treat the *green* and *yellow* states as
children to the *vehicalsGo* state.

::

    with vehicalsGo():
        green(duration = 10)
        yellow(duration = 3)
    red(duration = 14)

Using parental context in SMILE is that easy. SMILE also allows you to build
your experiments easier by compartimentalizing an experiment into 3 different
parts.  These parts are List Generation, Experimental Build Time, and
Experimental Runtime. By keeping your stimulus generation confinde to the
List Generation part of your experiment code, you greatly simplify the logic
required to program your experiment. The **most important** idea to realize
about SMILE is the difference between *Experimental Build Time* and
*Experimental Runtime*.

Experimental Build Time V.S. Runtime
------------------------------------
The difference bewteen **EBT** and **ER** is the most important concept to
understand when learning to SMILE. The SMILE code that you type out in your
experiment is being run before the experiment even starts. There are 2 lines of
code that designate the state of **EBT** and then the start of **ER**. Those
lines are *exp = Experiment()* and *exp.run()*.

*exp = Experiment()* initializes your instance of an Experiment. All calls to a
state must take place after this line in your code! Once this line is ran,
**EBT** starts.  **EBT**, or Experimental Build Time, is the section of your
code that sets up how your experiment will run.

.. note::

    Any functions called in **EBT** will not be run during **ER** unless ran
    through the proper channel. See *Calling functions in ER*.

During Experimental Build Time, you are setting up all of the states in your
experiment by passing in the information they would need to run correctly.
Primarily these information are things like *duration* and *pos* or *x* and *y*
coordinates. Other information your states might need is the kind of stimulus
they are presenting. Typically, we store stimulus information in a list of
dictionaries to be looped over in a smaile *Loop* state, where each key of the
dictionary is a different piece of stimulus information that was generated
during the List Generation step.

In building your experiment, you may need access to variable that isn't
available until the experiment is actually running. As an example, imagine that
you would like to create a *Label* just 200 pixles to the left of the screen
center. The screen property of Experiment won't be initialized until
*exp.run()*, so we need a way to give *Label* a placeholder variable that
points to *exp.screen.center_x - 200*. In order to do that, SMILE creates a
**reference**. Our reference to *exp.screen.center_x - 200* will be evaluated
during **ER**, making sure that our *Label* has all of the information it needs
to run correctly.

During **EBT** any calls to any functions that aren't the setting up of a state
will not be run during **ER**. In SMILE, if you would like a function to run
during **ER**, you need to utilize the *Func* state. The *Func* state will
create a call to a function and run that call at the correct place in the
experiment during **ER**.

Another thing to look out for when programming your experiment is the setting
and using of variables in **EBT**. You cannot set a local variable in between
*exp = Experiment()* and *exp.run()* and expect it to actually set during
**ER**.  In order to *set* and *get* local variables during **ER**, you must
*set* and *get* them through your local **Experiment** variable. Just like
setting any other variable, you just use the equal sign. The only difference is
you must add *exp.* to the beginning of your variable name. If you do this, it
creates an UpdateState in SMILE that will run in **ER**.  An example is as
follows

::

    exp.variableName = lbl.appear_time['time']

What are References?
--------------------
The second most important things to understand about SMILE are how References
work. The definition of a SMILE reference is a variable whoes value is to be
evaluated later. Without the *Reference* we would not be able to seperate the
Experimental Build Time and Experimental Runtime as easily. A Reference is a
class that holds any kind of value from a function call and parameters to an
expression of several variables like *fu + bar - coocoo*. In relation to
expressions, References are recursive. Every Reference has a method called
**.eval** which will attempt to evaluate the value of each part of the
expression. If one part of the experession is a Reference, then that Reference
will be recursively evaluated aswell. If the Reference is to a List of values,
each value in the list will be evaluated. Same with any other listlike.

Another interesting thing a Reference can do is create a Reference object that
contains a conditional expression to be evaluated later. These are important
when building SMILE *If* states. Say for instance you would like to present
"CONGRATS" if they answered in less than 3 seconds, but otherwise present
"NO GOOD BRO". You would need to rely on a Referenced conditional statement,
where **Ref.cond(cond, true_val, false_val)* can return any kind of object if
true or false. For an example, check the *Ref.cond* docstring.

References will also generate a list of their dependencies. For recursive
structures like References, there is a chance that they won't be able to be
evaluated. This will only happen if one of the dependencies is a
*NotAvailable* object. **NotAvailable** is the default value of a Reference
that isn't ready to be evaluated. During *Ref.eval*, if one of the dependencies
are *NotAvailabe* your experiment will raise a **NotAvailableError**. If you
run into one of these errors while coding your experiment, the easiest way to
fix it is to create a *Done* state.

A **Done** state is a fancy state that will wait until the value of a reference
is made available.

.. warning::

    This state is not for regular use. Only use it if you encounter a
    NotAvailableError. If you misuse the *Done* state, your experiment will
    have hangups in the framerate or running of the experiment.

You shouldn't run into *NotAvaiableError*'s unless you are trying to time
a state based off the disappear time of something.

