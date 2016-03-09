===========
Free Recall
===========

.. image:: _static/free_recall.png
    :width: 375
    :height: 241
    :align: right

Free-Recall is a psychological paradigm where the participant is shown a list of
words and is then asked to recall the displayed words in any order immediately
after being shown or after a period of delay.

The kind of Free-Recall Experiment that we wrote is the Immediate Free-Recall
task. Our participant will view 10, 15, or 20 words and then be asked to recall
as many words as possible from the list in 20, 30, or 40 seconds respectively.
This experiment will show you how to use the :py:class:`~smile.state.Subroutine`
called :py:class:`~smile.freekey.FreeKey`, as well as things like :py:class:`~smile.video.Label`
and :py:class:`~smile.state.Loop`.

Below we will show you the best practices for coding an experiment like this one.

The Experiment
==============

The best thing to do when coding a SMILE experiment is to break up the
experiment into 3 different files: the experiment file with all the SMILE code,
the config file with all the experimental variables, and the stimulus
generation file.

The first thing we will look at is `free_recall.py`. In this file we need to
import smile as well as execute the `config.py` and the `gen_stim.py`.

.. code-block:: python

    :linenos:

    #freekey.py
    from smile.common import *
    from smile.freekey import FreeKey

    #execute both the configuration file and the
    #stimulus generation file
    from config import *
    from gen_stim import *

Inside `config.py` we setup any variables that will need to be used during the
experiment as well as open any files that we might need for list generation or
instructions for the participant.

.. code-block:: python

    :linenos:

    #Names of the stimulus files
    filenameL = "pools/living.txt"
    filenameN = "pools/nonliving.txt"

    #Open the files and combine them
    L = open(filenameL)
    N = open(filenameN)
    stimList = L.read().split('\n')
    stimList.append(N.read().split('\n'))

    #Open the instructions file
    instruct_text = open('freekey_instructions.rst', 'r').read()

    #Define the Experimental Variables
    ISI = 2
    IBI = 2
    STIMDUR = 2
    PFI = 4
    FONTSIZE = 40
    RSTFONTSIZE = 30
    RSTWIDTH = 900

    MINFKDUR = 20

    NUMBLOCKS = 6
    NUMPERBLOCK = [10,15,20]

Next we can take a look into our list gen. Simply, we generate a list of
dictionaries where **study** points to a list of words and **duration** points
to the duration that the participants have to freely recall the words.

.. code-block:: python

    :linenos:

    import random

    #Shuffle the stimulus
    random.shuffle(stimList)

    blocks = []
    #Loop NUMBLOCKS times
    for i in range(NUMBLOCKS):
        tempList = []
        #For each block, loop either 10, 15, or 20 times
        #Counter balanced to have equal numbers of each
        for x in range(NUMPERBLOCK[i%len(NUMPERBLOCK)]):
            tempList.append(stimList.pop())
        #Create tempBlock
        tempBlock = {"study":tempList,
                     "duration":(MINFKDUR + 10*i%len(NUMPERBLOCK))}
        blocks.append(tempBlock)
    #Shuffle the newly created list of blocks
    random.shuffle(blocks)

Finally we can get to the fun stuff! We now can start programming our SMILE
experiment. The comments in the following section of code explain why we do each
part of the experiment.

.. code-block:: python

    #Initialize the Experiment
    exp = Experiment()

    #Show the instructions to the participant
    RstDocument(text=instruct_text, base_font_size=RSTFONTSIZE, width=RSTWIDTH, height=exp.screen.height)
    with UntilDone():
        #When a KeyPress is detected, the UntilDone
        #will cancel the RstDocument state
        KeyPress()
    #Start the experiment Loop
    with Loop(blocks) as block:
        Wait(IBI)
        with Loop(block.current['study']) as study:
            #Present the Fixation Cross
            Label(text="+", duration=ISI, font_size=FONTSIZE)
            #Present the study item
            Label(text=study.current, duration=STIMDUR, font_size=FONTSIZE)
        Wait(PFI)
        #Start FreeKey
        fk = FreeKey(Label(text="XXXXXXX", font_size=FONTSIZE), max_duration=block.current['duration'])
        #Log everything!
        Log(block,
            name="FreeKey",
            responses = fk.responses)
    #Run the experiment
    exp.run()

Analysis
========

When coding your experiment, you don't have to worry about losing any data
because all of it is saved out into `.slog` files anyway. The thing you do have
to worry about is whether or not you want that data to be easily available or if you
want to spend hours **slogging** through your data. We made it easy for you
to pick which data you want saved out during the running of your experiment with
use of the **Log** state.

