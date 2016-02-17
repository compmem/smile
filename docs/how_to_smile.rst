============
How to SMILE
============

.. _how-to-smile:

What is A Hierarchical State Machine?
=====================================

A Hierarchical State Machine is a state machine that relies on both the input
and all the previous states' information in order to make a decision as to
which state to go to next. It takes context information from the previous
states and the input parameters of the current state in order to pick the next
state. Another property of a HSM is the parent-child relationship that some
states have.  In the traffic light example, the green state and the yellow
state could be children of the vehicalsGO state, as in when vehicalsGo enters
it would run green state followed by yellow state after a set time. This
parent-child relationship allows a HSM to give control of several different
states to a single parent, allowing for the running of several states at once
and a higher level of logical progression between states.

SMILE possesses both of these qualities. SMILE takes care of the linking of
children and parents by creating pythonic contexts and using the *with* keyword.
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
your experiments easier by compartmentalizing an experiment into 3 different
parts.  These parts are List Generation, Experimental Build Time, and
Experimental Run Time. By keeping your stimulus generation confined to the
List Generation part of your experiment code, you greatly simplify the logic
required to program your experiment. The **most important** idea to realize
about SMILE is the difference between *Experimental Build Time* and
*Experimental Run Time*.

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

In building your experiment, you may need access to variable that isn't
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

.. code-block:: python
    :linenos:

    exp.variableName = lbl.appear_time['time']



What are References?
====================

The second most important things to understand about SMILE are how References
work. The definition of a SMILE reference is a variable who's value is to be
evaluated later. Without the *Reference* we would not be able to separate the
Experimental Build Time and Experimental Run Time as easily. A :py:class:`~smile.ref.Ref` is a
class that holds any kind of value from a function call and parameters to an
expression of several variables like `fu + bar - coocoo`. In relation to
expressions, References are recursive. Every Reference has a method called
:py:func:`~smile.ref.Ref.eval` which will attempt to evaluate the value of each part of the
expression. If one part of the experession is a Reference, then that Reference
will be recursively evaluated aswell. If the Reference is to a list of values,
each value in the list will be evaluated. Same with any other listlike.

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
    have hangups in the framerate or running of the experiment.

You shouldn't run into *NotAvaiableError*'s unless you are trying to time
a state based off the disappear time of something.

.. _running-smile:

Running a SMILE Experiment
==========================

Not implemented yet.

The states of a State
=====================

Every state in SMILE runs through 6 main function calls. These function calls
are automatic and never need to be called by the end user, but it is important
to understand what they do and when they do it to fully understand SMILE.
These function calls are *__init__*, *.enter()*, *.start()*, *.end()*,
*.leave()*, and *.finalize()*. Each of these calls happen at different parts of
the experiment, and have different functions depending on the subclass.

**.__init__** happens during **BT** and is the only one to happen at **BT**.
This function usually sets up all of the references, proccesses some of the
parameters, and knows what to do if a parameter is missing or wasn't passed in.

**.enter()** happens during **RT** and will be called after the previous state
calls *.leave()*. This function will evaluate all of the parameters that were
references, and set all the values of the remaining parameters. It will also
schedule a start time for this state.

**.start()** is a class of function calls that, during **RT**, the state starts
doing whatever makes it special. this function is not always called *.start()*.
In the case of an :py:class:`~smile.video.Image` state, *.start()* is replaced with *.appear()*. The
*.start()* functions could do anything from showing an image to recording a
keypress. After *.start()* this state will begin actually performing its
main function.

.. note::

    A *.start()* kind of call will only exist in an Action State (see below).

**.end()** is a class of function calls that, during **RT**, ends whatever makes
the state special. In the case of an Image, *.end()* is replaced with
*.disappear()*. After *.end()*, *.leave()* is available to be called.

.. note::

    A *.end()* kind of call will only exist in an Action State (see below).

