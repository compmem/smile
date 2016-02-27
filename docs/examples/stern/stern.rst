==============
Sternberg Task
==============

This is the Sternberg task. Developed by Saul Sternberg in the 1960's, this task
is designed to test a participants working memory by asking them to view a list
of several stimuli, usually words, numbers, or letters, and then showing them
a stimuli that may or may not have been in that list. They are then required to
make a judgement on whether or not that word was in the list. Below is the
SMILE version of that classic task. We use **Action** states like :py:class:`~smile.keyboard.KeyPress`
and :py:class:`~smile.video.Label` in this experiment, as well as **Flow**
states like :py:class:`~smile.state.UntilDone` and :py:class:`~smile.state.Loop`.

Each participant of this experiment will have a different log that will contain
all of the information about each block, as well as all of the information that
would be needed to run analysis of this experiment, i.e. reaction times.

The Experiment
==============

First lets do the imports of the experiment. Below is the start of `stern.py`.
We will also execute the configuration file and the stimulus generation file.

.. code-block:: python
    :linenos:

    # global imports
    import random
    import string
    # load all the states
    from smile.common import *

    #execute both the configuration file and the
    #stimulus generation file
    from config import *
    from gen_stim import *


Easy, Now lets also setup all the experiment variables. These are all the
variables that are needed for generating stimuli, durations of states, and
little things like instructions and the keys for **KeyPress** states. The
following is `config.py`

.. code-block:: python
    :linenos:

    # config vars
    NUM_TRIALS = 2
    #The trials, shuffled, for the stimulus generation.
    NUM_ITEMS = [2,2,2,2,2,2,2,3,3,3,3,3,3,3,4,4,4,4,4,4,4]
    random.shuffle(NUM_ITEMS)
    ITEMS = string.ascii_lowercase
    #instructions writen in another document
    instruct_text = open('stern_instructions.rst', 'r').read()
    RSTFONTSIZE = 30
    RSTWIDTH = 900
    STUDY_DURATION = 1.2
    STUDY_ISI = .4
    RETENTION_INTERVAL = 1.0
    #KeyPress stuff
    RESP_KEYS = ['J','K']
    RESP_DELAY = .2
    ORIENT_DURATION = 1.0
    ORIENT_ISI = .5
    ITI = 1.0
    FONTSIZE = 30

Next is the generation of our stimuli. In SMILE, the best practice is to
generate lists of dictionaires to loop over, that way you don't have to do any
calculations during the actual experiments. Next is the definition of a function
that was writen to generate a stern trial called `stern_trial()`, as well as
where we call it to generate our stimulus. The following is `gen_stim.py`

.. code-block:: python
    :linenos:

    # generate sternberg trial
    def stern_trial(nitems=2, lure_trial=False,):
        if lure_trial:
            condition = 'lure'
            items = random.sample(ITEMS,nitems+1)
        else:
            condition = 'target'
            items = random.sample(ITEMS,nitems)
            # append a test item
            items.append(random.sample(items,1)[0])
        trial = {'nitems':nitems,
                 'study_items':items[:-1],
                 'test_item':items[-1],
                 'condition':condition,}
        return trial

    trials = []
    for i in NUM_ITEMS:
        # add target trials
        trials.extend([stern_trial(i,lure_trial=False) for t in range(NUM_TRIALS)])
        # add lure trials
        trials.extend([stern_trial(i,lure_trial=True) for t in range(NUM_TRIALS)])

    # shuffle and number
    random.shuffle(trials)
    for t in range(len(trials)):
        trials[t]['trial_num'] = t

After we generate our stimulus we need to setup our experiment. The comments in
the following code explain what every few lines do.

.. code-block:: python
    :linenos:

    #Define the experiment
    exp = Experiment()
    #Present the instructions to the participant
    init_text = RstDocument(text=instruct_text, width=RSTWIDTH, font_size=RSTFONTSIZE, top=exp.screen.top, height=exp.screen.height)
    with UntilDone():
        #Once the KeyPress is detected, the UntilDone
        #cancels the RstDocument
        keypress = KeyPress()
    # loop over study block
    with Loop(trials) as trial:
        #Setup the list of study times.
        exp.study_times = []
        # orient stim
        orient = Label(text='+',duration=ORIENT_DURATION, font_size=FONTSIZE)
        Wait(ORIENT_ISI)
        # loop over study items
        with Loop(trial.current['study_items']) as item:
            # present the letter
            ss = Label(text=item.current, duration=STUDY_DURATION, font_size=FONTSIZE)
            # wait some jittered amount
            Wait(STUDY_ISI)
            # append the time
            exp.study_times+=[ss.appear_time['time']]
        # Retention interval
        Wait(RETENTION_INTERVAL - STUDY_ISI)
        # present the letter
        test_stim = Label(text=trial.current['test_item'], bold=True, font_size=FONTSIZE)
        with UntilDone():
            # wait some before accepting input
            Wait(RESP_DELAY)
            #After the KeyPress is detected, the UntilDone
            #cancels the Label test_stim and allows the
            #experiment to continue.
            ks = KeyPress(keys=RESP_KEYS,
                          base_time=test_stim.appear_time['time'])
        # Log the trial
        Log(trial.current,
            name="Stern",
            resp=ks.pressed,
            rt=ks.rt,
            orient_time=orient.appear_time['time'],
            study_times=exp.study_times,
            test_time=test_stim.appear_time['time'],
            correct=(((trial.current['condition']=='target')&
                     (ks.pressed==RESP_KEYS[0])) |
                     ((trial.current['condition']=='lure')&
                     (ks.pressed==RESP_KEYS[1]))))
        Wait(ITI)
    # run that exp!
    exp.run()

Analysis
========

