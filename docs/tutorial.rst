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

    - :ref:`Step 6: If, Elif, Else, and Conditional Refs<conditional_refs>`_

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

The Experiment Break-Down
=========================

The following tutorial teaches you how to code a smile experiment, from showing
you how to code up a basic experiment, to the best practices for timing user
input and visual states. The experiment described below is a made up Priming
Effect tutorial that presents the participant with a cirlce stimuli that is
on the left or the right side of the screen that is either red or green. After
that, a green and a red rectangle appear on the left or right side of the screen.
The participant will then need to indicate which side the screen the green rectangle
has appeared on as quickly as possible.

Each step builds on the last, and by the end of this tutorial you should have a
basic understanding of all of SMILE's ins and outs. Each step contains the
finished code with comments explaining each line of code that we add for each
step. After the finished code will be a more flushed out description of what we
do in the step.

As will all other programming tutorials, lets start with the Hello World example!

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

.. code-block:: python

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

Now that we have a better grasp on the flow states of SMILE, we will need to
add some user input to our experiment. This next section will go over some
how to use UntilDone states, KeyPress states, and how to properly time your
input.

.. _user_input

Step 4: User Input, UntilDone, and Meanwhile
++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: python

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
Earlier in the experiment we made use of the :py:class:`~smile.state.UntilDone`
state when creating an instructions screen. An UntilDone is a Parent state that
will run its children serially(one after the other) in parallel with the
previous state, just like the Meanwhile, but once its children are done running
it will cancel the previous state(the opposite of the Meanwhile). Both states
will be useful in different situations but it takes some time to master when
each one is the most useful.

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

.. code-block:: python

    from smile.common import *
    import random

    # Because our experiment is starting to get more complicated, we use a line
    # like this or a predefined function to create a list of dictionaries that
    # contains all of the information that SMILE will need to run each *trial*
    # of your experiment. Ours is simple and every trial will only need to know
    # what color goes on what side.
    block = [{'left_color': 'RED', 'right_color': 'GREEN', 'correct_key':'J'}]*50 + [{'left_color': 'GREEN', 'right_color': 'RED', 'correct_key':'F'}]*50
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
            # We created our list of dictionaries to include every peice of
            # information that we need in each trial. That includes which
            # key will be the correct key to press.
            kp = KeyPress(keys=['F','J'], correct_resp=trial.current['correct_key'])

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
attributes, a *func* and a *value*. SMILE will know when the result of a ref is
needed by the experiment, and then attempt to evaluate it by passing the *value*
into the *func*. *Ref*s allow you to reference the values of widths, heights,
or any value that isn't defined until the experiment is running during
*Build Time*. *Ref*s are also recursive. If a Ref's *value* is another Ref, it
will attempt to evaluate the value of that Ref before passing it into the
*func*. For more information about Refs, including the ability to use normal
opperators(+, -, *, /) on them and how they interact with lists, please refer
to the :ref:`SMILE References<setting_in_rt>`_ document in the Advanced SMILE
section.

Understanding Refs is important to understanding all of the more complicated
states in SMILE. The :py:class:'~smile.state.Loop' state was introduced in this
step. Loop will allow you to run chunks of your experiment multiple times. The
ammount of times that a Loop will run can be set in many different ways. Above,
we pass in a list of dictionaries to our Loop that will tell the loop to run
for as many times as the length of the list. Since *block* has a length of 100,
our loop will run 100 times. You can also pass in an integer to the loop to
tell it to run a set number of times. Lastly, you can tell a Loop to loop while
a Ref evaluates to True. For more information about the many uses of a Loop
state, please look at the :ref:`SMILE States<smile_states>`_ document.

If you understand the pythonic *with* and *as* statements, you know that when
we write the line `with Loop(block) as trial:` the variable *trial* will
containt the object created by *Loop(block)*. Since we do not have access to
the current item from *block* during build time, we use the *trial.current* Ref
to reference the current value of each iteration of the loop. You can also
reference the loop number with the Ref *trial.i*. You are able to treat
*trial.current* as if it was one of the items in the list *block*. Since
*block* contains a list of dictionaries, you can index into *trial.current*
using the same strings that we setup above, ala *trial.current['left_color']*.

.. warning::

    Whether it be a list or a dictionary, you cannot use a ref to index into either of these objects. For example, if you wanted to index into *ex_list* with *trial.current['index_num']*, you can't do `ex_list[trial.current['index_num']]`. This line will error out by saying that the index is invalid. Instead, refer to the documentation for *Ref.getitem()* for the way to index into an object with a Ref.

