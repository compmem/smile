from smile.common import *
from smile.audio import RecordSoundFile
from random import *
from math import *

#execute both the configuration file and the
#stimulus generation file
execfile("config.py")
execfile("gen_stim.py")

#Define the Experiment Variable
    exp = Experiment()

    #Show the instructions as an RstDocument Viewer on the screen
    init_text = RstDocument(text=instruct_text, width=600, top=exp.screen.top, height=exp.screen.height)
    with UntilDone():
        #Once you press any key, the UntilDone will cancel the RstDocument,
        #allowing the rest of the experiment to continue running.
        keypress = KeyPress()

    #Initialize the block counter, only used because we need
    #unique names for the .wav files later.
    exp.blockNum = 0

    #Initialize the Loop as "with Loop(list_like) as reference_variable_name:"
    with Loop(trials) as block:
        #Initialize the trial counter, only used because we need
        #unique names for the .wav files later.
        exp.trialNum = 0

        inter_stim = Label(text = '+', font_size = 80, duration = interBlockDur)
        #Initialize the Loop as "with Loop(list_like) as reference_variable_name:"
        with Loop(block.current) as trial:
            #Display the word, with the appropriate colored text
            t = Label(text=trial.current['word'], font_size=48, color=trial.current['color'])
            with UntilDone():
                #The Label will stay on the screen for as long as
                #the RecordSoundFile state is active. The filename
                #for this state is different for each trial in each block.
                rec = RecordSoundFile(filename="b_" + Ref(str,exp.blockNum) + "_t_" + Ref(str, exp.trialNum),
                                      duration=recDuration)
            #Log the color and word that was presented on the screen,
            #as well as the block and trial number
            Log(name='Stroop', stim_word=trial.current['word'], stim_color=trial.current['color'],
                block_num=exp.blockNum, trial_num=exp.trialNum)
            Wait(interStimulusInterval)
            #Wait for a duration then present the fixation
            #cross again.
            inter_stim = Label(text = '+', font_size = 80, duration = interBlockDur)
            #Increase the trialNum
            exp.trialNum += 1
        #Increase the blockNum
        exp.blockNum += 1
    #Run the experiment!
    exp.run()