When coding your experiment, you don't have to worry about losing any data,
becaues all of it is saved out into `.slog` files anyway. The thing you do have
to worry about is whether or not you want that data easily available or if you
want to spend hours **slogging** through your data. We made it easy for you
to pick which data you want saved out during the running of your experiment with
use of the **Log** state.

The relevant data that we need from a **Sternberg** task would be the reaction
times for every test event, all of the presented letters from the the study and
test portion of the experiment, and whether they answered correctly or not. In
the **Log** that we defined in our experiment above, we saved a little more than
that out, because it is better to save out data and not need it, then to not
save it and need it later.

If you would like to grab your data from the `.slog` files to analize your data
in python, you need to use the :py:func:`~smile.log.log2dl`. This function will
read in all of the `.slog` files with the same base name, and convert them into
one long list of dictionaries. Below is a the few lines of code you would use to
get at all of the data from three imaginary paricipants, named as `s000`, `s001`,
and `s002`.

.. code-block:: python
    :linenos:

    from smile.log as lg
    #define subject pool
    subjects = ["s000/","s001/","s002/"]
    dic_list = []
    for sbj in subjects:
        #get at all the different subjects
        dic_list.append(lg.log2dl(log_filename="data/" + sbj + "Log_Stern"))
    #print out all of the study times in the first study block for
    #participant one, block one
    print dic_list[0]['study_times']

You can also translate all of the `.slog` files into `.csv` files easily by
running the command :py:func:`~smile.log.log2csv` for each paricipant. An example of this is
located below.

.. code-block:: python
    :linenos:

    from smile.log as lg
    #define subject pool
    subjects = ["s000/","s001/","s002/"]
    for sbj in subjects:
        #Get at all the subjects data, naming the csv appropriately.
        lg.log2csv(log_filename="data/" + sbj + "Log_Stern", csv_filename=sbj + "_Stern")


stern.py in Full
=============

.. code-block:: python
    :linenos:

    # global imports
    import random
    import string
    # load all the states
    from smile.common import *

    #execute both the configuration file and the
    #stimulus generation file
    from config import *
    from gen_stim import *

    #Define the experiment
    exp = Experiment()
    #Present the instructions to the participant
    init_text = RstDocument(text=instruct_text, width=RSTWIDTH, font_size=RSTFONTSIZE top=exp.screen.top, height=exp.screen.height)
    with UntilDone():
        #Once the KeyPress is detected, the UntilDone
        #cancels the RstDocument
        keypress = KeyPress()
    # loop over study block
    with Loop(trials) as trial:
        #Setup the list of study times.
        exp.study_times = []
        # orient stim
        orient = Label(text='+',duration=ORIENT_DURATION, font_size=FONTSIZE)
        Wait(ORIENT_ISI)
        # loop over study items
        with Loop(trial.current['study_items']) as item:
            # present the letter
            ss = Label(text=item.current, duration=STUDY_DURATION, font_size=FONTSIZE)
            # wait some jittered amount
            Wait(STUDY_ISI)
            # append the time
            exp.study_times+=[ss.appear_time['time']]
        # Retention interval
        Wait(RETENTION_INTERVAL - STUDY_ISI)
        # present the letter
        test_stim = Label(text=trial.current['test_item'], bold=True, font_size=FONTSIZE)
        with UntilDone():
            # wait some before accepting input
            Wait(RESP_DELAY)
            #After the KeyPress is detected, the UntilDone
            #cancels the Label test_stim and allows the
            #experiment to continue.
            ks = KeyPress(keys=RESP_KEYS,
                          base_time=test_stim.appear_time['time'])
        # Log the trial
        Log(trial.current,
            name="Stern",
            resp=ks.pressed,
            rt=ks.rt,
            orient_time=orient.appear_time['time'],
            study_times=exp.study_times,
            test_time=test_stim.appear_time['time'],
            correct=(((trial.current['condition']=='target')&
                     (ks.pressed==RESP_KEYS[0])) |
                     ((trial.current['condition']=='lure')&
                     (ks.pressed==RESP_KEYS[1]))))
        Wait(ITI)
    # run that exp!
    exp.run()

config.py in Full
=================

.. code-block:: python
    :linenos:

    # config vars
    NUM_TRIALS = 2
    NUM_ITEMS = [2,3,4]
    ITEMS = string.ascii_lowercase
    instruct_text = open('stern_instructions.rst', 'r').read()
    RSTFONTSIZE = 30
    RSTWIDTH = 900
    STUDY_DURATION = 1.2
    STUDY_ISI = .4
    RETENTION_INTERVAL = 1.0
    RESP_KEYS = ['J','K']
    RESP_DELAY = .2
    ORIENT_DURATION = 1.0
    ORIENT_ISI = .5
    ITI = 1.0
    FONTSIZE = 30

gen_stim.py in Full
===================

.. code-block:: python
    :linenos:

    # generate sternberg trial
    def stern_trial(nitems=2, lure_trial=False,):
        if lure_trial:
            condition = 'lure'
            items = random.sample(ITEMS,nitems+1)
        else:
            condition = 'target'
            items = random.sample(ITEMS,nitems)
            # append a test item
            items.append(random.sample(items,1)[0])
        trial = {'nitems':nitems,
                 'study_items':items[:-1],
                 'test_item':items[-1],
                 'condition':condition,}
        return trial

    trials = []
    for i in NUM_ITEMS:
        # add target trials
        trials.extend([stern_trial(i,lure_trial=False) for t in range(NUM_TRIALS)])
        # add lure trials
        trials.extend([stern_trial(i,lure_trial=True) for t in range(NUM_TRIALS)])

    # shuffle and number
    random.shuffle(trials)
    for t in range(len(trials)):
        trials[t]['trial_num'] = t