**.leave()** happens during **RT** and will be called whenever the duration of
a state is over, or whenever the rules of a state says it should end. A special
case for this is the *.cancel()* call. If a state should need to be ended early
for whatever reason, the *Experiment* will call the state's *.cancel()* method
and that method will setup an immediate call to both *.leave()* and
*.finalize()*.

**.finalize()** happens during **RT** but not until after a state has left.
This call usually happens whenever the clock has extra time, IE during a :py:class:`~smile.state.Wait`
state. This call will save out the logs, setup callbacks to the :py:class:`~smile.state.ParentState` to
tell it that this state has finished, and set *self.active* to false. This call
is used to clean up the state sometime after the state has run *.leave()*.

The Flow States of SMILE
========================
One of the basic types of SMILE states are the **Flow** states.  **Flow**
states are states that control the flow of your experiment.

Serial State
------------

A :py:class:`~smile.state.Serial` state is a state that has children, and runs its children one after
the other. All states defined between the lines `exp = Experiment()` and
`exp.run()` in your experiment will exist as children of a *Serial* state. Once
one state `.leave()`'s, the :py:class:`~smile.state.Serial` state will call the next state's
`.enter()` method. Like any flow state, the use of the `with` pythonic keyword
is required and makes your code look clean and readable.  Below is an example
of the *Serial* state.

The following two experiments are equivalent.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    Label(text="First state", duration=2)
    Label(text="Second state", duration=2)
    Label(text="Third state", duration=2)
    exp.run()

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    with Serial():
        Label(text="First state", duration=2)
        Label(text="Second state", duration=2)
        Label(text="Third state", duration=2)
    exp.run()

As shown above, the default state of your experiment is a :py:class:`~smile.state.Serial` state in
which all of the states initialized between `exp = Experiment()` and
`exp.run()` are children of.

Parallel State
--------------

A :py:class:`~smile.state.Parallel` state is a state that has children, and runs those children in
parallel of each other. That means they run at the same time. The key to a
*Parallel* state is that it will not end unless all of its children have
run their `.leave()` function. Once it has no more children running, it will
schedule its own `.leave()` call, allowing the next state to run.

The exception to this rule is a parameter called *blocking*. It is a boolean
property of every state. If set to False and the state exists as a child of a
*Parallel* state, it will not prevent the *Parallel* state from calling its own
`.leave()` method. This means a *Parallel* will end when all of its *blocking*
states have called their `.leave()` method. All remaining, non-blocking states
will have their `.cancel()` method called to allow the *Parallel* state to end.

An example below has 3 :py:class:`~smile.video.Label` states that will disappear from the screen at
the same time, despite having 3 different durations.

.. code-block:: python
    :linenos:

    from smile.common import *
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
---------------

A :py:class:`~smile.state.Meanwhile` state is one of two parallel with previous states. A *Meanwhile*
will run all of its children in a :py:class:`~smile.state.Serial` state and then run that in
:py:class:`~smile.state.Parallel` with the previous state in the stack. A *Meanwhile* state will
`.leave()` when either all of its children have left, or if the previous state
has left. In simpler terms, A *Meanwhile* state runs while the previous state
is still running. If the previous state `.leave()`'s before the *Meanwhile* has
left, then the *Meanwhile* will call `.cancel()` on all of its remaining
children.

If a *Meanwhile* is created and there is no previous state, aka right after the
line `exp = Experiment()` then all of the children of the *Meanwhile* will
run until they leave, or until the experiment is over.

The following example shows how to use a *Meanwhile* to create an instructions
screen that waits for a keypress to continue.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    KeyPress()
    with Meanwhile():
        Label(text="THESE ARE YOUR INSTRUCTIONS, PRESS ENTER")
    exp.run()

As soon as the :py:class:`~smile.keyboard.KeyPress` state ends, the :py:class:`~smile.video.Label` will disappear off the screen
because the *Meanwhile* will have canceled it.

