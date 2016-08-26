======================
SMILE Tutorial Basics!
======================

Hello SMILErs! This tutorial is for people just starting out in the world of
SMILE. Further in this documentation, there is a more advanced tutorial. If you
are brand new to SMILE and want to learn the basics line by line, you are in the
right place.


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

What are References?
====================

Since SMILE will build the experiment before it runs it, we needed to think of a
way to reference variables before the variables were created. That is why we
developed the :py:class:`~smile.ref.Ref`. The **Ref**, very basically, is a
delayed function call. Using **Ref**s, SMILE is able to hold onto a reference to
data that hasn't been created yet in your experiment. **Ref**s are
powerful in that they are recursive. That means that if you apply a basic
operation to a **Ref** (i.e. +, -, *, or /) it will create a new **Ref** that
contains both sides of the operation, and the operation function itself.

.. code-block:: python
    from smile.ref import Ref

    a = Ref.object(5)
    b = Ref.object(6)
    c = a + b
    print c.eval()

In the above example, *a* and *b* are refs that are created to contain only an
object. **Ref.object()** will return a **Ref** that will, when being evaluated
later, check to see what the value of the object is at that moment and return
that value. The above example creates 2 *integer* references. The third line
*c = a + b* is an example of creating a recursive reference. When *c* tries to
evaluate itself, it will attempt to evaluate *a* and *b*, then add them
together and return the result. The above example will print out the number *11*
when it finishes running.

.. note::

    You should not have to ever call *.eval()* for a reference. This was just an example to demonstrate how we use references in SMILE's backend. SMILE calls *.eval()* automatically.

References can also create a Reference object that contains a conditional
expression to be evaluated later. These are important when building
SMILE :py:class:`~smile.state.If` states. Say for instance the experimenter
would like to present "CONGRATS" on screen if the participant responded in less
than three seconds, and "FAILURE" if the participant took longer than three seconds
to respond. The experimenter would need to rely on a Referenced conditional statement,
where `Ref.cond(cond, true_val, false_val)` can return any kind of object if
true or false. Say you want to display "jubba" if a participant presses "J" and
"bubba" if the participant presses "K". SMILE allows you to use *cond* to do
this in 1 line rather than use an **If** state. For the above example, please
see the :py:class:`~smile.ref.Ref` docstring.

A :py:class:`~smile.state.Done` state is a unique state that will wait until the
value of a reference is made available. A reference is made available the first
time something calls *.eval()*

.. warning::

    This state is not for regular use. It should only be used when encountering the NotAvailableError. Misuse of the *Done* state, the experiment will have hang-ups in the framerate or running of the experiment.

For more information about :py:class:`~smile.ref.Ref` and :py:class:`~smile.state.Func`
please see :ref:`Preforming Functions and Operations in RT <func_ref_def>`

The next section of the doc will go over some simple SMILE tutorials and
introduce you to the states you can add to a SMILE experiment.

Looping over Lists! In Style
============================
The following example will walkthrough the basics of looping over a list.  This
walkthrough is divided into sections of code and explanation with the combined
code sections given at the end of the example.

Before we start, create a new directory called *exp* and create a file called
*randWord1.py*. In this file, the stimulus can be defined.

.. code-block:: python

    words=['plank', 'dear', 'adopter',
           'initial', 'pull', 'complicated',
           'ascertain', 'biggest']

    random.shuffle(words)

The file has created a list of words that will be randomly sorted when compiled.
From here, :py:class:`~smile.state.Loop` is used to loop over the list of words.
Before that, however, the preliminary variables must be established. After,
*exp = Experiment()* begins the building process.

.. code-block:: python

    #Needed Preliminary Parameters of the Experiment
    interStimulusDuration=1
    stimulusDuration=2

    #We are ready to start building the Experiment!
    exp = Experiment()

The default state in which :py:class:`~smile.state.Experiment` runs in is the
:py:class:`~smile.state.Serial` state. :py:class:`~smile.state.Serial` just
means that every other state defined inside of it runs in order, first in first
out. So every state defined after *exp = Experiment()* will be executed fifo
style. Next, a staple of every SMILE experiment, the
:py:class:`~smile.state.Loop` state is needed to be defined.

