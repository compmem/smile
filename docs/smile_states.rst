============
SMILE States
============

The States of a State
=====================

Every state in SMILE runs through 6 main function calls. These function calls
are automatic and never need to be called by the end user, but it is important
to understand what they do and when they do it to fully understand SMILE.
These function calls are *__init__*, *.enter()*, *.start()*, *.end()*,
*.leave()*, and *.finalize()*. Each of these calls happen at different parts of
the experiment, and have different functions depending on the subclass.

**.__init__** happens during **BT** and is the only one to happen at **BT**.
This function usually sets up all of the references, processes some of the
parameters, and knows what to do if a parameter is missing or wasn't passed in.

**.enter()** happens during **RT** and will be called after the previous state
calls *.leave()*. This function will evaluate all of the parameters that were
references, and set all the values of the remaining parameters. It will also
schedule a start time for this state.

**.start()** is a class of function calls that, during **RT**, the state starts
doing whatever makes it special. This function is not always called *.start()*.
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
This call usually happens whenever the clock has extra time, i.e. during a :py:class:`~smile.state.Wait`
state. This call will save out the logs, setup callbacks to the :py:class:`~smile.state.ParentState` to
tell it that this state has finished, and set *self.active* to false. This call
is used to clean up the state sometime after the state has run *.leave()*.

The Flow States of SMILE
========================
One of the basic types of SMILE states are the **Flow** states.  **Flow**
states are states that control the flow of the experiment.

Serial State
------------

A :py:class:`~smile.state.Serial` state is a state that has children, and runs its children one after
the other. All states defined between the lines `exp = Experiment()` and
`exp.run()` in an experiment will exist as children of a *Serial* state. Once
one state `.leave()`'s, the :py:class:`~smile.state.Serial` state will call the next state's
`.enter()` method. Like any flow state, the use of the `with` pythonic keyword
is required and makes the source code look clean and readable.  Below is an example
of the *Serial* state.

The following two experiments are equivalent.

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Label(text="First state", duration=2)
    Label(text="Second state", duration=2)
    Label(text="Third state", duration=2)

    exp.run()

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    with Serial():
        Label(text="First state", duration=2)
        Label(text="Second state", duration=2)
        Label(text="Third state", duration=2)

    exp.run()

As shown above, the default state of an experiment is a :py:class:`~smile.state.Serial` state in
which all of the states initialized between `exp = Experiment()` and
`exp.run()` are children of.

Parallel State
--------------

A :py:class:`~smile.state.Parallel` state is a state that has children, and runs those children in
parallel of each other. That means they run at the same time. The key to a
*Parallel* state is that it will not end unless all of its children have
run their `.leave()` function. Once it has no more children running, the current state will
schedule its own `.leave()` call, allowing the next state to run.

The exception to this rule is a parameter called *blocking*. It is a Boolean
property of every state. If set to False and the state exists as a child of a
*Parallel* state, it will not prevent the *Parallel* state from calling its own
`.leave()` method. This means a *Parallel* will end when all of its *blocking*
states have called their `.leave()` method. All remaining, non-blocking states
will have their `.cancel()` method called to allow the *Parallel* state to end.

An example below has 3 :py:class:`~smile.video.Label` states that will disappear from the screen at
the same time, despite having 3 different durations.

.. code-block:: python

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
run until they leave. Then, the experiment will end.

The following example shows how to use an *UntilDone* to create an instructions
screen that waits for a keypress to continue.

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Label(text="THESE ARE YOUR INSTRUCTIONS, PRESS ENTER")
    with UntilDone():
        KeyPress()

    exp.run()

Wait State
----------

A :py:class:`~smile.state.Wait` state is a very simple state that has a lot of power behind it. At a
top level, it allows an experiment to hold up for a *duration* in seconds.
There are other options which can add to the wait to make it more complicated. The
*jitter* parameter allows for the *Wait* to pause an experiment for the
*duration* plus a random number between 0 and *jitter* seconds.

The unique characteristic a *Wait* state has is the ability to wait until a conditional
is evaluated to True. The *Wait* will create a :py:class:`~smile.ref.Ref` that will
*call_back* *Wait* to alert it to a change in value. Once that change evaluates
to True, the *Wait* state will stop waiting and call its own `.leave()` method.

An example below outlines how to use all the functionality of *Wait*. This
example wants a :py:class:`~smile.video.Label` to appear on the screen right after another *Label*
does. Since the first *Wait* has a jitter, it is impossible to detect how
long that would be, so there resides a second *Wait* wait until lb1 has an
*appear_time*.

.. code-block:: python

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

These 3 states are how SMILE handles branching in an experiment. Only a :py:class:`~smile.state.If`
state is needed to create a branch. Through the use of
the :py:class:`~smile.state.Elif` and the :py:class:`~smile.state.Else` state, much more complex experiments
can be created.