UntilDone State
---------------

An :py:class:`~smile.state.UntilDone` state is one of two parallel with previous states.  An
*UntilDone* state will run all of its children in a :py:class:`~smile.state.Serial` state and then run
that in a :py:class:`~smile.state.Parallel` with the previous state. An *UntilDone* state will
`.leave()` when all of its children are finished. Once the *UntilDone* calls
`.leave()` it will cancel the previous state if it is still running.

If an *UntilDone* is created and there is no previous state, aka right after
the `exp = Experiment()` line, then all of the children of the *UntilDone* will
run until they leave, then the your experiment will end.

The following example shows how to use an *UntilDone* to create an instructions
screen that waits for a keypress to continue.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    Label(text="THESE ARE YOUR INSTRUCTIONS, PRESS ENTER")
    with UntilDone():
        KeyPress()
    exp.run()

Wait State
----------

A :py:class:`~smile.state.Wait` state is a very simple state that has a lot of power behind it. At a
top level, it allows your experiment to hold up for a *duration* in seconds.
There are other option you can add to the wait to make it more complicated. The
*jitter* parameter allows for the *Wait* to pause your experiment for the
*duration* plus a random number between 0 and *jitter* seconds.

The other interesting thing a *Wait* state can do is wait until a conditional
is evaluated to True. The *Wait* will create a :py:class:`~smile.ref.Ref` that will
*call_back* *Wait* to alert it to a change in value. Once that change evaluates
to True, the *Wait* state will stop waiting and call its own `.leave()` method.

An example below outlines how to use all the functionality of *Wait*. This
example wants a :py:class:`~smile.video.Label` to appear on the screen right after another *Label*
does. Since the first *Wait* has a jitter, it is impossible to detect how
long that would be, so we have the second *Wait* wait until lb1 has an
*appear_time*.

.. code-block:: python
    :linenos:

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

If, ElIf, and Else States
-------------------------

These 3 states are how SMILE handles branching in your experiment. An :py:class:`~smile.state.If`
state is all you need to create a conditional branch, but through the use of
the :py:class:`~smile.state.Elif` and the :py:class:`~smile.state.Else` state, you can create a much more complex experiment
than if you didn't have to use of conditional states.

The *If* is a parent state that runs all of its children in  serial **if** the
conditional is evaluated as true during **RT**. Behind the scenes, the *If*
state creates a linked list of conditionals and :py:class:`~smile.state.Serial` states. Initially,
this linked list is populated only by the conditional passed into the *If* and
its children, and a True conditional linked with an empty *Serial* state.
During **RT**, the experiment will loop through each of the conditionals till
one of them evaluates to True and then will run the associated *Serial* state.

If the next state after the *If* state is the *Elif* state, then whatever
conditional is in the *Elif* will be added into the stack of conditionals
within the *If* state. The children of the *Elif* will also be added to the
appropriate stack. You can do as many *Elif*'s after the *If* state as you need
to. The last state can be an *Else* state. When you define the children of the
*Else* state, that *Serial* gets sent into the stack of conditionals and
replaces the True's empty *Serial*.

The following is a 4 option if test.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    Label(text='PRESS A KEY')
    with UntilDone():
        kp = KeyPress()
    with If(kp.pressed == "SPACE"):
        Label(text="YOU PRESSED SPACE", duration=3)
    with Elif(kp.pressed == "J"):
        Label(text="YOU PRESSED THE J KEY", duration=3)
    with Elif(kp.pressed == "F"):
        Label(text="YOU PRESSED THE K KEY", duration=3)
    with Else():
        Label(text="I DONT KNOW WHAT YOU PRESSED", duration=3)
    exp.run()


Loop State
----------

A :py:class:`~smile.state.Loop` state can handle any kind of looping that you need. The main thing we
use a *Loop* state is to loop over a list of dictionaries that contains your
stimulus. You are also able to create while loops by passing in a *conditional*
parameter. Lastly, instead of looping over a list of dictionaries, you can
loop an exact number of times by passing in a number as a parameter.

When creating a *Loop* state, you must define a variable to access all of the
information about that loop. You do this by utilizing the pythonic *as*
keyword. `with Loop(list_of_dic) as trial:` is the line that defines your loop.
If during your loop you need to access the current iteration of a loop, you
would try to access `trial.current`. Refer to the :py:class:`~smile.state.Loop`* docstring
for information on how to access the different properties of a *Loop*.

Below I will show examples of all 3 Loops

List of Dictionaries

.. code-block:: python
    :linenos:

    from smile.common import *
    #List Gen
    list_of_dic = [{'stim':"STIM 1", 'dur':3},
                   {'stim':"STIM 2", 'dur':2},
                   {'stim':"STIM 3", 'dur':5},
                   {'stim':"STIM 4", 'dur':1}]
    #Experiment
    exp = Experiment()
    #The *as* operator allows you to gain access
    #to the data inside the *Loop* state
    with Loop(list_of_dic) as trial:
        Label(text=trial.current['stim'], duration=trial.current['dur'])
    exp.run()


Loop a number of Times

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    with Loop(10):
        Label(text='this will show up 10 times!', duration=1)
        Wait(1)
    exp.run()

Loop while something is True

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    exp.test = 0
    #Never use *and* or *or* always use *&* and *|* when dealing
    #with references. Conditional References only work with
    #absolute operators, not *and* or *or*
    with Loop(conditional = (exp.test < 10)):
        Label(text='this will show up 10 times!', duration=1)
        Wait(1)
        exp.test = exp.test + 1
    exp.run()


The Action States of SMILE
==========================

The other basic type of SMILE states are the **Action** states. The Action
states handle both the input and output in your experiment. The following are
subclasses of WidgetState.

.. note::

    Heads up: All visual states that are wrapped by WidgetState are Kivy Widgets.
    That means all of their individual sets of parameters are located on Kivy's
    website. For all of the parameters that every single WidgetState shares,
    refer to the WidgetState Doctring.

Label
-----

:py:class:`~smile.video.Label` is a :py:class:`~smile.video.WidgetState` that displays text on the screen for a *duration*.
The parameter to interface with its output is called *text*. Whatever string
you pass into *text*, the label will display on the screen. You can also set
*text_size*, a touple that contains (width, height) of the area that your
text is allow to exist in. This parameter is only useful to set if you are
displaying a multiple line amount of text on the screen, in which case you
would pass in (width_of_text, None) so you don't restrict the text in the
vertical direction.

The following is a Label displaying the word "BabaBooie"

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    Label(text="BabaBooie", duration=2, text_size=(500,None))
    exp.run()

Image
-----

:py:class:`~smile.video.Image` is a :py:class:`~smile.video.WidgetState` that displays an image on the screen for a
*duration*. The parameter to interface with its output is called *source*. You
pass in a string path-name to the image you would like to present onto the
screen. If you would like to present the image at a different size than the
original, you need to also set the *allow_stretch* parameter to True. This will
stretch the image to the size of the widget without changing the original
ratio of width to height.

If you would like to make the image stretch to fill the entirety of the widget,
you need to set *allow_stretch* to True and *keep_ratio* to False.

Below is an example of an image at the path "test_image.png" to be presented to
the center of the screen.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    Image(source="test_image.png", duration=3)
    exp.run()

Video
-----

:py:class:`~smile.video.Video` is a :py:class:`~smile.video.WidgetState` that shows a video on the screen for a *duration*.
The parameter to interface with its output is called *source*. You pass in a
string path-name to the video you would like to present on the screen. The
video will play from the beginning for the *duration* of the video. If you would
like the video to be any size different from the original size, you need to set
the *allow_stretch* parameter to True. Then the video will attempt to fill the
size of the *Video* Widget without changing the aspect ratio. If you would like
to completely fill the *Video* Widget with the video, set the *keep_ratio*
parameter to False. There is also the *position* parameter which has to be
between 0 and the *duration* parameter, which tells the video where to start.

