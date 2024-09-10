from smile.common import *
from smile.freekey import FreeKey

# execute both the configuration file and the
# stimulus generation file
from config import *
from gen_stim import *

# Initialize the Experiment
exp = Experiment(debug=True)

# Show the instructions to the participant
RstDocument(text=instruct_text, base_font_size=RST_FONT_SIZE,
            width=RST_WIDTH, height=exp.screen.height)
with UntilDone():
    # When a KeyPress is detected, the UntilDone
    # will cancel the RstDocument state
    KeyPress()
# Start the experiment Loop
with Loop(blocks) as block:
    Wait(INTER_BLOCK_INTERVAL)
    with Loop(block.current['study']) as study:
        # Present the Fixation Cross
        Label(text="+", duration=INTER_STIMULUS_INTERVAL, font_size=FONT_SIZE)

        # Present the study item and add debug information for current stimulus
        Debug(study.current)
        Label(text=study.current, duration=STIMULUS_DURATION, font_size=FONT_SIZE)

    Wait(PRE_FREE_KEY_INTERVAL)

    # Start FreeKey session
    fk = FreeKey(Label(text="XXXXXXX", font_size=FONT_SIZE),
                 max_duration=block.current['duration'])
    # Log everything!
    Log(block.current,
        name="FreeKey",
        responses=fk.responses)
# Run the experiment
exp.run()
