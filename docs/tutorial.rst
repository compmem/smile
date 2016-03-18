================================
SMILE Tutorial Basics!
================================

Hello SMILErs! Today, I will show you how easy it is to start SMILEing! This
tutorial is setup in parts. First, we will show you just how easy it to display
a line of text on the screen.  Second, we will demonstrate how
*stimulus generation* and *experiment code* is 100% separate. Third is a
tutorial about how to added *User Input*. At the bottom of this tutorial are
some special examples for how to do some of the more complicated things in
SMILE.

Hello World, Let's start SMILEing!
================================

To start, I'll show you how the simplest *SMILE* experiment is programmed.
Create a directory called *SmileTest* and add a file named *main.py*

.. code-block:: python
    :linenos:

    from smile.common import *

    exp = Experiment()
    Label(text="Hello World, Lets start Smiling!", duration=4)
    exp.run()

Go ahead and run **main.py**. If you do not know how to run a SMILE program,
please refer to :ref:`Running SMILE <running-smile>` section of our
:ref:`How To SMILE <how-to-smile>` document. You should see a black screen with
the words "Hello World, Lets start Smiling!" appearing on the screen for 5
seconds.  What we have done is create a simple SMILE **experiment**. When we run
``exp = Experiment()`` we are initializing our experiment and telling out python
program that we are about to start defining the states of our program.

As said in our :ref:`How To SMILE <how-to-smile>` page, SMILE is a state machine.
In your SMILE program you are telling the *experiment* what states, in order
defined, it should run. After you have defined the states that your experiment
will go through, you add the line ``exp.run()``. This lets the *experiment*
know that the definition process is complete, and the *experiment* is ready to
run. In the next step, we will see how stimulus generation and stimulus
presentation can be separated with ease in this :py:class:`~smile.state.Loop` state example.

Looping over Lists! In Style
============================

To start this out, let's define the experiment we are going to create. We are
going to present a list of predefined words to the participant for 2 seconds
each and wait 1 second in between each word. Sounds complicated right? Wrong!
With SMILE, all you need to know is a basic idea of what the timing is in your
experiment and SMILE will take care of the rest! Create a new directory
called *exp2* and create a file called *randWord1.py*. In the file, let's define
the stimulus.

.. code-block:: python

    words=['plank', 'dear', 'adopter',
           'initial', 'pull', 'complicated',
           'ascertain', 'biggest']
    random.shuffle(words)

Easy. Now we have a list of words that are randomly sorted. From here, we can
build an experiment that :py:class:`~smile.state.Loop` over the list of words. Let's setup the
preliminary variables.

.. code-block:: python

    #Needed Parameters of the Experiment
    interStimulusDuration=1
    stimulusDuration=2

    #We are ready to start building the Experiment!
    exp = Experiment()


The default state that your :py:class:`~smile.state.Experiment` runs in is the :py:class:`~smile.state.Serial` state.
:py:class:`~smile.state.Serial` just means that every other state defined inside of it is run in
order, first in first out. So every state you define after
``exp = Experiment()`` will be executed fifo style. Next, we will define a
staple of every SMILE experiment, our :py:class:`~smile.state.Loop` state.

.. code-block:: python

    with Loop(words) as trial:
        Label(text=trial.current, duration=stimulusDuration)
        Wait(interStimulusDuration)

    exp.run()

Let's look at what is happening here line by line.
``with Loop(words) as trial:`` has a lot of stuff going on.  You are able to
send your list to *Loop* as a prarameter.  This tells SMILE to loop over
*words*. *Loop* also creates a reference variable, in our case we called it
*trial*. Trial acts as a link between the experiment building state of the
experiment, and the running state of the experiment.  Until ``exp.run()`` is
called, *trial* will not have a value. The next line defines a :py:class:`~smile.video.Label` state
that displays text for a duration. By default, it displays in the middle of the
experiment window. Notice ``trial.current``. In order to access the
numbers from our random list, we need to use ``trial.current`` instead of
``words[x]``. ``trial.current`` is a way to tell SMILE to access the
*current* member of the *words* list while looping.

.. warning::

    Do not try and access or test the value of trial.current. As it is a
    reference variable, you will not be able to test the value of it outside of
    a SMILE state.

