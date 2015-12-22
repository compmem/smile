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

The states of a State
---------------------
Every state in SMILE runs through 6 main function calls. These function calls
are automatic and never need to be called by the end user, but it is important
to understand what they do and when they do it to fully understand SMILE.
These function calls are *__init__*, *.enter()*, *.start()*, *.end()*,
*.leave()*, and *.finalize()*. Each of these calls happen at different parts of
the experiment, and have different functions depending on the subclass.

*.__init__* happens during **EBT** and is the only one to happen at **EBT**.
This function usually sets up all of the references, proccesses some of the
parameters, and knows what to do if a parameter is missing or wasn't passed in.

*.enter()* happens during **ER** and will be called after the previous state
calls *.leave()*. This function will evaluate all of the parameters that were
references, and set all the values of the remaining parameter. It will also
schedule a start time for this state.

*.start()* is a class of function calls that, during **ER**, the state starts
doing whatever makes it special. this function is not always called *.start()*.
In the case of an *Image* state, *.start()* is replaced with *.appear()*. The
*.start()* functions could do anything from showing an image to recording a
keypress. After *.start()* this state will begin actually performing its
main function.

*.end()* is a class of function calls that, during **ER**, ends whatever makes
the state special. In the case of an Image, *.end()* is replaced with
*.disapper()*. After *.end()*, *.leave()* is available to be called.

*.leave()* happends during **ER** and will be called whenever the duration of
a state is over, or whenever the rules of a state says it should end. A special
case for this is the *.cancel()* call. If a state should need to be ended early
for whatever reason, the *Experiment* will call the state's *.cancel()* method
and that method will setup a call to both *.leave()* and *.finalize()*.

*.finailize()* happens during **ER** but not until after a state has left.
This call usually happens during *Wait* states or whenever the clock has extra
time. This call will save out the logs, setup callbacks to the *ParentState* to
tell it that this state has finished, and set *self.active* to false. This call
is used to clean up things at after the state has ran *.leave()* but not
immediately afterword, just whenever the clock has extra time to preform this
call.

The Flow States of SMILE
------------------------
One of the basic types of SMILE states are the **Flow** states.  **Flow**
states are states that control the flow of your experiment. The basic **Flow**
state that all SMILE experiments are in is the *Serial* state.

Serial State
============
A *Serial* state is a state that has children, and runs its children one after
the other. All states defined between the lines *exp = Experiment()* and
*exp.run()* in your experiment will exist as children of a *Serial* state. Once
one state *.leave()*'s, the *Serial* state will call the next state's
*.enter()* method. Like any flow state, the use of the *with* pythonic keyword
is required and makes your code look clean and readable.  Below is an example
of the *Serial* state.

The following two experiments are equivalent.

::

    exp = Experiment()
    Label(text="First state", duration=2)
    Label(text="Second state", duration=2)
    Label(text="Third state", duration=2)
    exp.run()

::

    exp = Experiment()
    with Serial():
        Label(text="First state", duration=2)
        Label(text="Second state", duration=2)
        Label(text="Third state", duration=2)
    exp.run()

As shown above, the default state of your experiment is a *Serial* state in
which all of the states initialized between *exp = Experiment()* and
*exp.run()* are children of.

Parallel State
==============
A *Parallel state is a state that has children, and runs those children in
parallel of eachother. That means they run at the same time. The key to a
*Parallel* state is that it will not end unless all of its children have
run their *.leave()* function. Once it has no more children running, it will
schedule its own *.leave()* call, allowing the next state to run.

The expecption to this rule is a parameter called *blocking*. It is a boolean
property of every state. If set to False and the state exists as a child of a
*Parallel* state, it will not prevent the *Parallel* state from calling its own
*.leave()* method. This means a *Parallel* will end when all of its *blocking*
states have called thier *.leave()* method. All remaining, non-blocking states
will have their *.cancel()* method called to allow the *Parallel* state to end.

An example below has 3 *Label* states that will disappear from the screen at
the same time, dispite having 3 different durations.

::

    exp = Experiment()
    with Parallel():
        Label(text='This one is in the middle', duration=3)
        Label(text='This is on top', duration=5, blocking=False,
              center_y=exp.screen.center_y+100)
        Label(text='This is on the bottom', duration=10, blocking=False,
              center_y=exp.screen.center_y-100)
    exp.run()

Because the second and third *Label* in the above example are *non-blocking*,
the *Parallel* state will end after the first *Label*'s duration of 3 seconds
instead of the third *Label*'s duration which was 10 seconds.

Meanwhile State
===============
A *Meanwhile* state is one of two parallel with previous states. A *Meanwhile*
will run all of its children in a *Serial* state and then run that in
*Parallel* with the previous state in the stack. A *Meanwhile* state will
*.leave()* when either all of its children have left, or if the previous state
has left. In simpler terms, A *Meanwhile* state runs while the previous state
is still running. If the previous state *.leave()*'s before the *Meanwhile* has
left, then the *Meanwhile* will call *.cancel()* on all of its remaining
children.

If a *Meanwhile* is created and there is no previous state, aka right after the
line *exp = Experiment()* then all of the children of the *Meanwhile* will
run until they leave, or until the experiment is over.

The following example shows how to use a *Meanwhile* to create a instructions
screen that waits for a keypress to continue.

