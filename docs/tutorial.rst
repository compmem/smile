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

To start, programming simple *SMILE* programs will be examined.

Create a directory called *SmileTest* and add a file named *main.py*

.. code-block:: python
    :linenos:

    from smile.common import *

    exp = Experiment()

    Label(text="Hello World, Lets start Smiling!", duration=4)

    exp.run()

Now, run **main.py**. Please refer to :ref:`Running SMILE <running-smile>` section of the
:ref:`How To SMILE <how-to-smile>` document to understand how to run a SMILE program.
After running **main.py**, a black screen with the words "Hello World, Lets start
Smiling!" should appear for 5 seconds.

This is a simple SMILE **experiment**. When ``exp = Experiment()`` runs, it
initializes the experiment and tells python to start defining the states of the program

As stated in :ref:`How To SMILE <how-to-smile>`, SMILE is a state machine. The above
SMILE program tells the *experiment* what states, in defined order, what states to run.
After the states have been defined in the experiment, the line ``exp.run()`` lets
the *experiment* know that the definition process is complete, and the *experiment* is
ready to run. The next step will examine how stimulus generation and stimulus
presentation can be separated with ease in this :py:class:`~smile.state.Loop` state example.

Looping over Lists! In Style
============================

To start, define the experiment to be created. This experiment is going to present
a list of predefined words to the participant for two seconds each and wait one second
in between each word. This can be accomplished simply using SMILE. All that is needed
is a basic idea of what the timing is in the experiment. Create a new directory called
*exp2* and create a file called *randWord1.py*. In the file, the stimulus can be defined.

.. code-block:: python

    words=['plank', 'dear', 'adopter',
           'initial', 'pull', 'complicated',
           'ascertain', 'biggest']

    random.shuffle(words)

The file has created a list of words that will be randomly sorted when compiled.
From here, an experiment that :py:class:`~smile.state.Loop` over the list of words
can be created. What is next needed is to setup the preliminary variables.

.. code-block:: python

    #Needed Parameters of the Experiment
    interStimulusDuration=1

    stimulusDuration=2

    #We are ready to start building the Experiment!
    exp = Experiment()


The default state that your :py:class:`~smile.state.Experiment` runs in is the :py:class:`~smile.state.Serial` state.
:py:class:`~smile.state.Serial` just means that every other state defined inside of it is run in
order, first in first out. So every state defined after
``exp = Experiment()`` will be executed fifo style. Next, a staple of every SMILE
experiment, the :py:class:`~smile.state.Loop` state is needed to be defined.

.. code-block:: python

    with Loop(words) as trial:

        Label(text=trial.current, duration=stimulusDuration)

        Wait(interStimulusDuration)

    exp.run()


Now, to examine the on-goings of this experiment line-by-line. The list of words
to *Loop* as a parameter. This tells SMILE to loop over *words*. *Loop* also creates
a reference variable. In this instance, the reference variable is called *trial*.
Trial acts as a link between the experiment building state of the
experiment, and the running state of the experiment.  Until ``exp.run()`` is
called, *trial* will not have a value. The next line defines a :py:class:`~smile.video.Label` state
that displays text for a duration. By default, it displays in the middle of the
experiment window. Notice ``trial.current``. In order to access the
numbers from the random list, ``trial.current`` is used instead of
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

The final step in the SMILE tutorial is to add user input and logging.
First, define the experiment. The experiment used for this example asks the
participant to press J if the number of letters on the screen is even, and K if
the number of letters in the word on the screen is odd. One parameter of the experiment is
the participants have only 4 seconds to answer. In this tutorial, it will be taught how
to set up our experiment so that when the participant presses a key to answer, the
stimulus will drop off the screen and start the next iteration of the loop.

This tutorial will also teach how to compare **trial.current** comparisons.
Create a directory called *WordRemember* and create a file within the directory
called *randWord2.py*. First step will be to migrate over the word list from the
previous file.  It will be slightly edited to make sure that the
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


The list of words is now a list of dictionaries, in which ``words[x]['stimulus']``
will provide the word and ``words[x]['condtion']`` will provide whether the
word has an even or an odd length. Similar to the last example, the next step
is to initialize all of our experiment parameters. **key_list** is what
keys the participant will be pressing later.

.. code-block:: python

    #Needed Parameters of the Experiment
    interStimulusDuration=1

    maxResponseTime=4


    #We are ready to start building the Experiment!
    exp = Experiment()


Notice the line change from ``stimulusDuration=2`` to ``maxResponseTime=4``.

The next step entails setting up our basic loop.

The first thing needed to be added to this loop is the ``UntilDone():`` state. An
:py:class:`~smile.state.UntilDone` state is a state that will run its children in :py:class:`~smile.state.Serial`
until the state above it has finished.

The following is an example before the loop was edited:

.. code-block:: python

    ###########EXAMPLE, NOT PART OF EXPERIMENT#########
    Label(text='Im on the screen for at most 5 seconds')

    with UntilDone():

        Label(text='Im On the screen for 3 seconds!', duration=3)

        Wait(2)


