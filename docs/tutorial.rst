======================
SMILE Tutorial Basics!
======================

Hello SMILErs! This tutorial is for people just starting out in the world of
SMILE. This document will start of giving a description of the experiment we
will eventually create, and then go into sections detailing how we will build
that experiment from the ground up. Each section will introduce a new concept
that you will need to understand in order to be a successful SMILEr! Once you
complete this tutorial, you can read other documents that better explain the
more advanced use cases for all of the different smile *States* as well as
fully coded psychology experiments like the Flanker task and the Stroop task.

For your conveniance, here is a table of contents for this document to better
help you find the information you are looking for.

    - :ref:`Step 1: Hello, World!<hello_world>`_

    - :ref:`Step 2: Position, Size, and other Parameters<pos_size_par>`_

    - :ref:`Step 3: Timing, in Parallel and in Serial!<parallel_serial_time>`_

    - :ref:`Step 4: User Input, UntilDone, and Meanwhile<user_input>`_

    - :ref:`Step 5: Looping, References, and Animation<loops_ref>`_

The Experiment Break-Down
=========================

Blah Blah Blah Video Blah BLah Blah

.. _hello_world:

Step 1: Hello, World!
+++++++++++++++++++++

.. code-block:: python

    # Import all of the SMILE states that are common to all platforms
    from smile.common import *

    # Initialize the Experiment
    exp = Experiment()

    # Label is an action state in SMILE. A Label shows text on the screen
    lbl = Label(text="Hello, World!")

    # After defining the experiment above, tell the Experiment that you are
    # ready to run!
    exp.run()

Above is the most basic SMILE experiment that anyone could possibly write. In
order to run the above experiment from a command line, you must first copy and
paste the above code into a *.py* file. You should be able to run SMILE like any
other python script using the *python filename.py* in your preferred command
line program. There are command line arguments that you can add to the above
command but we will talk about that later in the
:ref:`Command Line Arguments <command_line>` section of these docs.

The most important part about the above code are the lines *exp = Experiment()*
and *exp.run()*.  SMILE is a state machine. That means you first build up the
experiment by defining the different states, then tell your machine to run. In
order for your SMILE experiment to function properly, you must define all of
your states between the lines *exp = Experiment()* and *exp.run()*.

Lets move onto Positioning, Sizing, and Parameters!

.. _pos_size_par:

Step 2: Position, Size, and other Parameters
++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: python


    from smile.common import *

    exp = Experiment()

    # text and font_size are parameters of the Label state.
    # Words like bottom, left, y, and center_x are words
    # used as positional parameters for WidgetStates.
    Label(text="Press Enter to Start!", center_x=exp.screen.center_x,
          bottom=exp.screen.bottom+50, font_size=30)

    exp.run()

There are many different things you can do with a :py:class:`~smile.video.Label`
state. You can make it multi-lined, you can make giant font, you can change the
font type, and you can set where you want it to display onto the screen. This is
because Label is a :py:class:`~smile.video.WidgetState`. WidgetState is the base
class on which all States that have a visual component to them are built upon.
WidgetStates are positional, meaning you can give them position arguments as
parameters and you can use their positional attributes when defining other
WidgetStates.

The parameters you can use to define a WidgetState's position and size include
x, y, height, and width but also include the less obvious parameters bottom,
top, left, and right. You can also refer to the center_x and center_y value of a
WidgetState's position. When defining a WidgetState's position you are only
allowed to pass in one piece of information about the X position and one piece
of information about the Y position. You can't pass in both the top and bottom
parameters and expect the height to be filled in correctly. Positional
parameters and size parameters must be passed in independently of each other.

    - DO: Define a rectangle as *Rectangle(center_x=50, top = 100, width=200, height=200)*.

    - DO NOT: Define a rectangle as *Rectangle(left=50, right=100, top=100, bottom=50)* in an attempt to set the height and width.

For more information about the different parameters each state can take in,
please refer first to the list of :ref:`SMILE States<smile_states>`_ and then to
the docstrings for each individual state. For more information about positioning
SMILE WidgetStates, please refer to the
:ref:`Screen Placement of Visual States<screen_placement>`_ section of our
Advanced SMILEing document.

Now that we know more about positioning, lets put more things on the screen!

.. _parallel_serial_time:

Step 3: Timing, in Parallel and in Serial!
++++++++++++++++++++++++++++++++++++++++++

