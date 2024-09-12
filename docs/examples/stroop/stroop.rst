===========
Stroop Task
===========

.. image:: ../../_static/stroop.png
    :width: 375
    :height: 241
    :align: right

This is the stroop task. The participant is required to view a list of words,
appearing one at a time on the screen, and say out loud the color of the text.
Each sound file corresponding to each trial are saved out as `.wav` files, with
the block and trial number in the filename.

The Experiment
==============

First, let's do the imports that we need for this experiment. We are also going
to execute the config.py file and the gen_stim.py file.

.. code-block:: python

    from smile.common import *
    from smile.audio import RecordSoundFile

    #execute both the configuration file and the
    #stimulus generation file
    from config import *
    from gen_stim import *

The following is `gen_stim.py`.

.. code-block:: python
    :linenos:

    from random import shuffle, randint, choice
    from typing import List, Dict
    from config import NUMBER_OF_BLOCKS, NUMBER_OF_TRIALS_PER_BLOCK


    def randomize_color(word: str, index: int) -> str:
        """
        Randomly select a color from the available colors that does not match the given word.

        Args:
            word (str): The word representing the color.
            index (int): The index used for color randomization.

        Returns:
            str: A mismatched color.
        """
        word_color_map = {
            'red': ["BLUE", "GREEN", "ORANGE"],
            'blue': ["RED", "GREEN", "ORANGE"],
            'green': ["RED", "BLUE", "ORANGE"],
            'orange': ["RED", "BLUE", "GREEN"]
        }
        return word_color_map[word][index % 3]


    def create_trial(word: str, matched: bool = True, color: str = None) -> Dict[str, str]:
        """
        Creates a trial dictionary with word, color, and matched status.

        Args:
            word (str): The word for the trial.
            matched (bool): Whether the word matches the color.
            color (str): Optional color to use for the trial, only for mismatched trials.

        Returns:
            dict: A dictionary representing a single trial.
        """
        trial_color = color if not matched else word.upper()
        return {
            'word': word,
            'color': trial_color,
            'matched': matched
        }


    def generate_block(number_of_trials_per_block: int) -> List[Dict[str, str]]:
        """
        Generate a block of trials with a specified length.

        Args:
            number_of_trials_per_block (int): The desired number of trials in the block.

        Returns:
            List[Dict[str, str]]: A list of trial dictionaries.
        """
        block = []
        words = ["red", "blue", "green", "orange"]

        num_matched_trials = number_of_trials_per_block // 2

        # Add matched trials
        for _ in range(num_matched_trials):  # Half of the trials are matched
            block.append(create_trial(choice(words), matched=True))

        # Add mismatched trials
        # Half of the trials are mismatched
        for _ in range(number_of_trials_per_block - num_matched_trials):
            random_word = choice(words)
            block.append(create_trial(random_word, matched=False,
                        color=randomize_color(random_word, randint(0, 2))))

        shuffle(block)  # Shuffle the block for randomization
        return block


    def generate_blocks(num_of_blocks: int, number_of_trials_per_block: int) -> List[List[Dict[str, str]]]:
        """
        Generate a list of blocks, where each block contains a number of trials.

        Each trial is represented as a dictionary with string keys and values.

        Args:
            num_of_blocks (int): The number of blocks to generate.
            number_of_trials_per_block (int): The number of trials in each block.

        Returns:
            List[List[Dict[str, str]]]: A list of blocks, where each block is a list of trials. 
            Each trial is represented as a dictionary with string keys and values.
        """
        blocks = []

        for _ in range(num_of_blocks):
            # Generate a block with the specified number of trials
            block = generate_block(number_of_trials_per_block)
            blocks.append(block)

        shuffle(blocks)  # Shuffle the list of blocks to randomize their order
        return blocks


    BLOCKS = generate_blocks(NUMBER_OF_BLOCKS, NUMBER_OF_TRIALS_PER_BLOCK)

Now that we have our list gen setup, let's run our list gen and setup our
experiment variables. The following is `config.py`.

.. code-block:: python
    :linenos:

    from pathlib import Path
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    # Read in the instructions
    INSTRUCT_TEXT = open(script_dir / 'stroop_instructions.rst', 'r').read()
    NUMBER_OF_BLOCKS = 1
    NUMBER_OF_TRIALS_PER_BLOCK = 2
    RECORD_DURATION = 2
    INTER_BLOCK_DURATION = 2
    INTER_STIMULUS_INTERVAL = 2
    RST_FONT_SIZE = 30
    RST_WIDTH = 900

Now we can start building our stroop experiment. The first line we run is
`exp = Experiment()` to tell **SMILE** that we are ready to start defining the
states in our state machine. The main states we are going to need when
presenting any stimulus, in our case :py:class:`Labels <smile.video.Label>` of text, are :py:class:`Loops <smile.state.Loop>`.
The other state will be needed is the :py:class:`~smile.state.Wait` state, to
provide a much needed slight delay in the stimulus.

