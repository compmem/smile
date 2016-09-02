================
Special Examples
================

This section is designed to develop techniques on how to use more
advanced states and advanced interactions with other states in SMILE.
For more detailed real life examples of experiments, reference
:ref:`Full Experiments <full-experiments>` page!

Subroutine
----------

A subroutine is a stand-alone state that performs a specific action; an action that is
often called multiple times in an experiment. The experiment will provide parameters
for the subroutine, but not alter the subroutine itself.

.. note::
    It's the experiment's responsibility to save logging information that comes from the subroutine. The coder should make sure that the subroutine is providing the desired information to the experiment, which the experiment may save.

This tutorial covers how to write custom :py:class:`~smile.subroutine` states.In
SMILE, a :py:class:`~smile.subroutine` state is used.
to compartmentalize a block of states that a researcher reuses in different experiments.
The following example is an overview of a list presentation subroutine.

First, create a new directory called *ListPresentTest* and then create a new file
in that directory called *list_present.py*.  Next, import the necessary packages and
define the subroutine for the list presentation.

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
to treat this as a SMILE :py:class:`~smile.subroutine`. The subroutine will
eventually present a fixation cross, wait, present the stimulus, wait again, and
then repeat for all of the list items it is passed. Just like calling a function
or declaring a state, call :py:class:`~smile.subroutine` in the body of the
experiment and pass in the variables into *main_list_present.py*, which will be
created later.

.. warning::
    Always have *self* as the first argument when defining a subroutine. If you don't, your code will not work as intended.

A powerful feature of :py:class:`~smile.subroutine` is that any variable
declared into 'self' can be accessed outside of the subroutine. So, add a few of
the following to the subroutine:

.. code-block:: python

    @Subroutine
    def ListPresent(self,
                    listOfWords=[],
                    interStimDur=.5,
                    onStimDur=1,
                    fixDur=1,
                    interOrientDur=.2):

        self.timing = []

The only variable needed for later testing is an element to hold all of the
timing information to pass out into the experiment.

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

At this point the subroutine is finished. The *mainListPresent.py* needs to be
written next. All that is needed is generation of a list of words to be passed
into the new subroutine.

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

When making an experiment with buttons, the cursor used to make the selections (such as a mouse cursor)
is a necessesary consideration. The :py:class:`~smile.video.MouseCursor` state handles this.
By default, the experiment hides the mouse cursor. In
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
