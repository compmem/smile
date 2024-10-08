.. _smile_states


============
SMILE States
============

The States of SMILE
===================
Below is the list of most of the SMILE states you will ever need when running an
experiment. Each state has a rudimentary tutorial on how to use them. If you
need more information about what a specific state does, then checkout each
state's docstring.

The Flow States of SMILE
========================
One of the basic types of SMILE states are the **Flow** states.  **Flow**
states are states that control the flow of the experiment.

Serial State
------------

A :py:class:`~smile.state.Serial` state is a state that has children and runs
its children one after another. That means that the next state will not start
until the previous state has ended. The default state that a SMILE experiment is
in is a *Serial* state. That means that every state between
'exp = Experiment()' and 'exp.run()'. Once one state ends, the
:py:class:`~smile.state.Serial` state will call the next state's start method.
Like any flow state, the use of the `with` pythonic keyword is required.  Below
are a few examples of the *Serial* state and displaying text on the screen.

.. note::

    For many examples, Action State *Label* will be used.  This state merely
    displays text on the screen, similar to the "print" python command.  For
    more details on *Label*, click :py:class:`~smile.video.Label`.

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

As shown above, the default state of an experiment is a
:py:class:`~smile.state.Serial` state in which all of the states initialized
between `exp = Experiment()` and `exp.run()` are children.

For more details, see the :py:class:`~smile.state.Serial` docstring.

Parallel State
--------------

A :py:class:`~smile.state.Parallel` state is a parent state that has children
and runs those children simultaneously. This means that all of the children
inside a *Parallel* state will start at the exact same time. The key to a
*Parallel* state is that it will not end unless all of its children have ended.
Once it has no more children running, the current state will schedule its own
end call, allowing the next state to run.

The exception to this rule is when a parameter called *blocking* is set to
False. *blocking* is a Boolean property of every state that only works when the
state is a child of a *Parallel* state. If set to False, it will not prevent the
*Parallel* state from calling its own end method. So, a *Parallel* will end when
all of its *blocking* children have called their end methods. All remaining,
non-blocking states will have their cancel method called to allow the *Parallel*
state to end.

An example below has 3 :py:class:`~smile.video.Label` states that will disappear
from the screen at the same time, despite having 3 different durations.

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

Below is a real world example showing an important use case for having all
non-blocking states within a parallel. In this scenario, the experimenter only
wants a Rectangle state to be on the screen until either a mouse press or a
key press occurs. 

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Rectangle(color="GREEN")
    with UntilDone():
        with Parallel():
            # Because both the MousePress and the KeyPress
            # are non-blocking, the Parallel will end when
            # ever one of the two end.
            mp = MousePress(blocking=False)
            kp = KeyPress(blocking=False)

    # Since we don't know whether or not the mouse press or
    # the key press happened, we have to have an If to test
    # whose data we save out.
    with If(kp.pressed != None):
        exp.pressed = kp.pressed
        exp.rt = kp.rt
        exp.press_time = kp.press_time
    with Else():
        exp.pressed = mp.pressed
        exp.rt = mp.rt
        exp.press_time = mp.press_time

    # This is a Log state saving out the data from the above
    # test.
    Log(name="pressed_log",
        pressed=exp.pressed,
        rt=exp.rt,
        press_time=exp.press_time)

    exp.run()


Parallel.insert()
+++++++++++++++++

Sometimes in a smile experiment you want to run a number of states in parallel
of each other, but you don't know that number until the experiment is already
running. *Parallel.insert()* is how you accomplish this. It allows you to add
states to a *Parallel* during Run Time. A good use case for this function is in
the dot judgement task. Each trail of dot judgement has a different amount of
dots on the screen, so we can't exactly define every single dot that could
possibly be in each trial! Instead we will use the Parallel.insert() to
accomplish this.

For this example, we will be displaying a number of rectangles onto the screen