Below are the first few lines of our experiment. We setup the experiment
variables and the loops that drive our experiment.

.. code-block:: python

    # Define the Experiment Variable
    exp = Experiment()

    # Show the instructions as an RstDocument Viewer on the screen
    init_text = RstDocument(text=INSTRUCT_TEXT, font_size=RST_FONT_SIZE,
                            width=RST_WIDTH, top=exp.screen.top, height=exp.screen.height)
    with UntilDone():
        # Once you press any key, the UntilDone will cancel the RstDocument,
        # allowing the rest of the experiment to continue running.
        keypress = KeyPress()

    # Initialize the block counter, only used because we need
    # unique names for the .wav files later.
    exp.block_number = 0

    # Initialize the Loop as "with Loop(list_like) as reference_variable_name:"
    with Loop(BLOCKS) as block:
        # Initialize the trial counter, only used because we need
        # unique names for the .wav files later.
        exp.trial_number = 0

        # Initialize the Loop as "with Loop(list_like) as reference_variable_name:"
        with Loop(block.current) as trial:

We have now declared our 2 loops. One is to loop over our blocks, and one is to
loop over our trials in each block. We also put an inter-stimulus fixation cross
to show the participant where the stimulus will be presented. The next step is
to define how our action states will work.

.. code-block:: python

            inter_stim = Label(text='+', font_size=80,
                                duration=INTER_BLOCK_DURATION)
            # Display the word, with the appropriate colored text
            t = Label(text=trial.current['word'],
                    font_size=48, color=trial.current['color'])
            with UntilDone():
                # The Label will stay on the screen for as long as
                # the RecordSoundFile state is active. The filename
                # for this state is different for each trial in each block.
                rec = RecordSoundFile(filename="b_" + Ref(str, exp.block_number) + "_t_" + Ref(str, exp.trial_number),
                                    duration=RECORD_DURATION)
            # Log the color and word that was presented on the screen,
            # as well as the block and trial number
            Log(name='Stroop', stim_word=trial.current['word'], stim_color=trial.current['color'],
                block_num=exp.block_number, trial_num=exp.trial_number)
            Wait(INTER_STIMULUS_INTERVAL)
            # Increase the trial_number
            exp.trial_number += 1
        # Increase the block_number
        exp.block_number += 1
    # Run the experiment!
    exp.run()

Analysis
========

The main way to analyze this data is to run all of your `.wav` files through
some kind of program that deals with sifting through the important information
that each file contains to remove errors. That info is what word they are saying
in it and how long, from the start of recording, it took them to respond. With
those two peices of information, you would be able to run stats on them along with
the data from the experiment, i.e. the color and the text of the presented item
during each trial.

How you go about getting the info from the `.wav` files might be hard, but
getting the data from SMILE and into a data-frame is fairly easy. Below is a
the few lines of code you would use to get at all of the data from all of your
participants.

.. code-block:: python
    :linenos:

    from smile.log as lg
    #define subject pool
    subjects = ["s000/","s001/","s002/"]
    dic_list = []
    for sbj in subjects:
        #get at all the different subjects
        dic_list.append(lg.log2dl(log_filename="data/" + sbj + "Log_Stroop"))
    #print out all of the stimulus words of the first subject's first trial
    print dic_list[0]['stim_word']

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
        lg.log2csv(log_filename="data/" + sbj + "Log_Stroop", csv_filename=sbj + "_Stroop")


stroop.py in Full
=================

.. code-block:: python
    :linenos:

   from smile.common import *
    from smile.audio import RecordSoundFile

    # execute both the configuration file and the
    # stimulus generation file
    from config import *
    from gen_stim import *

    # Define the Experiment Variable
    exp = Experiment()

    # Show the instructions as an RstDocument Viewer on the screen
    init_text = RstDocument(text=INSTRUCT_TEXT, font_size=RST_FONT_SIZE,
                            width=RST_WIDTH, top=exp.screen.top, height=exp.screen.height)
    with UntilDone():
        # Once you press any key, the UntilDone will cancel the RstDocument,
        # allowing the rest of the experiment to continue running.
        keypress = KeyPress()

    # Initialize the block counter, only used because we need
    # unique names for the .wav files later.
    exp.block_number = 0

    # Initialize the Loop as "with Loop(list_like) as reference_variable_name:"
    with Loop(BLOCKS) as block:
        # Initialize the trial counter, only used because we need
        # unique names for the .wav files later.
        exp.trial_number = 0

        # Initialize the Loop as "with Loop(list_like) as reference_variable_name:"
        with Loop(block.current) as trial:
            inter_stim = Label(text='+', font_size=80,
                            duration=INTER_BLOCK_DURATION)
            # Display the word, with the appropriate colored text
            t = Label(text=trial.current['word'],
                    font_size=48, color=trial.current['color'])
            with UntilDone():
                # The Label will stay on the screen for as long as
                # the RecordSoundFile state is active. The filename
                # for this state is different for each trial in each block.
                rec = RecordSoundFile(filename="b_" + Ref(str, exp.block_number) + "_t_" + Ref(str, exp.trial_number),
                                    duration=RECORD_DURATION)
            # Log the color and word that was presented on the screen,
            # as well as the block and trial number
            Log(name='Stroop', stim_word=trial.current['word'], stim_color=trial.current['color'],
                block_num=exp.block_number, trial_num=exp.trial_number)
            Wait(INTER_STIMULUS_INTERVAL)
            # Increase the trial_number
            exp.trial_number += 1
        # Increase the block_number
        exp.block_number += 1
    # Run the experiment!
    exp.run()