::

    exp = Experiment()
    KeyPress()
    with Meanwhile():
        Label(text="THESE ARE YOUR INSTRUCTIONS, PRESS ENTER")
    exp.run()

As soon as the *KeyPress* state ends, the *Label* will disappear off the screen
because the *Meanwhile* will have canceled it.

UntilDone State
===============
An *UntilDone* state is one of two parallel with previous states.  An
*UntilDone* state will run all of its children in a *Serial* state and then run
that in a *Parallel* with the previous state. An *UntilDone* state will
*.leave()* when all of its children are finished. Once the *UntilDone* calls
*.leave()* it will cancel the previous state if it is still running.

If an *UntilDone* is created and there is no previous state, aka right after
the *exp = Experiment()* line, then all of the children of the *UntilDone* will
run until they leave, then the your experiment will end.

The following example shows how to use an *UntilDone* to create an instructions
screen that waits for a keypress to continue.

::

    exp = Experiment()
    Label(text="THESE ARE YOUR INSTRUCTIONS, PRESS ENTER")
    with UntilDone():
        KeyPress()
    exp.run()

Wait State
==========
A *Wait* state is a very simple state that has a lot of power behind it. At a
top level, it allows your experiment to hold up for a *duration* in seconds.
There are other option you can add to the wait to make it more complicated. The
*jitter* parameter allows for the *Wait* to pause your experiment for the
*duration* plus a random number between 0 and *jitter* seconds.

The other interesting thing a *Wait* state can do is wait until a conditional
is evaluated to True. The *Wait* will create a *Reference* that will
*call_back* *Wait* to alert it to a change in value. Once that change evaluates
to True, the *Wait* state will stop waiting and call its own *.leave()* method.

An example below outlines how to use all the functionality of *Wait*. This
example wants a *Label* to appear on the screen right after another *Label*
does. Since the first *Wait* has a jitter, it is impossible to detect how
long that would be, so we have the second *Wait* wait until lb1 has an
*appear_time*.

::

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

If, ElIf, and Else States
=========================
These 3 states are how SMILE handles branching in your experiment. An *If*
state is all you need to create a conditional branch, but through the use of
the *Elif* and the *Else* state, you can create a much more complex experiment
than if you didn't have to use of conditional states.

The *If* is a parent state that runs all of its children in  serial **if** the
conditional is evaluated as true during **ER**. Behind the scenes, the *If*
state creates a linked list of conditionals and *Serial* states. Initially,
this linked list is populated only by the conditional passed into the *If* and
its children, and a True conditional linked with an empty *Serial* state.
During **ER**, the experiment will loop through each of the conditionals till
one of them evaluates to True and then will run the associated *Serial* state.

If the next state after the *If* state is the *Elif* state, then whatever
conditional is in the *Elif* will be added into the stack of conditionals
within the *If* state. The children of the *Elif* will also be added to the
appropriate stack. You can do as many *Elif*'s after the *If* state as you need
to. The last state can be an *Else* state. When you define the children of the
*Else* state, that *Serial* gets sent into the stack of conditionals and
replaces the True's empty *Serial*.

The following is a 4 option if test.

::

    exp = Experiment()
    Label(text='PRESS A KEY')
    with UntilDone():
        kp = KeyPress()
    with If(kp.pressed == "SPACE"):
        Label(text="YOU PRESSED SPACE", duration=3)
    with Elif(kp.pressed == "J"):
        Label(text="YOU PRESSED THE K KEY", duration=3)
    with Elif(kp.pressed == "F"):
        Label(text="YOU PRESSED THE J KEY", duration=3)
    with Else():
        Label(text="I DONT KNOW WHAT YOU PRESSED", duration=3)
    exp.run()


Loop State
==========
A *Loop* state can handle any kind of looping that you need. The main thing we
use a *Loop* state is to loop over a list of ditionaries that contains your
stimulus. You are also able to create while loops by passing in a *conditional*
parameter. Lastly, instead of looping over a list of dictionaries, you can
loop an exact number of times by passing in a number as a parameter.

When creating a *Loop* state, you must define a variable to access all of the
information about that loop. You do this by utilizing the pythonic *as*
keyword. *with Loop(list_of_dic) as trial:* is the line that defines your loop.
If during your loop you need to access the current iteration of a loop, you
would try to access *trial.current*. Refer to the *smile.state.Loop* docstring
for information on how to access the different properties of a *Loop*.

Below I will show examples of all 3 Loops

List of Dictionaries

::

    #List Gen
    list_of_dic = [{'stim':"STIM 1", 'dur':3},
                   {'stim':"STIM 2", 'dur':2},
                   {'stim':"STIM 3", 'dur':5},
                   {'stim':"STIM 4", 'dur':1}]
    #Experiment
    exp = Experiment()
    with Loop(list_of_dic) as trial:
        Label(text=trial.current['stim'], duration=trial.current['dur'])
    exp.run()


Loop a number of Times

::

    exp = Experiment()
    with Loop(10):
        Label(text='this will show up 10 times!', duration=1)
        Wait(1)
    exp.run()

Loop while something is True

::

    exp = Experiment()
    exp.test = 0
    with Loop(conditional = (exp.test < 10)):
        Label(text='this will show up 10 times!', duration=1)
        Wait(1)
        exp.test = exp.test + 1
    exp.run()



