Now that we have a better understanding of Refs and build time vs run time, we
can now move onto more complicated applications of these concepts. Mainly, the
next section will cover the conditional States, If, Elif, and Else, as well as
the conditional Refs, *Ref.cond*.

.. _conditional_refs

Step 6: If, Elif, Else, and Conditional Refs
++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: python

    from smile.common import *
    import random
    # Now we are creating a list of dictionaries that has all of our conditions
    # in it. The *prime_* keys are associated with the new conditional that
    # we are adding to our experiment.
    block = [{'left_color': 'RED', 'right_color': 'GREEN', 'correct_key':'J', 'prime_side':'left','prime_color':'RED'}]*10 + \
            [{'left_color': 'RED', 'right_color': 'GREEN', 'correct_key':'J', 'prime_side':'left','prime_color':'GREEN'}]*10 + \
            [{'left_color': 'RED', 'right_color': 'GREEN', 'correct_key':'J', 'prime_side':'right','prime_color':'RED'}]*10 + \
            [{'left_color': 'RED', 'right_color': 'GREEN', 'correct_key':'J', 'prime_side':'right','prime_color':'GREEN'}]*10 + \
            [{'left_color': 'GREEN', 'right_color': 'RED', 'correct_key':'F', 'prime_side':'left','prime_color':'RED'}]*10 + \
            [{'left_color': 'GREEN', 'right_color': 'RED', 'correct_key':'F', 'prime_side':'left','prime_color':'GREEN'}]*10 + \
            [{'left_color': 'GREEN', 'right_color': 'RED', 'correct_key':'F', 'prime_side':'right','prime_color':'RED'}]*10 + \
            [{'left_color': 'GREEN', 'right_color': 'RED', 'correct_key':'F', 'prime_side':'right','prime_color':'GREEN'}]*10

    # Priming shape on screen Duration
    PRIME_DUR = .2
    # Between priming  and stim duration
    PRIME_ISI = .2
    # Stimulus duration
    STIM_DUR = 2.
    INTER_TRIAL_INTERVAL=1.
    INTER_TRIAL_JITTER=.5
    random.shuffle(block)

    exp = Experiment()

    Label(Text="Press F if the left rectangle is green and J if the right rectangle is green. The experiment will begin when you press ENTER.",
          text_size=(500, None), font_size=30, duration=4.)
    with UntilDone():
        KeyPress(keys=["ENTER"])
    Wait(2)

    With Loop(block) as trial:

        # We are finally ready to add the priming stimulus to the screen! We
        # will present a circle on a side of the screen that depends on which
        # trial of the Loop we are on.  The color of the circle will also
        # depend on the trial that we are on in the Loop. We use Ref.cond to
        # make Ref's whos value will change depending on the value of the
        # conditional, true or false.
        exp.prime_center_x = Ref.cond(trial.current['prime_side'] == "LEFT",
                                      true_value=exp.screen.width/4.,
                                      false_value=exp.screen.width*3./4.)

        # Setup the Priming Ellipse that will be shown before our actual trial
        # using both the ref we defined about and the 'prime_color' key from
        # our dictionary.
        prime_ell = Ellipse(center_x=exp.prime_center_x,
                            color=trial.current['prime_color'],
                            duration=PRIME_DUR)

        Wait(PRIME_ISI)

        With Parallel():
            Rectangle(center_x=exp.screen.width/4.,
                             center_y=exp.screen.height/2.,
                             color=trial.current['left_color'],
                             duration=STIM_DUR)
            Rectangle(center_x=exp.screen.width*3./4.,
                             center_y=exp.screen.height/2.,
                             color=trial.current['right_color'],
                             duration=STIM_DUR)
        with Meanwhile():
            kp = KeyPress(keys=['F','J'],
                          correct_resp=trial.current['correct_key'])


        # Utilizing the If and Else states, we are able to provide feedback to
        # our participants. If kp.correct is True, we will show "Correct!" in
        # Green on the screen, if kp.correct is False, we will show "Incorrect!"
        # in red.
        with If(kp.correct):
            Label(text="CORRECT!", color="GREEN", font_size=35, duration=2.)
        with Else():
            Label(text="INCORRECT!", color="RED", font_size=35, duration=2.)

        # Jitter allows you to create random duration waits that will last
        # duration and duration+jitter seconds.
        Wait(INTER_TRIAL_INVERVAL, jitter=INTER_TRIAL_JITTER)

    exp.run()

Now that we have a good understanding of build time vs run time, we can
introduce how SMILE handles conditionals. We have special states that allow you
to run sections of your state machine based on the results of a conditional.
These states are called the :py:class:`~smile.state.If`,
:py:class:`~smile.state.Elif`, and :py:class:`~smile.state.Else` states. If the
conditional that is passed into the *If* state evaluates as true, then the child
states of that *If* state will run. The same applies to the *Elif* state and its
 children. If all of the conditionals within the *If* state and the *Elif*