config.py in Full
=================

.. code-block:: python
    :linenos:

    from pathlib import Path
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    # Read in the instructions
    INSTRUCT_TEXT = open(script_dir / 'stroop_instructions.rst', 'r').read()
    NUMBER_OF_BLOCKS = 1
    NUMBER_OF_TRIALS_PER_BLOCK = 2
    RECORD_DURATION = 2
    INTER_BLOCK_DURATION = 2
    INTER_STIMULUS_INTERVAL = 2
    RST_FONT_SIZE = 30
    RST_WIDTH = 900

gen_stim.py in Full
===================

.. code-block:: python
    :linenos:

    from random import shuffle, randint, choice
    from typing import List, Dict
    from config import NUMBER_OF_BLOCKS, NUMBER_OF_TRIALS_PER_BLOCK


    def randomize_color(word: str, index: int) -> str:
        """
        Randomly select a color from the available colors that does not match the given word.

        Args:
            word (str): The word representing the color.
            index (int): The index used for color randomization.

        Returns:
            str: A mismatched color.
        """
        word_color_map = {
            'red': ["BLUE", "GREEN", "ORANGE"],
            'blue': ["RED", "GREEN", "ORANGE"],
            'green': ["RED", "BLUE", "ORANGE"],
            'orange': ["RED", "BLUE", "GREEN"]
        }
        return word_color_map[word][index % 3]


    def create_trial(word: str, matched: bool = True, color: str = None) -> Dict[str, str]:
        """
        Creates a trial dictionary with word, color, and matched status.

        Args:
            word (str): The word for the trial.
            matched (bool): Whether the word matches the color.
            color (str): Optional color to use for the trial, only for mismatched trials.

        Returns:
            dict: A dictionary representing a single trial.
        """
        trial_color = color if not matched else word.upper()
        return {
            'word': word,
            'color': trial_color,
            'matched': matched
        }


    def generate_block(number_of_trials_per_block: int) -> List[Dict[str, str]]:
        """
        Generate a block of trials with a specified length.

        Args:
            number_of_trials_per_block (int): The desired number of trials in the block.

        Returns:
            List[Dict[str, str]]: A list of trial dictionaries.
        """
        block = []
        words = ["red", "blue", "green", "orange"]

        num_matched_trials = number_of_trials_per_block // 2

        # Add matched trials
        for _ in range(num_matched_trials):  # Half of the trials are matched
            block.append(create_trial(choice(words), matched=True))

        # Add mismatched trials
        # Half of the trials are mismatched
        for _ in range(number_of_trials_per_block - num_matched_trials):
            random_word = choice(words)
            block.append(create_trial(random_word, matched=False,
                        color=randomize_color(random_word, randint(0, 2))))

        shuffle(block)  # Shuffle the block for randomization
        return block


    def generate_blocks(num_of_blocks: int, number_of_trials_per_block: int) -> List[List[Dict[str, str]]]:
        """
        Generate a list of blocks, where each block contains a number of trials.

        Each trial is represented as a dictionary with string keys and values.

        Args:
            num_of_blocks (int): The number of blocks to generate.
            number_of_trials_per_block (int): The number of trials in each block.

        Returns:
            List[List[Dict[str, str]]]: A list of blocks, where each block is a list of trials. 
            Each trial is represented as a dictionary with string keys and values.
        """
        blocks = []

        for _ in range(num_of_blocks):
            # Generate a block with the specified number of trials
            block = generate_block(number_of_trials_per_block)
            blocks.append(block)

        shuffle(blocks)  # Shuffle the list of blocks to randomize their order
        return blocks


    BLOCKS = generate_blocks(NUMBER_OF_BLOCKS, NUMBER_OF_TRIALS_PER_BLOCK)


    # Example usage
    if __name__ == "__main__":
        BLOCKS = generate_blocks(NUMBER_OF_BLOCKS, NUMBER_OF_TRIALS_PER_BLOCK)
        print(len(BLOCKS))
        print(BLOCKS)

	
CITATION
========

::

	Stroop, J.R. (1935), "Studies of interference in serial verbal reactions", Journal of Experimental Psychology 18 (6): 643–662