As you can see, The first :py:class:`~smile.video.Label` is on the screen for 5 seconds because the
:py:class:`~smile.state.UntilDone` state doesn't end until the second :py:class:`~smile.video.Label` has ran 3 seconds
and the :py:class:`~smile.state.Wait` has ran 2 seconds.

Now to implement this state into the loop:

.. code-block:: python

    with Loop(words) as trial:

        Label(text=trial.current['stimulus'])

        with UntilDone():
            kp = KeyPress(keys=key_dic)

        Wait(interStimulusDuration)

    exp.run()


This displays the current trial's number until a key is pressed, then waits the
inter-stimulus duration that was predefined earlier. Though this is not perfect,
the example is a start for understanding the ongoings of experiments. The next step
entails editing ``kp = KeyPress(keys=keys)`` to include the response time
duration. Also needed is the ability to add a check to see if the participant answered
correctly. This will require the use of `trial.current['condition']`, which is a
listgen value set earlier.

.. code-block:: python

    with Loop(words) as trial:

        Label(text=trial.current['stimulus'])

        with UntilDone():

            kp = KeyPress(keys=key_dic, duration=maxResponseTime,
                          correct_resp=trial.current['condition'])

        Wait(interStimulusDuration)

    exp.run()

The last thing needed to complete the experiment is to add, at the end of the ``Loop()``,
is the :py:class:`~smile.state.Log`. Wherever a :py:class:`~smile.state.Log` state is placed in the experiment,
it will save out a **.slog** file to a folder called *data* in the experiment
directory under a predetermined name put in the *name* field.

.. code-block:: python

    Log(name='Loop',
        correct=kp.correct,
        time_to_respond=kp.rt)

With this line, each iteration of the loop in the experiment will save a
line into *Loop.slog* containing all of the values defined in the ``Log()`` call.
The loop will look as follows:

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

This section is designed to develop techniques on using more
advanced states and advanced interactions with other states in SMILE.
For more detailed real life examples of experiments, reference
:ref:`Full Experiments <full-experiments>` page!

Subroutine
-----------------------------

In this tutorial how to write custom :py:class:`~smile.subroutine` states will be
examined.  In SMILE, a :py:class:`~smile.subroutine` state is used
to compartmentalize a block of states that a researcher reuses in different experiments.
The following example is an overview of a list presentation subroutine

First, create a new directory called *ListPresentTest* and then create a new file
in that directory called *list_present.py*.  Next, we need to do for setup the basic imports and define the
subroutine for the list presentation subroutine .

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



By placing `@Subroutine` above the subroutine definition, the compiler is told
to treat this as a SMILE :py:class:`~smile.subroutine`. The subroutine will eventually present
a fixation cross, wait, present the stimulus, wait again, and then repeat for
all of the list items it is passed. Just like calling a function or declaring a
state, call :py:class:`~smile.subroutine` in the body of the experiment and pass in
the variables in *main_list_present.py*, which will be created later.

.. warning::
    Always have *self* as the first argument when defining a subroutine. If you
    don't, your code will not work as intended.

The cool thing about :py:class:`~smile.subroutine` is that any variable declared
into 'self' can be accessed outside of the subroutine. So first,
add a few of the following to the subroutine:

.. code-block:: python

    @Subroutine
    def ListPresent(self,
                    listOfWords=[],
                    interStimDur=.5,
                    onStimDur=1,
                    fixDur=1,
                    interOrientDur=.2):

        self.timing = []

The only variable needed for testing later is an element to hold all of
the timing information to pass out into the experiment.

Next, add the stimulus loop:

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

At this point the subroutine is finished. The *mainListPresent.py* needs to be written
next. All that is needed is generation of a list of words to be passed into
the new subroutine.

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

In this section, the :py:class:`~smile.video.ButtonPress` state and the
:py:class:`~smile.video.MouseCursor` state will be examined. The following is a
simple experient that allows a participant to click a button on the screen and
then reports if the correct button was chosen.

Notice that this code, :py:class:`~smile.video.ButtonPress`, acts as a
:py:class:`~smile.video.Parallel` state. This means that all of the states defined within
:py:class:`~smile.video.ButtonPress` become its children. The field `correct` that is passed into
:py:class:`~smile.video.ButtonPress` takes the *name* of the correct button for the participant
as a string.

When defining **Buttons** within button press, the `name` attribute of each should
be set to something different.  That way, when reviewing post-experiment
data, it is easy to distinguish which button the participant pressed.

Another thing that is important to understand about this code is the
:py:class:`~smile.video.MouseCursor` state.  By default, the experiment hides the mouse cursor. In
order to allow the participant to see where they are clicking, a :py:class:`~smile.video.MouseCursor`
state must be included in the :py:class:`~smile.video.ButtonPress` state. If the
participant needs to use the mouse for the duration of an experiment,
call the :py:class:`~smile.video.MouseCursor` state just after assignment of the
:py:class:`~smile.experiment.Experiment` variable.

Finished **button_press_example.py**
++++++++++++++++++++++++++++++++++++

.. code-block:: python
    :linenos:

    from smile.common import *

    exp = Experiment()

    #From here you can see setup for a ButtonPress state.
    with ButtonPress(correct_resp='left', duration=5) as bp:
        MouseCursor()

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