Relevant data from the **Free-Recall** task would be the responses from each
**FreeKey** state. In the **Log** that we used in the experiment above, we
log everything in each *block* of the experiment, i.e. the stimulus and the
duration that they are allowed to respond in, and the responses from **FreeKey**.

If you would like to grab your data from the `.slog` files to analyze your data
in python, you need to use the :py:func:`~smile.log.log2dl`. This function will
read in all of the `.slog` files with the same base name, and convert them into
one long list of dictionaries. Below is a the few lines of code you would use to
get at all of the data from three imaginary participants, named as `s000`, `s001`,
and `s002`.

.. code-block:: python

    :linenos:

    from smile.log as lg
    #define subject pool
    subjects = ["s000/","s001/","s002/"]
    dic_list = []
    for sbj in subjects:
        #get at all the different subjects
        dic_list.append(lg.log2dl(log_filename="data/" + sbj + "Log_FreeKey"))
    #print out all of the study times in the first study block for
    #participant one, block one
    print dic_list[0]['study_times']

You can also translate all of the `.slog` files into `.csv` files easily by
running the command :py:func:`~smile.log.log2csv` for each participant. An example of this is
located below.

.. code-block:: python

    :linenos:

    from smile.log as lg
    #define subject pool
    subjects = ["s000/","s001/","s002/"]
    for sbj in subjects:
        #Get at all the subjects data, naming the csv appropriately.
        lg.log2csv(log_filename="data/" + sbj + "Log_FreeKey", csv_filename=sbj + "_FreeKey")

free_recall.py in Full
======================

.. code-block:: python

    :linenos:

    #freekey.py
    from smile.common import *
    from smile.freekey import FreeKey

    #execute both the configuration file and the
    #stimulus generation file
    from config import *
    from gen_stim import *

    #Initialize the Experiment
    exp = Experiment()

    #Show the instructions to the participant
    RstDocument(text=instruct_text, base_font_size=RSTFONTSIZE, width=RSTWIDTH, height=exp.screen.height)
    with UntilDone():
        #When a KeyPress is detected, the UntilDone
        #will cancel the RstDocument state
        KeyPress()
    #Start the experiment Loop
    with Loop(blocks) as block:
        Wait(IBI)
        with Loop(block.current['study']) as study:
            #Present the Fixation Cross
            Label(text="+", duration=ISI, font_size=FONTSIZE)
            #Present the study item
            Label(text=study.current, duration=STIMDUR, font_size=FONTSIZE)
        Wait(PFI)
        #Start FreeKey
        fk = FreeKey(Label(text="XXXXXXX", font_size=FONTSIZE), max_duration=block.current['duration'])
        #Log everything!
        Log(block,
            name="FreeKey",
            responses = fk.responses)
    #Run the experiment
    exp.run()

config.py in Full
=================

.. code-block:: python

    :linenos:

    #Names of the stimulus files
    filenameL = "pools/living.txt"
    filenameN = "pools/nonliving.txt"

    #Open the files and combine them
    L = open(filenameL)
    N = open(filenameN)
    stimList = L.read().split('\n')
    stimList.append(N.read().split('\n'))

    #Open the instructions file
    instruct_text = open('freekey_instructions.rst', 'r').read()

    #Define the Experimental Variables
    ISI = 2
    IBI = 2
    STIMDUR = 2
    PFI = 4
    FONTSIZE = 40
    RSTFONTSIZE = 30
    RSTWIDTH = 900

    MINFKDUR = 20

    NUMBLOCKS = 6
    NUMPERBLOCK = [10,15,20]

gen_stim.py in Full
===================

.. code-block:: python

    :linenos:

    import random

    #Shuffle the stimulus
    random.shuffle(stimList)

    blocks = []
    #Loop NUMBLOCKS times
    for i in range(NUMBLOCKS):
        tempList = []
        #For each block, loop either 10, 15, or 20 times
        #Counter balanced to have equal numbers of each
        for x in range(NUMPERBLOCK[i%len(NUMPERBLOCK)]):
            tempList.append(stimList.pop())
        #Create tempBlock
        tempBlock = {"study":tempList,
                     "duration":(MINFKDUR + 10*i%len(NUMPERBLOCK))}
        blocks.append(tempBlock)
    #Shuffle the newly created list of blocks
    random.shuffle(blocks)

CITATION
========

::

	Murdock, Bennet B. (1962), "The serial position effect of free recall", Journal of Experimental Psychology 64 (5): 482–488

::

	Waugh, Nancy C. (1961), "Free versus serial recall", Journal of Experimental Psychology 62 (5): 496–502