states evaluate to False, then the children of the *Else* state will run.

Refs also have the ability to be initialized with condtionals. We make use of
*Ref.cond* to create a ref that has one value if the conditional evaluates to
True, and another value if it evaluates to False. You can make good use of
*Ref.cond* if your experiment has many complex variables and conditionals.

*Loop* states also have a conditional parameter to them. Regardless of the
other parameters passed into your Loop, if the *conditional* you pass in
evaluates to False, then the Loop will not start its next iteration. This is
how you do While loops using SMILE state machines.

.. warning::

    If you are constructing conditionals that might contain a Ref object, you must use the '&' or '|' operators instead of using 'and' or 'or'. Refs cannot handle the 'and' and 'or' keywords.

Now that you have a basic understanding of how to create an experiment in
SMILE, it is important that we go over how to *Log* your data properly. We will
also go over the best practices that are needed to properly time the different
events in smile.


.. _timing_logging

Step 7: Logging and Good Timing Practices
+++++++++++++++++++++++++++++++++++++++++

.. code-block:: python

    from smile.common import *
    import random

    block = [{'left_color': 'RED', 'right_color': 'GREEN', 'correct_key':'J', 'prime_side':'left','prime_color':'RED'}]*10 + \
            [{'left_color': 'RED', 'right_color': 'GREEN', 'correct_key':'J', 'prime_side':'left','prime_color':'GREEN'}]*10 + \
            [{'left_color': 'RED', 'right_color': 'GREEN', 'correct_key':'J', 'prime_side':'right','prime_color':'RED'}]*10 + \
            [{'left_color': 'RED', 'right_color': 'GREEN', 'correct_key':'J', 'prime_side':'right','prime_color':'GREEN'}]*10 + \
            [{'left_color': 'GREEN', 'right_color': 'RED', 'correct_key':'F', 'prime_side':'left','prime_color':'RED'}]*10 + \
            [{'left_color': 'GREEN', 'right_color': 'RED', 'correct_key':'F', 'prime_side':'left','prime_color':'GREEN'}]*10 + \
            [{'left_color': 'GREEN', 'right_color': 'RED', 'correct_key':'F', 'prime_side':'right','prime_color':'RED'}]*10 + \
            [{'left_color': 'GREEN', 'right_color': 'RED', 'correct_key':'F', 'prime_side':'right','prime_color':'GREEN'}]*10


    PRIME_DUR = .2
    PRIME_ISI = .2
    STIM_DUR = 2.
    INTER_TRIAL_INTERVAL=1.
    INTER_TRIAL_JITTER=.5

    random.shuffle(block)

    exp = Experiment()

    Label(Text="Press F if the left rectangle is green and J if the right rectangle is green. The experiment will begin when you press ENTER.",
          text_size=(500, None), font_size=30, duration=4.)
    with UntilDone():
        KeyPress(keys=["ENTER"])
    Wait(2)

    With Loop(block) as trial:

        exp.prime_center_x = Ref.cond(trial.current['prime_side'] == "LEFT",
                                      true_value=exp.screen.width/4.,
                                      false_value=exp.screen.width*3./4.)

        prime_ell = Ellipse(center_x=exp.prime_center_x,
                            color=trial.current['prime_color'],
                            duration=PRIME_DUR)

        # Wait(until) will not end *until* prime_ell.disappear_time is not None
        Wait(until=prime_ell.disappear_time)

        # ResetClock will ensure that the next ensure that the next state, i.e.
        # Wait, will calculate its end time based upon the
        # prime_ell.disappear_time, and not its "start time". You want to use
        # ResetClock right before a state whose timing you need ensured to be
        # accurate. In this case, we want to make sure that the stimulus
        # rectangles come on the screen exactly PRIME_ISI seconds after the
        # priming ellipse.
        ResetClock(prime_ell.disappear_time['time'])
        Wait(PRIME_ISI)

        With Parallel():
            rec1 = Rectangle(center_x=exp.screen.width/4.,
                             center_y=exp.screen.height/2.,
                             color=trial.current['left_color'],
                             duration=STIM_DUR)
            rec2 = Rectangle(center_x=exp.screen.width*3./4.,
                             center_y=exp.screen.height/2.,
                             color=trial.current['right_color'],
                             duration=STIM_DUR)
        with Meanwhile():
            # KeyPress will the *base_time* parameter to calculate the
            # reaction time (rt) after a key is pressed.
            #  rt = press_time - base_time
            kp = KeyPress(keys=['F','J'],
                          correct_resp=trial.current['correct_key'],
                          base_time=rec1.appear_time['time'])

        Wait(.2)

        # The first argument is the dictionary *trial.current* which will save
        # out each key as a different column in our .slog. Our slog file name
        # will be *log_[name].slog* where *name* is the name parameter of
        # this state. We log everything that we could possibly need for later
        # analysis, including the appear and disappear times of important
        # stimuli and all of the info about each keypress. Each Keyword argument
        # that goes into the Log state will be turned into a separate column.
        Log(trial.current,
            name="PrimingEffect",
            prime_appear=prime_ell.appear_time,
            prime_disappear=prime_ell.disappear_time,
            stim_appear=rec1.appear_time,
            stim_disappear=rec1.disappear_time,
            correct=kp.correct,
            resp=kp.pressed,
            rt=kp.rt,
            base_time=kp.base_time,
            press_time=kp.press_time)

        with If(kp.correct):
            Label(text="CORRECT!", color="GREEN", font_size=35, duration=2.)
        with Else():
            Label(text="INCORRECT!", color="RED", font_size=35, duration=2.)

        Wait(INTER_TRIAL_INVERVAL, jitter=INTER_TRIAL_JITTER)

    exp.run()

