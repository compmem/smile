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