.. code-block: python

    from smile.common import *

    exp = Experiment()

    # 3 seconds after it appears, this Label will disappear from the screen.
    # This is because we told this state that it should remain on the screen for
    # 3 seconds with the duration parameter.
    Label(text="Get Ready to Start!", center_x=exp.screen.center_x,
          bottom=exp.screen.bottom+50, font_size=30, duration=3)

    # Wait is a flow state that tells SMILE to delay the start of the next state
    # by whatever duration is passed into it.
    Wait(2)

    # Parallel is a flow state that will run all of the states inside of it
    # at the same time, e.g. in parallel! The states inside of a Parent State
    # like Parallel are referred to as its children.
    With Parallel():

        # We want this rectangle to be on the left middle of the screen. As a
        # child of the above Parallel state, this rectangle and the rectangle
        # below will appear at the same time. We will make this rectangle Red.
        Rectangle(center_x=exp.screen.width/4.,center_y=exp.screen.height/2.,
                 color="RED", duration=2.)

        # We want this rectangle to be on the right middle of the screen. We are
        # able to use the screen size in our calculations for position. This
        # state will appear at the exact same time as the other child of the
        # Parallel.
        Rectangle(center_x=exp.screen.width*3./4.,center_y=exp.screen.height/2.,
                 color="GREEN", duration=2.)

    exp.run()

Timing is one of the most important things when it comes to running psychology
experiments. When designing SMILE, we wanted to make sure it was easy for you to
program an experiment that does exactly what you want it to do. With that idea
in mind, we made it so that all of the Action (visual or auditory) states in
SMILE have a duration. This is so you can define exactly how long you want
anything to happen in SMILE. Once one state ends, the next state will
immediately begin.

We can also control the timing of states using the *flow states* of SMILE. These
states include Serial, Parallel, Loop, If, Wait, and a few more complicated
states like UntilDone and Meanwhile. For more information about these states,
please view the :ref:`SMILE States<smile_states>`_ document or their individual
docstrings.

For the next step in building our experiment, we needed to add some rectangles
onto the screen a few seconds after our *start?* label disappears from the
screen. We accomplished this with the :py:class:'~smile.state.Wait' state, which
tells SMILE to delay the start of the next state (or states) for the duration of
the wait.

After that, we needed to have multiple Rectangles appear at the same time.
:py:class:'~smile.state.Parallel' is the perfect state for this. When a Parallel
state starts, it will start all of its children at the same time. A Parallel
state ends when all of its children are done running. You can also use multiple
Parallels and Serials hierarchically in that you can have a set of states
running in serial of each other at the same time that a bunch of states are
running in parallel.

Because the Parallel state is so complicated, I recommend reading the Parallel
section of the :ref:`SMILE States<smile_states>`_ document. It explains some of
the more complicated functionality of a Parallel state.

MAYBE ADD MORE?

Now that we have a better grasp on the flow states of SMILE, we will need to
add some user input to our experiment. This next section will go over some
how to use UntilDone states, KeyPress states, and how to properly time your
input.

.. _user_input

Step 4: User Input, UntilDone, and Meanwhile
++++++++++++++++++++++++++++++++++++++++++++

.. code-block: python

    from smile.common import *

    exp = Experiment()

    Label(text="Press Enter to Start!", center_x=exp.screen.center_x,
          bottom=exp.screen.bottom+50, font_size=30)

    # UntilDone is a state that runs its children in parallel with the previous
    # state. When the children of the children of the UntilDone finish running,
    # the previous state will be canceled, even if it means ending early.
    with UntilDone():
        KeyPress(keys=["ENTER"])

    Wait(2)

    # We added in this label to give our participants a little more direction.
    # Notice text_size and font_size. text_size is a parameter that dictates the
    # size of the Label, in the form of (width, height) in pixels. If None is
    # passed into the height, you have created a multi-line Label with a fixed
    # max width.
    Label(Text="Press F for left and J for right. The experiment will begin momentarily", text_size=(500, None),
          font_size=30, duration=4.)

    Wait(2)

    With Parallel():
        Rectangle(center_x=exp.screen.width/4.,center_y=exp.screen.height/2.,
                 color='RED', duration=2.)
        Rectangle(center_x=exp.screen.width*3./4.,center_y=exp.screen.height/2.,
                 color='GREEN', duration=2.)

    # Meanwhile, like UntilDone, runs its children in parallel of the previous
    # state. The difference is that when the previous state finishes, the
    # children of the meanwhile will be canceled, even if it means ending early.
    with Meanwhile():

        # You can provide a list of acceptable keys into a KeyPress state. This
        # state will only accept those keys as input. you are able to access the
        # response key and the correctness of the response via the attributes
        # "pressed" and "correct". kp.correct would return True if they pressed
        # the J key in this case.
        kp = KeyPress(keys=['F','J'], correct_resp='J',)

    exp.run()