..code-block:: python

    from smile.common import *

    exp = Experiment()

    with Loop(10) as lp:
        Wait(1)
        # The *as par* allows us to access the parallel state later
        with Parallel() as par:
            # Loop.i is the is the number representing the ith iteration through
            # the loop.
            with Loop(lp.i+1) as rec_loop:
                with par.insert():
                    Rectangle(center_x=rec_loop.i*70, width=60, height=60,
                              duration=1)

    exp.run()

As you can see above, the Parallel.insert() within a Loop state within a
Parallel state framework allows you to put a to be determined amount of states
into a parallel.

For more details about the inner workings of a Parallel state, or for how to log
information from states that have been inserted into a parallel, see the
:py:class:`~smile.state.Parallel` docstring.

Meanwhile State
---------------

A :py:class:`~smile.state.Meanwhile` state is one of two parallel with previous
states. A *Meanwhile* will run all of its children in a
:py:class:`~smile.state.Serial` state and then run that in
:py:class:`~smile.state.Parallel` with the previous state in the stack. A
*Meanwhile* state will end when either all of its children have left, or if the
previous state has left. In simpler terms, a *Meanwhile* state runs while the
previous state is still running. If the previous state ends before the
*Meanwhile* has ended, then the *Meanwhile* will cancel all of its remaining
children.

If you create a *Meanwhile* state at the start of your experiment, i.e. after
the *exp = Experiment()* line, the children of the Meanwhile state will run in
parallel to the rest of the experiment. Once the rest of the experiment ends,
the meanwhile will end.

The following example shows how to use a *Meanwhile* to create an instructions
screen that waits for a keypress to continue.

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    KeyPress()
    with Meanwhile():
        Label(text="THESE ARE YOUR INSTRUCTIONS, PRESS ENTER")

    exp.run()

As soon as the :py:class:`~smile.keyboard.KeyPress` state ends, the
:py:class:`~smile.video.Label` will disappear off the screen because the
*Meanwhile* will have canceled it.

For more details, see the :py:class:`~smile.state.Meanwhile` docstring.

UntilDone State
---------------

An :py:class:`~smile.state.UntilDone` state is one of two parallel with previous
states.  An *UntilDone* state will run all of its children in a
:py:class:`~smile.state.Serial` state and then run them in a
:py:class:`~smile.state.Parallel` with the previous state. An *UntilDone* state
will end when all of its children are finished. Once the *UntilDone* ends, it
will cancel the previous state if still running.

If an *UntilDone* is created and there is no previous state (right after
the `exp = Experiment()` line), all of the children of the *UntilDone* will
run until they end. The experiment will then end.

The following example shows how to use an *UntilDone* to create an instructions
screen that waits for a keypress to continue.

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Label(text="THESE ARE YOUR INSTRUCTIONS, PRESS ENTER")
    with UntilDone():
        KeyPress()

    exp.run()

For more details, see the :py:class:`~smile.state.UntilDone` docstring.

Wait State
----------

A :py:class:`~smile.state.Wait` state is a very simple state that has a lot of
power behind it. This is particularly useful when coordinating the timings
different action states. There are other options which can add to the wait to
make it more complicated. The *jitter* parameter allows for the *Wait* to pause
an experiment for the *duration* plus a random number between 0 and *jitter*
seconds.

The unique characteristic a *Wait* state has is the ability to wait until a
conditional is evaluated to True. The *Wait* will create a
:py:class:`~smile.ref.Ref` that will *call_back* *Wait* to alert it to a change
in value. Once that change evaluates to True, the *Wait* state will stop waiting
and call its own end method.

An example below outlines how to use all the functionality of *Wait*. This
example wants a :py:class:`~smile.video.Label` to appear on the screen right
after another *Label* does. Since the first *Wait* has a *jitter*, it is
impossible to detect how long that would be, so there resides a second *Wait*
state waits until lb1 has an *appear_time*.

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

For more details, see the :py:class:`~smile.state.Wait` docstring.

If, Elif, and Else States
-------------------------