Below is an example of playing a video at the path "test_video.mp4" that starts
4 seconds into the video and plays for the entire duration (duration=None).

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    Video(source="test_video.mp4", position=4)
    exp.run()

Vertex Instructions
-------------------

Each **Vertex Instruction** outlined in *video.py* displays a predefined shape
on the screen for a *duration*. The following are all of the basic Vertex
Instructions that SMILE implements.

    - Bezier

    - Mesh

    - Point

    - Triangle

    - Quad

    - Rectangle

    - BorderImage

    - Ellipse

The parameters for each of these vary, but just like any other SMILE state,
they take the same parameters as the default *State* class. They are Kivy
widgets wrapped in our *WidgetState* class, so if you need to know how to use
them or what parameters they take, please refer to the Kivy documentation.

Beep
----

:py:class:`~smile.audio.Beep` is a state that plays a beep noise at a set frequency and volume for
a *duration*. The four parameters you need to set the output of this **Beep**
are *freq*, *volume*, *fadein*, and *fadeout*. *freq* and *volume* are used to
set the frequency and the volume of the **Beep**. *freq* defaults to 400 Hz
and *volume* defaults to .5 the max system volume. *fadein* and *fadeout* are
in seconds and they represent the time it takes to get from 0 to *volume* and
*volume* to 0 respectively.

Below is an example of a beep at 555hz, for 2 seconds, with no fade in or out,
and at 50% volume.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    Beep(freq=555, volume=0.5, duration=2)
    exp.run()

SoundFile
---------

:py:class:`~smile.audio.SoundFile` is a state that plays sound file, like an mp3, for a *duration*
that defaults to the duration of the file. The parameter used to interface
with the output of this state is *filename*. *filename* is the path name to the
sound file you would like to play. *volume* is a float from 1 to 0 where 1 is
the max system volume.

If you would like to start the sound file from a point in the file that isn't
the beginning, you can set the *start* parameter to how many seconds into the
file you would like to start playing.

If you would like to stop playing the sound file at a certain point in the file
that isn't the original end, you must set the *end* parameter to how ever many
seconds from the beginning of the sound file you would like it to end. This
parameter must be greater than the value of *start*.

If you would like the sound file to run on a loop for the *duration* of the
**State**, then you must set the *loop* parameter to True.

Below is an example of playing a sound file at path "test_sound.mp3" at 50%
volume for the full duration of the sound file.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    SoundFile(source="test_sound.mp3", volume=0.5)
    exp.run()

RecordSoundFile
---------------

:py:class:`~smile.audio.RecordSoundFile` will record any sound coming into a microphone for the
*duration* of the state. The file you wish to save this sound file into will be
passed into the *filename* parameter.

Below is an example of recording sound for 10 second while looking at a Label
that says "PLEASE TALK TO YOUR COMPUTER", and saves it into "new_sound.mp3".

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    Label(text="PLEASE TALK TO YOUR COMPUTER")
    #UntilDone to cancel the label after the sound file
    #is done recording.
    with UntilDone():
        RecordSoundFile(filename="new_sound.mp3", duration = 10)
    exp.run()

Button
------

:py:class:`~smile.video.Button` is a visual and an input state that draws a button on the screen
with optional text in the button for a *duration*. You may also set every button
to have a *name* that can be reference by :py:class:`~smile.video.ButtonPress` states to determine
if you pressed the *correct* button. Check out the SMILE tutorial example for
*ButtonPress* for more information.

Below is an example of a Form, where a :py:class:`~smile.video.Label` state will
ask someone to type in an answer to a :py:class:`~smile.video.TextInput`. Then
they will press the button when they are finished typing.