In this section, we add in a few states that are vital for someone to
analyze our experiment. The :py:class:`~smile.state.Log` state allows us to
aggrigate all of the information important to analysis in one place, and the
:py:class:`~smile.state.ResetClock` state allows us to garuntee the timing of
certain states.

The *ResetClock* state takes in a time and then bases the next state's end time
on that time. In the case above, we used ResetClock to garuntee that our *Wait*
between the priming stimulus and the testing stimulus ended exactly PRIME_ISI
after the disappear_time of the *prime_ell*, not PRIME_ISI after the start of
the wait. If timing is important to your expierment, you will want to use
*ResetClock* every time you have a non_visual state that has a duration.
*ResetClock* should also only have a time passed into it that is definite. The
only times in SMILE that are the appear and disappear times of visual stimulus.
If you want to learn more about timing and why appear and disappear times are
definite, please read the :ref:`Timing<advanced_timing>`_ section of
*Advanced Smiling*.

.. warning::

    Using ResetClock correctly can give you better control over the timing of things in your experiment. Using ResetClock incorrectly can break everything and cause very unexpected timing errors. Use with Caution.

The *Log* state allows you to save out specific information to a .slog file.
SMILE, by default, saves out everything related to every state during your
experiment. It saves these data into a directory, depending on your OS, that
looks like *data/[experiemnt name]/[subject ID]/[log_file].slog*. The experiment
name can be passed into *Experiment* via the *name* parameter, and by default
it is "Smile". SMILE will create a separate file for each kind of state that
you use in your experiment. For example, each row in *state_Parallel.slog* will
be a different instance of the *Parallel* state, containing each peice of
information about them in different columns. The kinds of things that get logged
into the default state loggers are outlined in the docstrings of each state.
Because it would be difficult and time consuming to slog (get it?) through all
of those files, we created the *Log* state to allow you to just save out the
information that you think is important to your analysis later. Each
keyword arugment that you pass into the Log state will be a separate column in
your data.

.. note::

    A note about .slog files : each new line is compressed and writen to the end of the file during runtime. If you experiment, for whatever reason, crashes midway through running, you wont lose all of the data that you collected up until that point. All of that data will have already been saved out and you will be able to access it with our myriade of slog reading functions.

Lastly, we used the *base_time* parameter in the KeyPress state. Every input
state that cacluates a reaction time will be able to take a *base_time* as a
parameter. The forumla for reaction time of an input is as follows :

.. code:: python

    rt = action_time - base_time

The reaction time is the time since the base time, when an action occurs. Most
experiments want to know a reaction time based on when something came on to or
off of the screen. In our case, we wanted to know how long after the appear_time
of the rectangle stimuli did they press a key, so our *base_time* needed to be
set to the appear_time of the rectangle.

.. note::

    *appear_time* and *disappear_time* are Events meaning they have a 'time' key and an 'error' key. 'error' will always be 0, so you need to pass *appear_time['time']* into basetime.


And there you go!
=================

Now that you have finished the tutorial, you can move on to the other, more
advanced concepts in SMILE. The next section of this documentation will take
your through the different states in SMILE and give you a brief description as
to why they are useful. Later you will be able to go checkout some real life
examples of experiments coded in SMILE, like Sternberg, Stroop, Free Recall, and
IAT Mouse tracking.