Finished **rand_word_1.py**
---------------------------------------

.. code-block:: python
    :linenos:

    from smile.common import *
    import random

    words = ['plank', 'dear', 'adopter',
             'initial', 'pull', 'complicated',
             'ascertain', 'biggest']
    random.shuffle(words)

    #Needed Parameters of the Experiment
    interStimulusDuration=1
    stimulusDuration=2

    #We are ready to start building the Experiment!
    exp = Experiment()
    with Loop(words) as trial:
        Label(text=trial.current, duration=stimulusDuration)
        Wait(interStimulusDuration)

    exp.run()

And Now, With User Input!
=========================

The final step for our basic SMILE tutorial is to add user input and logging.
Let's define the experiment. Let's say we need to ask the participant to press J
if the number of letters on the screen is even, and K if the number of letters
in the word on the screen is odd. We have to say that the participants have
only 4 seconds to answer. In this tutorial, you will learn how to set up
our experiment so that when the participant presses a key to answer, the stimulus
will drop off the screen and start the next iteration of the loop.

This tutorial will also teach you how to compare **trial.current** comparisons.
Create a directory called *WordRemember* and create a file within the directory
called *randWord2.py*. First, we will bring over the word list from the
previous file.  We are going to change it a little bit to make sure that the
experiment will be able to tell what key is the correct key for each trial.

.. code-block:: python

    key_dic = ['J', 'K']
    words = ['plank', 'dear', 'thopter',
             'initial', 'pull', 'complicated',
             'ascertain', 'biggest']
    temp = []
    for i in range(len(words)):
        condition = len(words[i])%2
        temp.append({'stimulus':words[i], 'condition':key_dic[condition]})
    words = temp
    random.shuffle(words)


Our list of words is now a list of dictionaries, in which ``words[x]['stimulus']``
will give us the word and ``words[x]['condtion']`` will give us whether the
word has an even or an odd length. Like in the last example, the next thing we
must do is initialize all of our experiment parameters. **key_list** is what
keys our participant will be pressing later.

.. code-block:: python

    #Needed Parameters of the Experiment
    interStimulusDuration=1
    maxResponseTime=4


    #We are ready to start building the Experiment!
    exp = Experiment()


We changed the line ``stimulusDuration=2`` into ``maxResponseTime=4``. Next, we
are going to setup up our basic loop.

The first thing we need to add to this loop is the ``UntilDone():`` state. An
:py:class:`~smile.state.UntilDone` state is a state that will run its children in :py:class:`~smile.state.Serial` until
the state above it has finished. Here is an example before we edit the
loop.

.. code-block:: python

    ###########EXAMPLE, NOT PART OF EXPERIMENT#########
    Label(text='Im on the screen for at most 5 seconds')
    with UntilDone():
        Label(text='Im On the screen for 3 seconds!', duration=3)
        Wait(2)


As you can see, The first :py:class:`~smile.video.Label` is on the screen for 5 seconds because the
:py:class:`~smile.state.UntilDone` state doesn't end until the second :py:class:`~smile.video.Label` has ran 3 seconds
and the :py:class:`~smile.state.Wait` has ran 2 seconds.

Now we will implement this state into our loop.

.. code-block:: python

    with Loop(words) as trial:
        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=key_dic)
        Wait(interStimulusDuration)
    exp.run()


This displays the current trial's number until you press a key then waits the
inter-stimulus duration that we set earlier.  This isn't exactly what we want,
but it is the start we need to fully understand what we are doing. Next we are
going to edit ``kp = KeyPress(keys=keys)`` to include our response time
duration. We also need to add in the ability to check and see if they answered
correct. This will require the use of `trial.current['condition']`, which is a
listgen value that we set earlier.

.. code-block:: python

    with Loop(words) as trial:
        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=key_dic, duration=maxResponseTime,
                          correct_resp=trial.current['condition'])
        Wait(interStimulusDuration)

    exp.run()

The last thing we need to add to this experiment, at the end of the ``Loop()``,
is the :py:class:`~smile.state.Log`. Wherever you put a :py:class:`~smile.state.Log` state in the experiment, it will
save out a **.slog** file to a folder called *data* in your experiment
directory under whatever name you put in the *name* field.

