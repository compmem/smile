#freekey.py
from smile.common import *
from smile.freekey import FreeKey

#execute both the configuration file and the
#stimulus generation file
from config import *
from gen_stim import *

#Initialize the Experiment
exp = Experiment()

#Show the instructions to the paricipant
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
