# load all the states
from smile.common import *

# execute both the configuration file and the
# stimulus generation file
from config import *
from gen_stim import *

# Define the experiment
exp = Experiment()
# Present the instructions to the participant
init_text = RstDocument(text=INSTRUCT_TEXT, width=RST_WIDTH,
                        font_size=RST_FONT_SIZE, top=exp.screen.top, height=exp.screen.height)
with UntilDone():
    # Once the KeyPress is detected, the UntilDone
    # cancels the RstDocument
    keypress = KeyPress()
# loop over study block
with Loop(trials) as trial:
    # Setup the list of study times.
    exp.study_times = []
    # orient stim
    orient = Label(text='+', duration=ORIENT_DURATION, font_size=FONT_SIZE)
    Wait(ORIENT_ISI)
    # loop over study items
    with Loop(trial.current['study_items']) as item:
        # present the letter
        ss = Label(text=item.current, duration=STUDY_DURATION,
                   font_size=FONT_SIZE)
        # wait some jittered amount
        Wait(STUDY_ISI)
        # append the time
        exp.study_times += [ss.appear_time['time']]
    # Retention interval
    Wait(RETENTION_INTERVAL - STUDY_ISI)
    # present the letter
    test_stim = Label(
        text=trial.current['test_item'], bold=True, font_size=FONT_SIZE)
    with UntilDone():
        # wait some before accepting input
        Wait(RESP_DELAY)
        # Wait until the test_stim label has the appear_time attribute
        Wait(until=test_stim.appear_time)
        # After the KeyPress is detected, the UntilDone
        # cancels the Label test_stim and allows the
        # experiment to continue.
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
        correct=(((trial.current['condition'] == 'target') &
                 (ks.pressed == RESP_KEYS[0])) |
                 ((trial.current['condition'] == 'lure') &
                 (ks.pressed == RESP_KEYS[1]))))
    Wait(ITI)
# run that exp!
exp.run()