.. code-block:: python

    Log(name='Loop',
        correct=kp.correct,
        time_to_respond=kp.rt)

With this line, each iteration of the loop in the experiment will save our a
line into *Loop.slog* all of the values defined in the ``Log()`` call. The loop
will look like this

.. code-block:: python

    with Loop(words) as trial:
        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=key_dic, duration=maxResponseTime,
                          correct_resp=trial.current['condition'])
        Wait(interStimulusDuration)
        Log(name='Loop',
            correct=kp.correct,
            time_to_respond=kp.rt)


Finished **rand_word_2.py**
---------------------------

.. code-block:: python
    :linenos:

    from smile.common import *
    import random

    words = ['plank', 'dear', 'thopter',
             'initial', 'pull', 'complicated',
             'ascertain', 'biggest']
    temp = []
    for i in range(len(words)):
        condition = len(words[i])%2
        temp.append({'stimulus':words[i], 'condition':key_dic[condition]})
    words = temp
    random.shuffle(words)

    #Needed Parameters of the Experiment
    interStimulusDuration=1
    maxResponseTime = 4
    key_dic = ['J', 'K']
    #We are ready to start building the Experiment!
    exp = Experiment()

    with Loop(words) as trial:
        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=key_dic, duration=maxResponseTime,
                          correct_resp=trial.current['condition'])
        Wait(interStimulusDuration)
        Log(name='Loop',
            correct=kp.correct,
            time_to_respond=kp.rt)
    exp.run()


Now you are ready to get SMILEing!


Special Examples
================

This section is designed to help you figure out how to use some of the more
advanced states and interesting interactions with some of the states in SMILE.
For more detailed real life examples of experiments, head over to the
:ref:`Full Experiments <full-experiments>` page!

Subroutine
-----------------------------

This is the tutorial that will teach you how to write your own :py:class:`~smile.subroutine`
state and highlight its importance.  In SMILE, a :py:class:`~smile.subroutine` state is used
to compartmentalize a block of states that you are bound to use over and over
again in different experiments. The one we will go over is a list
presentation subroutine.

Let's create a new directory called *ListPresentTest* and then create a new file
in that directory called *list_present.py*.  The first thing we need to do for
our list presentation subroutine is setup the basic imports and define our
subroutine.

.. code-block:: python

    from smile.common import *

    @Subroutine
    def ListPresent(self,
                    listOfWords=[],
                    interStimDur=.5,
                    onStimDur=1,
                    fixation=True,
                    fixDur=1,
                    interOrientDur=.2):



By placing `@Subroutine` above our subroutine definition, we tell the compiler
to treat this as a SMILE :py:class:`~smile.subroutine`. The subroutine will eventually present
a fixation cross, wait, present the stimulus, wait again, and then repeat for
all of the list items you pass it. Just like calling a function or declaring a
state, we will call :py:class:`~smile.subroutine` in the body of our experiment and pass in
those variables in *main_list_present.py*, which we will create later.

.. warning::
    Always have *self* as the first argument when defining a subroutine. If you
    don't, your code will not work as intended.

The cool thing about :py:class:`~smile.subroutine` is that you can access any of the
variables that you declare into `self` outside of the subroutine, so the first
thing we are going to do is add a few of these to our subroutine.

.. code-block:: python

    @Subroutine
    def ListPresent(self,
                    listOfWords=[],
                    interStimDur=.5,
                    onStimDur=1,
                    fixDur=1,
                    interOrientDur=.2):
        self.timing = []

The only variable we will need for testing later is an element to hold all of
our timing information to pass out into the experiment. Next, let's add the
stimulus loop.

.. code-block:: python

    @Subroutine
    def ListPresent(self,
                    listOfWords=[],
                    interStimDur=.5,
                    onStimDur=1,
                    fixDur=1,
                    interOrientDur=.2):
        self.timing = []
        with Loop(listOfWords) as trial:
            fix = Label(text='+', duration=fixDur)
            oriWait = Wait(interOrientDur)
            stim = Label(text=trial.current, duration=onStimDur)
            stimWait = Wait(interStimDur)
            self.timing += [Ref(dict,
                                fix_dur=fix.duration,
                                oriWait_dur=oriWait.duration,
                                stim_dur=stim.duration,
                                stimWait_dur=stimWait.duration)]