These 3 states are how SMILE handles branching in an experiment. Only a
:py:class:`~smile.state.If` state is needed to create a branch. Through the use
of the :py:class:`~smile.state.Elif` and the :py:class:`~smile.state.Else`
state, much more complex experiments can be created.

An *If* state runs all of its children in serial only if its conditional
statement is considered True. Below is a simple of an *If* state.

.. code-block:: python

	from smile.common import *
	exp = Experiment()
	exp.a = 1
	exp.b = 1
	with If exp.a == exp.b:
		Label(text="CORRECT")
	exp.run()

Here, *exp.a == exp.b* is the conditional statement.  This *If* state expresses
that if the conditional *exp.a == exp.b* is True, then the experiment will
display the Label "CORRECT".  In this case, if the conditional was False
(say exp.b = 2 instead of 1), then the experiment will not display the Label.

An *Elif* statement, short for "Else if", is another conditional statement. It
functions the same as the pythonic "elif". An *Else* statement is identical to
the pythonic "else". The following is a 4 option if test.

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

For more details, see the:py:class:`~smile.state.If`,
:py:class:`~smile.state.Elif`, or :py:class:`~smile.state.Else` docstrings.

Loop State
----------

A :py:class:`~smile.state.Loop` state can handle any kind of looping needed. The
main use for a *Loop* state is to loop over a list of dictionaries that contain
stimuli. Loops can also be created by passing in a *conditional* parameter.
Lastly, instead of looping over a list of dictionaries, *Loop* states can be
used to loop an exact number of times by passing in a number as a parameter.

A *Loop* state requires a variable to be defined to access all of the
information about the loop. This can be performed by utilizing the pythonic *as*
keyword. *with Loop(list_of_dic) as trial:* is the line that defines the loop.
If access to the current iteration of a loop is needed, 'trial.current' can be
utilized.

Refer to the :py:class:`~smile.state.Loop`* docstring for information on how to
access the different properties of a *Loop*.

Below are a few examples of different use-cases for loops.

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

Loop and Display a different number based on the current loop iteration:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    with Loop(10) as lp:
        # Because lp.i is a ref, we need to create a ref that converts it to
        # to a string during run time. That is what Ref(str, lp.i) does.
        Label(text=Ref(str, lp.i), duration=1)
        Wait(1)

    exp.run()



Loop while something is true:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    exp.test = 0

    # Never use *and* or *or*. Always use *&* and *|* when dealing
    # with references. Conditional References only work with
    # absolute operators, not *and* or *or*
    with Loop(conditional = (exp.test < 10)):
        Label(text='This will show up 10 times!', duration=1)
        Wait(1)
        exp.test = exp.test + 1

    exp.run()

For more details, see the :py:class:`~smile.state.Loop` docstrings.

The Action States of SMILE
==========================

The other basic type of SMILE states are the **Action** states. The Action
states handle both the input and output in experiments. The following are
subclasses of WidgetState.

.. note::

    Heads up: All visual states that are wrapped by WidgetState are Kivy Widgets. That means all of their individual sets of parameters are located on Kivy's website. For all of the parameters that every single WidgetState shares, refer to the WidgetState Doctring.

Debug
-----

:py:class:`~smile.state.Debug` is a :py:class:`~smile.state.State` that is
primarily used to print out the values of references to the command line. This
**State** should not be used as a replacement for **print** during experimental
runtime. It should only be used to print the current values of references during
the experimental runtime.

You can give a **Debug** state a *name* to distinguish it from other **Debug**
states that you might be running. **Debug** work with keyword arguments. Below
is an example for how to properly use the **Debug** state and the sample output
that it produces.

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    lbl = Label(text="Hello, World", duration=2)
    Wait(until=lbl.disappear_time)
    Debug(name="Label appear debug", appear=lbl.appear_time['time'],
          disappear=lbl.disappear_time['time'])

    exp.run()

And it would output:

::

    DEBUG (file: 'debug_example.py', line: 7, name: Label appear debug) - lag=0.012901s
        appear: 1468255447.360574
        disappear: 1468255449.359951

For more details, see the :py:class:`~smile.state.Debug` docstring.

Func
----

:py:class:`~smile.state.Func` is a :py:class:`~smile.state.State` that can run a
function during Experimental Runtime. The first argument is always the name of
the function and the rest of the arguments are sent to the function. You can
pass in parameters to the **Func** state the same way you would pass them into
the function you are wanting to run during experimental runtime. In order to
access the return value of the function passed in, you need to access the
*.result* attribute of the **Func** state.

The following is an example on how to run a predefined function during
experimental runtime.

.. code-block:: python

    from smile.common import *

    def pre_func(i):
        return i * 50.7777

    exp = Experiment()

    with Loop(100) as lp:
        rtrn = Func(pre_func,lp.i)
        Debug(i = rtrn.result)

    exp.run()

For more details click :py:class:`~smile.state.Func`.

Label
-----

:py:class:`~smile.video.Label` is a :py:class:`~smile.video.WidgetState` that
displays text on the screen for a *duration*. The parameter to interface with
its output is called *text*. The label will display any string that is passed
into *text*. *Text_size* can also be set, which is a tuple that contains (width,
height) of the area the text resides in. If a goal in an experiment is to
display multiple lines of text on the screen, this parameter is helpful through
passing in (width_of_text, None) so the amount of text is not restricted in the
vertical direction.

The following is a Label displaying the word "BabaBooie":

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Label(text="Hello, World", duration=2, text_size=(500,None))

    exp.run()

For more details, see the :py:class:`~smile.video.Label` docstring.

Image
-----

:py:class:`~smile.video.Image` is a :py:class:`~smile.video.WidgetState` that
displays an image on the screen for a *duration*. The parameter to interface
with its output is called *source*. A string path-name is passed into the
desired image to be presented onto the screen. The *allow_stretch* parameter can
 be set to True if the original image needs to be presented at a different size.
  The *allow_stretch* parameter will stretch the image to the size of the widget
without changing the original ratio of width to height.

By setting *allow_stretch* to True and *keep_ratio* to False the image will
stretch to fill the entirety of the widget.

Below is an example of an image at the path "test_image.png" to be presented to
the center of the screen:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Image(source="test_image.png", duration=3)

    exp.run()

For more details, see the :py:class:`~smile.video.Image` docstring.

Video
-----

:py:class:`~smile.video.Video` is a :py:class:`~smile.video.WidgetState` that
shows a video on the screen for a *duration*. The parameter to interface with
its output is called *source*. A string path-name to the video can be passed in
to present the video on the screen. The video will play from the beginning for
the *duration* of the video. The *allow_stretch* parameter can be set to True if
changing the video size from the original size is desired. Afterwards, the video
will attempt to fill he size of the *Video* Widget without changing the aspect
ratio. Setting the *keep_ratio* parameter to False will completely fill the
*Video* Widget with the video. There is also the *position* parameter, which has
to be between 0 and the *duration* parameter, telling the video where to start.

Below is an example of playing a video at the path "test_video.mp4" that starts
4 seconds into the video and plays for the entire duration (duration=None):

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Video(source="test_video.mp4", position=4)

    exp.run()

For more details, see the :py:class:`~smile.video.Video` docstring.

Vertex Instructions
-------------------

Each **Vertex Instruction** outlined in *video.py* displays a predefined shape
on the screen for a *duration*. The following are all of the basic Vertex
Instructions that SMILE implements:

    - :py:class:`~smile.video.Bezier`

    - :py:class:`~smile.video.Mesh`

    - :py:class:`~smile.video.Point`

    - :py:class:`~smile.video.Triangle`

    - :py:class:`~smile.video.Quad`

    - :py:class:`~smile.video.Rectangle`

    - :py:class:`~smile.video.BorderImage`

    - :py:class:`~smile.video.Ellipse`