The *If* is a parent state that runs all of its children in  serial **if** the
conditional is evaluated as true during **RT**. Behind the scenes, the *If*
state creates a linked list of conditionals and :py:class:`~smile.state.Serial` states. Initially,
this linked list is populated only by the conditional passed into the *If* and
its children and a True conditional linked with an empty *Serial* state.
During **RT**, the experiment will loop through each of the conditionals until
one of them evaluates to True and then will run the associated *Serial* state.

If the next state after the *If* state is the *Elif* state, then whatever
conditional is in the *Elif* state will be added into the stack of conditionals
within the *If* state. The children of the *Elif* will also be added to the
appropriate stack. As many *Elif* states as desired can be used after the *If* state
The last state can be an *Else* state. When the children of the
*Else* state is defined, the *Serial* state gets sent into the stack of conditionals and
replaces the True's empty *Serial*.

The following is a 4 option if test.

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Label(text='PRESS A KEY')
    with UntilDone():
        kp = KeyPress()

    with If(kp.pressed == "SPACEBAR"):
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

A :py:class:`~smile.state.Loop` state can handle any kind of looping needed. The
main use for a *Loop* state is to loop over a list of dictionaries that contain
stimuli. Loops can also be created by passing in a *conditional* parameter.
Lastly, instead of looping over a list of dictionaries, *Loop* states can be used to
loop an exact number of times by passing in a number as a parameter.

A *Loop* state requires a variable to be defined to access all for the information
about the loop. This can be performed by utilizing the pythonic *as* keyword.
`with Loop(list_of_dic) as trial:` is the line that defines the loop. If access
to the current iteration of a loop is needed, 'trial.current' can be utilized.

Refer to the :py:class:`~smile.state.Loop`* docstring
for information on how to access the different properties of a *Loop*.

Below is an example of all 3 loops.

List of Dictionaries

.. code-block:: python

    from smile.common import *

    #List Gen
    list_of_dic = [{'stim':"STIM 1", 'dur':3},
                   {'stim':"STIM 2", 'dur':2},
                   {'stim':"STIM 3", 'dur':5},
                   {'stim':"STIM 4", 'dur':1}]

    # Initialize the Experiment
    exp = Experiment()

    # The *as* operator allows one to gain access
    # to the data inside the *Loop* state
    with Loop(list_of_dic) as trial:
        Label(text=trial.current['stim'], duration=trial.current['dur'])

    exp.run()


Loop a number of times:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    with Loop(10):
        Label(text='This will show up 10 times!', duration=1)
        Wait(1)

    exp.run()

Loop while something is true:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    exp.test = 0

    # Never use *and* or *or* always use *&* and *|* when dealing
    # with references. Conditional References only work with
    # absolute operators, not *and* or *or*
    with Loop(conditional = (exp.test < 10)):
        Label(text='This will show up 10 times!', duration=1)
        Wait(1)
        exp.test = exp.test + 1

    exp.run()


The Action States of SMILE
==========================

The other basic type of SMILE states are the **Action** states. The Action
states handle both the input and output in experiments. The following are
subclasses of WidgetState.

.. note::

    Heads up: All visual states that are wrapped by WidgetState are Kivy Widgets.
    That means all of their individual sets of parameters are located on Kivy's
    website. For all of the parameters that every single WidgetState shares,
    refer to the WidgetState Doctring.

Debug
-----

:py:class:`~smile.state.Debug` is a :py:class:`~smile.state.State` that is
primarily used to print out the values of references to the command line. This
**State** should not be used as a replacement for **print** during experimental
runtime. It should only be used to print the current values of references during
the experimental runtime.

You can give a **Debug** state a *name* to distinguish it from other **Debugs**
that you might be running. **Debugs** work on with keyword arguments. Below is
an example for how to properly use the **Debug** state and the sample output
that it produces.

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    lbl = Label(text="Hello, World", duration=2)
    Wait(until=lbl.disappear_time)
    Debug(name="Label appear debug", appear=lbl.appear_time['time'],
          disappear=lbl.disappear_time['time'])

    exp.run()

And it would output

::

    DEBUG (file: 'debug_example.py', line: 7, name: Label appear debug) - lag=0.012901s
        appear: 1468255447.360574
        disappear: 1468255449.359951


Func
----

:py:class:`~smile.state.Func` is a :py:class:`~smile.state.State` that can run a
function during Experimental Runtime. The first argument is always the name of
the function and the rest of the arguments are the arguments that are sent to
the function. You can pass in parameters to the **Func** state the same way you
would pass them into the function you are wanting to run during experimental
runtime. In order to access the return value of the function passed in, you need
to access the *.result* attribute of the **Func** state.

The following is an exmaple on how to run a predefined function during
experimental runtime.