From here, we have a finished subroutine! We now have to write the
*mainListPresent.py*. We just need to generate a list of words and pass it into
our new subroutine.

Finished **main_list_present.py**
+++++++++++++++++++++++++++++++++

.. code-block:: python
    :linenos:

    from smile.common import *
    from list_present import ListPresent
    import random

    WORDS_TO_DISPLAY = ['The', 'Boredom', 'Is', 'The', 'Reason', 'I',
                        'started', 'Swimming', 'It\'s', 'Also', 'The',
                        'Reason', 'I','Started', 'Sinking','Questions',
                        'Dodge','Dip','Around','Breath','Hold']
    INTER_STIM_DUR = .5
    STIM_DUR = 1
    INTER_ORIENT_DUR = .2
    ORIENT_DUR = 1
    random.shuffle(WORDS_TO_DISPLAY)
    exp = Experiment()

    lp = ListPresent(listOfWords=WORDS_TO_DISPLAY, interStimDur=INTER_STIM_DUR,
                     onStimDur=STIM_DUR, fixDur=ORIENT_DUR,
                     nterOrientDur=INTER_ORIENT_DUR)
    Log(name='LISTPRESENTLOG',
        timing=lp.timing)
    exp.run()


Finished **list_present.py**
++++++++++++++++++++++++++++

.. code-block:: python
    :linenos:

    from smile.common import *

    @Subroutine
    def ListPresent(self,
                    listOfWords=[],
                    interStimDur=.5,
                    onStimDur=1,
                    fixDur=1,
                    interOrientDur=.2):
        self.timing = []
        with Loop(listOfWords) as trial:
            fix = Label(text='+', duration=fixDur)
            oriWait = Wait(interOrientDur)
            stim = Label(text=trial.current, duration=onStimDur)
            stimWait = Wait(interStimDur)
            self.timing += [Ref(dict,
                                fix_dur=fix.duration,
                                oriWait_dur=oriWait.duration,
                                stim_dur=stim.duration,
                                stimWait_dur=stimWait.duration)]





ButtonPress
-----------

This is an example to teach you how to use the state :py:class:`~smile.video.ButtonPress` and how to
use the :py:class:`~smile.video.MouseCursor` state. This is a simple experiment that allows you to
click a button on the screen, and then it tells you if you chose the correct
button.

An important thing to notice about this code is that :py:class:`~smile.video.ButtonPress` acts as a
:py:class:`~smile.video.Parallel` state. This means that all of the states defined within
:py:class:`~smile.video.ButtonPress` become its children. The field `correct` that you pass into
your :py:class:`~smile.video.ButtonPress` takes the *name* of the correct button for the participant
as a string.

When defining your **Buttons** within your button press, you should set the
`name` attribute of each to something different.  That way, when reviewing the
data you get at the end of the experiment, you are able to easily distinguish
which button the participant pressed.

Another thing that is important to understand about this code is the
:py:class:`~smile.video.MouseCursor` state.  By default, the experiment hides the mouse cursor. In
order to allow your participant to see where they are clicking, you must
include a :py:class:`~smile.video.MouseCursor` state in your :py:class:`~smile.video.ButtonPress` state. If you ever feel
that your participant needs to use the mouse for the duration of an experiment,
you are able to call the :py:class:`~smile.video.MouseCursor` state just after you assign your
:py:class:`~smile.experiment.Experiment` variable.

Finished **button_press_example.py**
++++++++++++++++++++++++++++++++++++

.. code-block:: python
    :linenos:

    from smile.common import *

    exp = Experiment()

    #From here you can see setup for a ButtonPress state.
    with ButtonPress(correct_resp='left', duration=5) as bp:
        MouseCursor()S
        Button(name='left', text='left', left=exp.screen.left,
               bottom=exp.screen.bottom)
        Button(name='right', text='right', right=exp.screen.right,
               bottom=exp.screen.bottom)
        Label(text='PRESS THE LEFT BUTTON FOR A CORRECT ANSWER!')
    Wait(.2)
    with If(bp.correct):
        Label(text='YOU PICKED CORRECT', color='GREEN', duration=1)
    with Else():
        Label(text='YOU WERE DEAD WRONG', color='RED', duration=1)
    exp.run()