.. code-block:: python
    :linenos:

    from smile.common import *
    from smile.video import TextInput
    exp = Experiment()
    #Show both the Label and the TextInput at the same time
    #during the experiment
    with Parallel():
        #Required to show the mouse on the screen during your experiment!
        MouseCursor()
        Label(text="Yo, Tell me about your ay!?!?", center_y=exp.screen.center_y+50)
        TextInput(text="", width=500, height=200)
    #When the button is pressed, the Button state ends, causing
    #The parallel to cancel all of its children, the Label and the
    #TextInput
    with UntilDone():
        Button(text="Enter")
    exp.run()


ButtonPress
-----------

:py:class:`~smile.video.ButtonPress` is a parent state, much like :py:class:`~smile.state.Parallel` that will run until
a button inside of it is pressed. When defining a **ButtonPress** state, you
can tell it the name of a button inside of it that will be deemed as the
correct button to press by passing in that string *name* of the correct
**Button** or **Buttons** into the *correct_resp* parameter. Refer to the
**ButtonPress** example in the SMILE tutorial document.

Here is an example of choosing between 3 buttons where only one of the buttons
is the correct button to click.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    with ButtonPress(correct_resp=['First_Choice']) as bp:
        #Required to do anything with buttons.
        MouseCursor()
        Label(text="Choose WISELY young WEESLY")
        #Define both bottons, naming them both unique things
        Button(name="First_Choice",text="LEFT CHOICE", center_x=exp.screen.center_x-200)
        Button(name="Second_Choice",text="RIGHT CHOICE", center_x=exp.screen.center_x+200)
    Label(text=bp.pressed, duration=2)
    exp.run()


KeyPress
--------

:py:class:`~smile.keyboard.KeyPress` is an input state that waits for a keyboard press during its
*duration*. You are able to pass in as parameters a list of strings that are
acceptable keyboard buttons into *keys*. You are also able to select a correct
key by passing in its string name as a parameter to *correct_resp*.

You are able to access the information about this **KeyPress** state by getting
the following attributes :

    -pressed : a string that is the name of the key that was pressed.
    -press_time : a float value of the time when the key was pressed.
    -correct : a boolean that is whether or not they pressed the correct_resp
    -rt : a float that is the reaction time of the keypress. It is *press_time* - *base_time*.

The following is a keypress example that will show you what key you pressed.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    with Loop(10):
        #Wait until any key is pressed
        kp = KeyPress()
        #Even though kp.pressed is a reference, you are able
        #to concatinate strings together
        Label(text="You Pressed :" + kp.pressed, duration = 2)
    exp.run()

KeyRecord
---------

:py:class:`~smile.keybaord.KeyRecord` is an input state that records all of the keyboard inputs for its
*duration*. This state will write out each keypress during its *duration* to a
*.slog* file.

The following example will save out a `.slog` file into log_bob.slog after
recording all of the keypresses during a 10 second period.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()
    KeyRecord(name="Bob", duration = 10)
    exp.run()

MouseCursor
-----------

:py:class:`~smile.mouse.MouseCursor` is a visual state that shows your mouse for its *duration*. In
order to effectively use **ButtonPress** and **Button** states, you must also use
**MouseCursor** in parallel. Refer to the **ButtonPress** example in the
SMILE tutorial page for more information.

You can also set the cursor image and the offset of the image as parameters
to this state. Whatever image you have in the passed in filename will be
presented on the screen instead of your default mouse cursor.

The following example is of a mouse cursor that needs to be presented with an
imaginary image to be displayed as the cursor. Since the imaginary image is
100 by 100 pixels, and it points to the center of the image, we want the offset
of the cursor to be (50,50) so that the actual *click* of the mouse is in the
correct location.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = experiment()
    MouseCursor(duration = 10, filename="mouse_test_pointer.png", offset=(50,50))
    exp.run()

For more useful mouse tutorials, see the **Mouse Stuff** section of the Tutorial
docutment.

