.. code-block:: python

    from smile import *

    def pre_func(i):
        return i * 50.7777

    exp = Experiment()

    with Loop(100) as lp:
        rtrn = Func(lp.i)
        Debug(i = rtrn.result)

    exp.run()

Label
-----

:py:class:`~smile.video.Label` is a :py:class:`~smile.video.WidgetState` that displays text on the screen for a *duration*.
The parameter to interface with its output is called *text*. The lable will display
any string that is passed into *text*. *Text_size* can also be set, which is a tuple
that contains (width, height) of the area the text resides in. If a goal in an experiment
is to display multiple lines of text on the screen, this parameter is helpful through passing
in (width_of_text, None) so the amount of text is not restricted in the vertical direction.

The following is a Label displaying the word "BabaBooie":

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Label(text="Hello, World", duration=2, text_size=(500,None))

    exp.run()

Image
-----

:py:class:`~smile.video.Image` is a :py:class:`~smile.video.WidgetState` that displays an image on the screen for a
*duration*. The parameter to interface with its output is called *source*. A string
path-name is passed in to the image desired to be presented onto the screen. The *allow_stretch*
parameter can be set to True if the original image needs to be presented at a different
size. The *allow_stretch* parameter will stretch the image to the size of the widget
without changing the original ratio of width to height.

By setting *allow_stretch* to True and *keep_ratio* to False the image will stretch
to fill the entirety of the widget.

Below is an example of an image at the path "test_image.png" to be presented to
the center of the screen:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Image(source="test_image.png", duration=3)

    exp.run()

Video
-----

:py:class:`~smile.video.Video` is a :py:class:`~smile.video.WidgetState` that shows a video on the screen for a *duration*.
The parameter to interface with its output is called *source*. A string path-name to the video
can be passed in to present the video on the screen The video will play from the beginning
for the *duration* of the video. The *allow_stretch* parameter can be set to True if changing
the video size from the original size is desired. Afterwards, the video will attempt to fill
the size of the *Video* Widget without changing the aspect ration. Setting the *keep_ratio*
parameter to False will completely fill the *Video* Widget with the video.There is also the
*position* parameter which has to be between 0 and the *duration* parameter, which tells
the video where to start.

Below is an example of playing a video at the path "test_video.mp4" that starts
4 seconds into the video and plays for the entire duration (duration=None):

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Video(source="test_video.mp4", position=4)

    exp.run()

Vertex Instructions
-------------------

Each **Vertex Instruction** outlined in *video.py* displays a predefined shape
on the screen for a *duration*. The following are all of the basic Vertex
Instructions that SMILE implements:

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
widgets wrapped in our *WidgetState* class. Kivy documentation can be reffered to
for understanding how to use them or what parameters they take.

Beep
----

:py:class:`~smile.audio.Beep` is a state that plays a beep noise at a set frequency and volume for
a *duration*. The four parameters needed to set the output of this **Beep**
are *freq*, *volume*, *fadein*, and *fadeout*. *freq* and *volume* are used to
set the frequency and the volume of the **Beep**. *freq* defaults to 400 Hz
and *volume* defaults to .5 the max system volume. *fadein* and *fadeout* are
in seconds and they represent the time it takes to get from 0 to *volume* and
*volume* to 0 respectively.

Below is an example of a beep at 555hz, for 2 seconds, with no fade in or out,
and at 50% volume:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Beep(freq=555, volume=0.5, duration=2)

    exp.run()

SoundFile
---------

:py:class:`~smile.audio.SoundFile` is a state that plays a sound file, like an mp3, for a *duration*
that defaults to the duration of the file. The parameter used to interface
with the output of this state is *filename*. *filename* is the path name to the
sound file saved on the computer. *volume* is a float from 1 to 0 where 1 is
the max system volume.

The *start* parameter allows for sound files to begin at the desired point in the audio file.
By using the *start* parameter, the audio will begin however many seconds into the audio as
desired.

The *end* parameter allows for sound files to end before the original end of the audio.
The *end* parameter must be set to however many seconds from the beginning of the sound file
it is desired to end at. The parameter must be greater than the value of *start*.

If the *loop* parameter is set to True, the sound file will run on a loop for the
*duration* of the **State**.

Below is an example of playing a sound file at path "test_sound.mp3" at 50%
volume for the full duration of the sound file:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    SoundFile(source="test_sound.mp3", volume=0.5)

    exp.run()

RecordSoundFile
---------------

:py:class:`~smile.audio.RecordSoundFile` will record any sound coming into a microphone for the
*duration* of the state. The audio recording will be saved to an audio file named
after what is passed into the *filename* parameter.

Below is an example of recording sound for 10 second while looking at a Label
that says "PLEASE TALK TO YOUR COMPUTER", and saves it into "new_sound.mp3":

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Label(text="PLEASE TALK TO YOUR COMPUTER")
    # UntilDone to cancel the label after the sound file
    # is done recording.
    with UntilDone():
        RecordSoundFile(filename="new_sound.mp3", duration = 10)

    exp.run()

Button
------

:py:class:`~smile.video.Button` is a visual and an input state that draws a button on the screen
with optional text in the button for a *duration*. Every button can be set to have
a *name* that can be reference by :py:class:`~smile.video.ButtonPress` states to determine
if the *correct* button was pressed. See the SMILE tutorial example for
*ButtonPress* for more information.

Below is an example of a Form, where a :py:class:`~smile.video.Label` state will
ask someone to type in an answer to a :py:class:`~smile.video.TextInput`. Then
they will press the button when they are finished typing:

.. code-block:: python

    from smile.common import *

    from smile.video import TextInput

    exp = Experiment()

    # Show both the Label and the TextInput at the same time
    # during the experiment
    with Parallel():
        # Required to show the mouse on the screen during the experiment!
        MouseCursor()
        Label(text="Hello, Tell me about your day!", center_y=exp.screen.center_y+50)
        TextInput(text="", width=500, height=200)

    # When the button is pressed, the Button state ends, causing
    # the parallel to cancel all of its children, the Label and the
    # TextInput
    with UntilDone():
        # A ButtonPress will end whenever one of its child buttons
        # is pressed.
        with ButtonPress():
            Button(text="Enter")

    exp.run()


ButtonPress
-----------

:py:class:`~smile.video.ButtonPress` is a parent state, much like :py:class:`~smile.state.Parallel`, that will run until
a button inside of it is pressed. When defining a **ButtonPress** state, The name
of a button inside of the parent state can be designated as the correct button to
press by passing the string *name* of the correct **Button** or **Buttons** into
the *correct_resp* parameter. Refer to the **ButtonPress** example in the SMILE
tutorial document.

The following is an example of choosing between 3 buttons where only one of the buttons
is the correct button to click:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    # A ButtonPress will end whenever one of its child buttons
    # is pressed.
    with ButtonPress(correct_resp=['First_Choice']) as bp:
        # Required to do anything with buttons.
        MouseCursor()
        Label(text="Choose WISELY young WEESLY")
        # Define both buttons, naming them both unique things
        Button(name="First_Choice",text="LEFT CHOICE", center_x=exp.screen.center_x-200)
        Button(name="Second_Choice",text="RIGHT CHOICE", center_x=exp.screen.center_x+200)
    Label(text=bp.pressed, duration=2)

    exp.run()


KeyPress
--------

:py:class:`~smile.keyboard.KeyPress` is an input state that waits for a keyboard press during its
*duration*. A list of strings can be passed in as parameters that are
acceptable keyboard buttons into *keys*. a correct key can be selected by passing
in its string name as a parameter to *correct_resp*.

Access to the information about the **KeyPress** state by can be achieved by using
the following attributes:

    -pressed : a string that is the name of the key that was pressed.
    -press_time : a float value of the time when the key was pressed.
    -correct : a boolean that is whether or not they pressed the correct_resp
    -rt : a float that is the reaction time of the keypress. It is *press_time* - *base_time*.

The following is a keypress example that will identify what keys were pressed.

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    with Loop(10):
        # Wait until any key is pressed
        kp = KeyPress()
        # Even though kp.pressed is a reference, you are able
        # to concatenate strings together
        Label(text="You Pressed :" + kp.pressed, duration = 2)

    exp.run()

KeyRecord
---------

:py:class:`~smile.keybaord.KeyRecord` is an input state that records all of the keyboard inputs for its
*duration*. This state will write out each keypress during its *duration* to a
*.slog* file.

The following example will save out a `.slog` file into log_bob.slog after
recording all of the keypresses during a 10 second period:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    KeyRecord(name="Bob", duration = 10)

    exp.run()

MouseCursor
-----------

:py:class:`~smile.mouse.MouseCursor` is a visual state that shows the mouse for its *duration*. In
order to effectively use **ButtonPress** and **Button** states, **MouseCursor**
in parallel must be used. Refer to the **ButtonPress** example in the
SMILE tutorial page for more information.

The cursor image and the offset of the image can also be set as parameters
to this state. Any image passed in filename will be presented on the screen, replacing
the default mouse cursor.

The following example is of a mouse cursor that needs to be presented with an
imaginary image to be displayed as the cursor. Since the imaginary image is
100 by 100 pixels, and it points to the center of the image, we want the offset
of the cursor to be (50,50) so that the actual *click* of the mouse is in the
correct location:

.. code-block:: python

    from smile.common import *

    exp = experiment()

    MouseCursor(duration = 10, filename="mouse_test_pointer.png", offset=(50,50))

    exp.run()

For more useful mouse tutorials, see the **Mouse Stuff** section of the Tutorial
document.