The parameters for each of these vary, but just like any other SMILE state,
they take the same parameters as the default *State* class. They are Kivy
widgets wrapped in our *WidgetState* class. Kivy documentation can be referred
to for understanding how to use them or what parameters they take.

Beep
----

:py:class:`~smile.audio.Beep` is a state that plays a beep noise at a set
frequency and volume for a *duration*. The four parameters needed to set the
output of this **Beep** are *freq*, *volume*, *fadein*, and *fadeout*. *freq*
and *volume* are used to set the frequency and the volume of the **Beep**.
*freq* defaults to 400 Hz and *volume* defaults to .5 the max system volume.
*fadein* and *fadeout* are in seconds, and they represent the time it takes to
get from 0 to *volume* and *volume* to 0 respectively.

Below is an example of a beep at 555hz for 2 seconds with no fade in or out
while at 50% volume:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Beep(freq=555, volume=0.5, duration=2)

    exp.run()

For more details, see the :py:class:`~smile.audio.Beep` docstring.

SoundFile
---------

:py:class:`~smile.audio.SoundFile` is a state that plays a sound file - such as
an mp3 - for a *duration* that defaults to the duration of the file. The
parameter used to interface with the output of this state is *filename*.
*filename* is the path name to the sound file saved on the computer. *volume* is
a float from 1 to 0 where 1 is the max system volume.

The *start* parameter allows for sound files to begin at the desired point in
the audio file. By using the *start* parameter, the audio will begin however
many seconds into the audio file as desired.

The *end* parameter allows for sound files to end before the original end of the
audio. The *end* parameter must be set to however many seconds from the
beginning of the sound file it is desired to end at. The parameter must be
greater than the value of *start*.

If the *loop* parameter is set to True, the sound file will run on a loop for
the *duration* of the **State**.

Below is an example of playing a sound file at path "test_sound.mp3" at 50%
volume for the full duration of the sound file:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    SoundFile(source="test_sound.mp3", volume=0.5)

    exp.run()

For more details, see the :py:class:`~smile.audio.SoundFile` docstring.

RecordSoundFile
---------------

:py:class:`~smile.audio.RecordSoundFile` will record any sound coming into a
microphone for the *duration* of the state. The audio recording will be saved to
an audio file named after what is passed into the *filename* parameter.

Below is an example of recording sound for 10 seconds while looking at a Label
that says "PLEASE TALK TO YOUR COMPUTER". It then saves the recording as
"new_sound.mp3":

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Label(text="PLEASE TALK TO YOUR COMPUTER")
    # UntilDone to cancel the label after the sound file
    # is done recording.
    with UntilDone():
        RecordSoundFile(filename="new_sound.mp3", duration = 10)

    exp.run()

For more details, see the :py:class:`~smile.audio.RecordSoundFile` docstring.

KeyPress
--------

:py:class:`~smile.keyboard.KeyPress` is an input state that waits for a keyboard
press during its *duration*. A list of strings can be passed in as parameters
that are acceptable keyboard buttons into *keys*. A correct key can be selected
by passing in its string name as a parameter to *correct_resp*.

Access to the information about the **KeyPress** state by can be achieved by
using the following attributes:

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

For more details, see the :py:class:`~smile.keyboard.KeyPress` docstring.

KeyRecord
---------

:py:class:`~smile.keybaord.KeyRecord` is an input state that records all of the
keyboard inputs for its *duration*. This state will write out each keypress
during its *duration* to a *.slog* file.

The following example will save out a `.slog` file into log_bob.slog after
recording all of the keypresses during a 10 second period:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    KeyRecord(name="Bob", duration = 10)

    exp.run()

For more details, see the :py:class:`~smile.keybaord.KeyRecord` docstring.

MouseCursor
-----------

:py:class:`~smile.mouse.MouseCursor` is a visual state that shows the mouse for
its *duration*. In order to effectively use **ButtonPress** and **Button**
states, **MouseCursor** in parallel must be used. Refer to the **ButtonPress**
example in the SMILE tutorial page for more information.