.. code-block:: python

    with Loop(words) as trial:
        Label(text=trial.current, duration=stimulusDuration)
        Wait(interStimulusDuration)

    exp.run()

The list of words that are to be looped act as a parameter in *Loop*. This tells
SMILE to loop over *words*. *Loop* also creates a reference variable. In this
instance, the reference variable is called *trial*. *trial* acts as a link
between the experiment's building and running states.  Until *exp.run()* is
called, *trial* will not have a value. The next line defines a
:py:class:`~smile.video.Label` state that displays text for a duration. By
default, it displays in the middle of the experiment window. Notice
*trial.current*: In order to access the numbers from the random list,
*trial.current* is used instead of *words[x]*. *trial.current* is a way to tell
SMILE to access the *current* member of the *words* list while looping.

.. warning::

    Do not try to access or test the value of trial.current. trial.current is a reference variable, so you will not be able to test its value outside of a SMILE state.

Finished **rand_word_1.py**
---------------------------

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
In this experiment example, a participant is presented with words, one a time.
The participant is told to press the J key if the presented word contains an
even number of letters, or press K the number of letters is odd. The
participant has 4 seconds to make a response.

This tutorial will also teach how to compare **trial.current** comparisons.
First, create a directory called *WordRemember* and create a file within the
directory called *randWord2.py*. Now, the word list must migrate to our new file
from the previous file in the tutorial.  This file will be slightly edited to
make sure that the experiment will be able to tell which key is the correct key
for each trial.

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

The list of words is now a list of dictionaries, in which *words[x]['stimulus']*
will provide the word and *words[x]['condition']* will provide whether the
word has an even or an odd length. Similar to the last example, the next step
is to initialize all of our experiment parameters. **key_list** is which
keys the participant will be pressing later.

.. code-block:: python

    #Needed Parameters of the Experiment
    interStimulusDuration=1
    maxResponseTime=4

    #We are ready to start building the Experiment!
    exp = Experiment()

Notice the line change from *stimulusDuration=2* to *maxResponseTime=4*.
Now, the basic loop can be set up.
The first thing needed to be added to this loop is the *UntilDone():* state. A
:py:class:`~smile.state.UntilDone` state will run its children
in :py:class:`~smile.state.Serial` until the parent state has finished.

The following is an example before the loop was edited:

.. code-block:: python

    ###########EXAMPLE, NOT PART OF EXPERIMENT#########
    Label(text='Im on the screen for at most 5 seconds')
    with UntilDone():
        Label(text='Im On the screen for 3 seconds!', duration=3)
        Wait(2)

As you can see, The first :py:class:`~smile.video.Label` is on the screen for 5
seconds because the :py:class:`~smile.state.UntilDone` state does not end until
the second :py:class:`~smile.video.Label` runs for 3 seconds and the
:py:class:`~smile.state.Wait` runs for 2 seconds.

Now to implement this state into the loop:

.. code-block:: python

    with Loop(words) as trial:

        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=key_dic)

        Wait(interStimulusDuration)

    exp.run()

This displays the number of the current trial until a key is pressed, after which
the loop waits for the inter-stimulus duration that was predefined earlier. The
next step entails editing *kp = KeyPress(keys=keys)* to include the response
time duration. Also needed is the ability to add a check to see if the participant
answered correctly. This will require the use of `trial.current['condition']`,
which is a listgen value set earlier.

.. code-block:: python

    with Loop(words) as trial:
        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=key_dic, duration=maxResponseTime,
                          correct_resp=trial.current['condition'])
        Wait(interStimulusDuration)
    exp.run()

The last thing needed to complete the experiment is to add, at the end of the
*Loop()*, the :py:class:`~smile.state.Log`. Wherever a :py:class:`~smile.state.Log`
state is placed in the experiment, it will save out a **.slog** file to a folder
called *data* in the experiment directory under a predetermined name put in the
*name* field.

.. code-block:: python

    Log(name='Loop',
        correct=kp.correct,
        time_to_respond=kp.rt)

With this line, each iteration of the loop in the experiment will save a
line into *Loop.slog* containing all of the values defined in the *Log()* call.

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

Now you are ready to get SMILEing! The next section of this documentation goes
over every state that SMILE has to offer!