SMILE has two main forms of input to an experiment. It has Keyboard input
through the :py:class:'~smile.keyboard.KeyPress' state, and mouse input via the
:py:class:'~smile.mouse.MousePress' state. The third form of input is the
:py:class:'~smile.video.ButtonPress' Parent state that works with the visual
:py:class:'~smile.video.Button' state. All of these states have the ability for
you to choose the buttons or keys that are *legal* inputs, pick the input that
is the correct response, and even give it a time in which to base the reaction
time of the state.

For our experiment, we want to record a KeyPress while the rectangles are on
the screen. In order to do this right, we need to use one of our Flow States
called the :py:class:'~smile.state.Meanwhile' state. A Meanwhile is a Parent
state that will run its children serially(one after the other) in parallel with
the previous state, and cancel its children when the previous state has ended.
Earlier in the experiment we made use of the UntilDone state when creating an
instructions screen. An UntilDone is a Parent state that will run its children
serially(one after the other) in parallel with the previous state, just like
the Meanwhile, but once its children are done running it will cancel the
previous state(the opposite of the Meanwhile). Both states will be useful in
different situations but it takes some time to master when each one is the most
useful.

.. note::

    A simple trick to figure out whether to use a Meanwhile state or an UntilDone state is to listen to the word you use when describing the situation. If you want to do something until something else is done, you would use the UntilDone state. If you want to do something while something else is happening, you would use the Meanwhile state.

Pay attention to the Meanwhile in our above experiment. Meanwhiles, like the
UntilDone states, will run their children in parallel of the previous state. In
our case, the previous state is a Parallel with our Rectangles in it. This
means you will be able to input a key for KeyPress as long as that Parallel
hasn't ended. Since our experiment is a 2 choice task, we are able to set the
*keys* parameter of KeyPress as 'F' and 'J'. We also want to set our correct
response through the correct_resp parameter. Eventaully, our correct response
will be different depending on where we are in the experiment, but for now we
just set the correct_resp to be 'J'.

At this point in the tutorial, we have a few states that all run once. In order
run things many times with many different conditions, we will need to introduce
our next SMILE flow state, the Loop State.

.. _loops_ref

Step 5: Looping, References, and Animation
++++++++++++++++++++++++++++++++++++++++++

.. code-block: python

    from smile.common import *
    import random

    # Because our experiment is starting to get more complicated, we use a line
    # like this or a predefined function to create a list of dictionaries that
    # contains all of the information that SMILE will need to run each *trial*
    # of your experiment. Ours is simple and every trial will only need to know
    # what color goes on what side.
    block = [{'left_color': 'RED', 'right_color': 'GREEN'}]*10 + [{'left_color': 'GREEN', 'right_color': 'RED'}]*90
    random.shuffle(block)

    exp = Experiment()

    Label(Text="Press F if the left rectangle is green and J if the right rectangle is green. The experiment will begin when you press ENTER.",
          text_size=(500, None), font_size=30, duration=4.)
    with UntilDone():
        KeyPress(keys=["ENTER"])
    Wait(2)



    # Loop is a Parent State that will run its children as many times as you
    # want. In the case below, the Loop will run for as many iterations as there
    # are items in the list *block*. There are 100 trials defined above, so our
    # loop will run 100 times. trail is the variable that allows us to the
    # different iterations of each loop. *trial.current* is a reference to the
    # current iteration, and acts as your portal to any information residing
    # inside *block*
    With Loop(block) as trial:
        With Parallel():

            # As you can see below, trial.current is acting as our link to the
            # current iteration of the loop. Since each item in block is a
            # dictionary object, we are able to index into trial.current using
            # the same keys that exist in our dictionary that we setup above.
            Rectangle(center_x=exp.screen.width/4.,center_y=exp.screen.height/2.,
                     color=trial.current['left_color'], duration=2.)
            Rectangle(center_x=exp.screen.width*3./4.,center_y=exp.screen.height/2.,
                     color=trial.current['right_color'], duration=2.)
        with Meanwhile():
            kp = KeyPress(keys=['F','J'], correct_resp='J',)

    exp.run()