The cursor image and the offset of the image can also be set as parameters
to this state. Any image passed in filename will be presented on the screen,
replacing the default mouse cursor.

The following example is of a mouse cursor that needs to be presented with an
imaginary image to be displayed as the cursor. Since the imaginary image is
100 by 100 pixels, and it points to the center of the image, we want the offset
of the cursor to be (50,50) so that the actual *click* of the mouse is in the
correct location:

.. code-block:: python

    from smile.common import *

    exp = experiment()

    MouseCursor(duration = 10, filename="mouse_test_pointer.png",
                offset=(50,50))

    exp.run()

For more details, see the :py:class:`~smile.mouse.MouseCursor` docstring.

For more useful mouse tutorials, see the **Mouse Stuff** section of the Tutorial
document.

Button
------

:py:class:`~smile.video.Button` is a visual and an input state that draws a
button on the screen with optional text in the button for a specified
*duration*. Every button can be set to have a *name* that can be referenced by
:py:class:`~smile.video.ButtonPress` states to determine if the *correct* button
was pressed. See the SMILE tutorial example for *ButtonPress* for more information.

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

For more details, see the :py:class:`~smile.video.Button` docstring.

ButtonPress
-----------

:py:class:`~smile.video.ButtonPress` is a parent state, much like
:py:class:`~smile.state.Parallel`, that will run until a button inside of it is
pressed. When defining a **ButtonPress** state, The name of a button inside of
the parent state can be designated as the correct button to press by passing the
string *name* of the correct **Button** or **Buttons** into the *correct_resp*
parameter. Refer to the **ButtonPress** example in the SMILE tutorial document.

The following is an example of choosing between 3 buttons where only one of the
buttons is the correct button to click:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    # A ButtonPress will end whenever one of its child buttons
    # is pressed.
    with ButtonPress(correct_resp=['First_Choice']) as bp:
        # Required to do anything with buttons.
        MouseCursor()
        Label(text="Choose WISELY")
        # Define both buttons, giving both unique names
        Button(name="First_Choice",text="LEFT CHOICE",
               center_x=exp.screen.center_x-200)
        Button(name="Second_Choice",text="RIGHT CHOICE",
               center_x=exp.screen.center_x+200)
    Label(text=bp.pressed, duration=2)

    exp.run()

For more details, see the :py:class:`~smile.video.ButtonPress` docstring.

Interactive Widgets
-------------------

Each **Interactive Widget** listed below has a brief description in the video.py
docstrings. They are used whenever you need to create an interactive page in
SMILE. Most of these are very useful in questionnaires, and some of them are
used within a ButtonPress state.

    - :py:class:`~smile.video.Slider`

    - :py:class:`~smile.video.TextInput`

    - :py:class:`~smile.video.ToggleButton`

    - :py:class:`~smile.video.CheckBox`

    - :py:class:`~smile.video.ProgressBar`

The parameters for each of these vary, but just like any other SMILE state,
they take the same parameters as the default *State* class. They are Kivy
widgets wrapped in our *WidgetState* class. Kivy documentation can be referred
to for understanding how to use them or what parameters they take.

Kivy Layouts
------------

Each **Kivy Layout** allows you to put widget states on the screen with different
positioning rules. **FloatLayout** is the default layout of any SMILE
experiment, which allows you to place widgets relative to the bottom right of
the screen.

    - AnchorLayout

    - BoxLayout

    - FloatLayout

    - RelativeLayout

    - GridLayout

    - PageLayout

    - ScatterLayout

    - StackLayout

    - ScrollView

Each layout borrows its rules from the corrisponding kivy layout. If you would
like more information on how each layout works, please view the page on layouts
over on `the kivy website.<https://kivy.org/docs/gettingstarted/layouts.html>`_
Most of the parameters map on to parameters that work directly with SMILE.