At this point in the tutorial, it is going to be important to clarify the
difference between Run time and Build time. Build time is the time between the
declaration of Experiment, 'exp = Experiment()', and when you run your built
experiment with the line 'exp.run()'. Run time is everything after the call to
'exp.run()'. With SMILE you build your experiment up, providing references to
different values between states, and then when you are ready you run it. In
order to allow people to make references to values that might not exist until
the experiment is running, we cre ate the :py:class:'~smile.ref.Ref' object.

A *Ref*, at its simplest, is a delayed function call. It contains two
attributes, a *func* and a *value*, and SMILE identifies when the value of the
Ref is needed and then evaluates



Running a SMILE Experiment
==========================

After installing SMILE, there is only one thing needed to run a SMILE
experiment, and that is a fully coded experiment file. SMILE uses python to run
its experiments, so to run SMILE you must run the *.py* file with python.

If you followed our instructions for installing SMILE, Linux and Windows users
would use the following line in a command prompt to run their SMILE experiments:

::

    >> python filename.py -s SubjectID

If you are an OSX user, you just replace the **python** in the previous line
with **kivy**:

::

    $ kivy filename.py -s SubjectID

Notice the *-s* in the commands above. This is a command line argument for
SMILE. SMILE has 3 command line arguments.

    - *-s* : Subject ID, whatever identifier you would like to use for a particular run of the experiment. The next argument passed *-s* will be the subject ID for the purposes of where to save data on your system.

    - *-f* : Fullscreen, if *-f* is present in the command line, SMILE will run in windowed mode.

    - *-c* : CSV, if -c is present, SMILE will save out all of its *.slog* data files as *.csv* data files as well. **Not Recommended**

Before you learn how to code SMILE experiments, it is important to understand
a few things about how SMILE works. The next section goes over how SMILE
first *builds* then *runs* experiments.

.. _run_build_time:

Build Time V.S. Run Time
========================

The difference between **Build Time** and **Run Time** is the most important
concept to understand when learning to use SMILE. There are 2 lines of
code that designate the start of **BT** and then the start of **RT**. Those
lines are `exp = Experiment()` and `exp.run()` respectively.

`exp = Experiment()` initializes the instance of an :py:class:`~smile.experiment.Experiment`. All calls to a
state must take place after this line! Once this line is run,
**BT** starts.  **BT**, or Experimental Build Time, is the section of the
code that sets up how the experiment will run.

*During Experimental Build Time*, all calls to the different states of SMILE
define how your experiment will run to SMILE. SMILE sees each of those states
and uses them to setup the rules of how your state machine will flow from one
state to another. When SMILE see the *with Parallel():* state, it will know
that all of the states that are defined within should run at the same time.
When SMILE sees one **Label** following another **Label**, SMILE will know
that the second **Label** should not show up on the screen until the first
one has finished running.

*During Experimental Run Time*, all of the timing and intricacies of SMILE's
backend are run. Once *exp.run()* is called, SMILE will start whatever the first
state you defined in the experiment is and continue with the rest of your
experiment afterwards.

.. note::

    During **RT**, SMILE will not run any non-SMILE code. SMILE will only run the prebuilt state-machine. If you need to run any kind of python during your experiment, use the :py:class:`~smile.state.Func` state.

Another thing to look out for when programming the experiment how variables are
set and used in **BT**. A local variable in between *exp = Experiment()* and
*exp.run()* cannot be set and expected to actually set during **RT**.
In order to *set* and *get* local variables during **RT**, *set* and *get*
must be used through the local :py:class:`~smile.experiment.Experiment`
variable. To set this kind of variable, *exp.variable_name* must be added to the
beginning of the variable name. Doing this creates a :py:class:`~smile.experiment.Set`
state in SMILE that will run during **RT**.  An example is as follows.

.. code-block:: python

    exp.variableName = lbl.appear_time['time']

For more information about setting in **RT** see the :ref:`Setting a Variable in RT <setting_in_rt>`
section of **Advanced SMILEing**

.. _ref_def:
