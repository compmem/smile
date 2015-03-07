#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# global imports
import random
import string

# load all the states
from smile import *
from smile.pulse import Pulse
from smile.audio import Beep

# create an experiment
#exp = Experiment()
exp = Experiment(screen_ind=0, resolution=(1024,768), pyglet_vsync=False)

# config vars
DO_PULSE = True
PULSE_ISI = 2.0
PULSE_JITTER = 2.0

# list def
NUM_REPS = 1
NUM_RARE = 10
NUM_COMMON = 40
STIMS = {'visual':['X','O'],
         'auditory':['BEEP','BOOP']}
FREQS = {'BOOP':[400,400],
         'BEEP':[800,800]}
RESPS = ['F','J']
MODES = STIMS.keys()
CONDS = ['common']*NUM_COMMON + ['rare']*NUM_RARE

# timing
AUDIO_DUR = .5
AUDIO_ISI = 1.5
VISUAL_DUR = 1.0
VISUAL_ISI = 1.0
JITTER = .5
MIN_RT = .100
RESP_DUR = 1.25

# Each stim as rare
# Each response mapped to each stimulus
blocks = []
for mode in MODES:
    for reverse_stim in [True, False]:
        # pick the proper stim set
        stims = STIMS[mode]
        # reverse if required
        if reverse_stim:
            stims = stims[::-1]
        # map to common and rare
        stim = {'common':stims[0],
                'rare':stims[1]}

        # loop over response mappings
        for reverse_resp in [True, False]:
            # pick the responses
            resps = RESPS[:]
            if reverse_resp:
                resps = resps[::-1]
            # make the mapping
            resp = {'common':resps[0],
                    'rare':resps[1]}

            # shuffle the conds
            random.shuffle(CONDS)

            # make the block
            block = [{'cond':cond,
                      'modality':mode,
                      'common_stim':stim['common'],
                      'rare_stim':stim['rare'],
                      'common_resp':resp['common'],
                      'rare_resp':resp['rare'],
                      'stim':stim[cond],
                      'correct_resp':resp[cond]}
                     for cond in CONDS]

            # append to blocks
            blocks.append(block)
             
# shuffle the blocks
random.shuffle(blocks)

# do the actual experiment

# start pulsing
if DO_PULSE:
    Set('keep_pulsing',True)
    with Parallel():
        with Loop(conditional=Get('keep_pulsing')):
            # send the pulse
            pulse=Pulse()
            # wait a tiny bit to make sure the end time is registered
            Wait(.010, stay_active=True)
            # log it all
            Log(log_file='pulse.yaml',
                pulse_code=pulse['pulse_code'],
                pulse_start=pulse['pulse_time'],
                pulse_end=pulse['pulse_end_time'])
            # Wait the full jitter now
            Wait(duration=PULSE_ISI, jitter=PULSE_JITTER)
        serial_exp = Serial()

    # make the serial parent the active parent
    serial_exp.__enter__()


# give instructions
init_inst = """In this experiment we will present blocks of visual and auditory stimuli one stimulus at a time. Your task is to press the key corresponding to the matching stimulus as quickly and accurately as possible when each stimulus is presented. The mappings between stimuli and specific keyboard responses will change for each block.

The visual stimuli will be either an X or an O, while the auditory stimuli will either be a high-frequency Beep or a low-frequency Boop.

We will now review each stimulus prior to beginning the blocks. Press any key to continue.
"""
inst_txt = Text(init_inst, width=600, multiline=True)
KeyPress()
Unshow(inst_txt)

# show each stim
txt = Text("Press any key to see the visual stimuli.")
KeyPress()
Unshow(txt)
with Loop(STIMS['visual']) as stim:
    Show(Text(stim.current, font_size=24),
         duration=VISUAL_DUR)
    Wait(VISUAL_ISI, JITTER)

txt = Text("Press any key to hear the auditory stimuli.")
KeyPress()
Unshow(txt)
with Loop(STIMS['auditory']) as stim:
    with Parallel():
        Beep(duration=AUDIO_DUR, 
             freq=Ref(FREQS)[stim.current])
        Show(Text(stim.current, font_size=24),
             duration=VISUAL_DUR)
    Wait(VISUAL_ISI, JITTER)
    
# give instructions
final_inst = """Note that the words BEEP and BOOP will not be presented during the blocks.

We will now begin the actual experiment. Before each block we will display a screen specifying whether the block with be AUDIORY or VISUAL and what the mapping from the stimuli to the specific keys will be for that block. Please take a moment before beginning the block to learn the new mapping.

Press any key to continue.
"""
inst_txt = Text(final_inst, width=600, multiline=True)
KeyPress()
Unshow(inst_txt)

# loop over blocks
Set('left_stim','')
Set('right_stim','')
Set('stim_time',{'time':0,'error':0})
with Loop(blocks) as block:

    # show modality and mapping info
    If(block.current[0]['rare_resp']==RESPS[0],
       Parallel([Set('left_stim','rare'),Set('right_stim','common')]),
       Parallel([Set('left_stim','common'),Set('right_stim','rare')]))
    with Parallel():
        tm = Text(Ref(string.upper)(block.current[0]['modality'])+' Block', 
                  y=exp['window'].height//2 + 100,
                  font_size=20)
        tl = Text(block.current[0][Get('left_stim')+'_stim'], #+' = '+RESPS[0],
                  x=exp['window'].width//2 - 75,
                  anchor_x='right',
                  font_size=24)
        tr = Text(block.current[0][Get('right_stim')+'_stim'], #+' = '+RESPS[1],
                  x=exp['window'].width//2 + 75,
                  anchor_x='left',
                  font_size=24)
        tlk = Text('Press '+RESPS[0], x=tl['x']-tl['shown'].content_width//2, 
                   y=tl['y']-25, anchor_y='top')
        trk = Text('Press '+RESPS[1], x=tr['x']+tr['shown'].content_width//2, 
                   y=tr['y']-25, anchor_y='top')
        tb = Text('Press SPACEBAR to begin the next block.', 
                  y=exp['window'].height//2 - 150,
                  font_size=18)

    # wait for keypress to move on
    KeyPress(keys=['SPACE'])
    Parallel([Unshow(t) for t in [tm,tl,tr,tb,tlk,trk]])
    
    # show orienting stim
    orient = Text('+', font_size=24)
    Wait(VISUAL_DUR)

    # remove if visual
    If(block.current[0]['modality']=='visual', 
       Unshow(orient))

    # pause before trials
    Wait(VISUAL_ISI, JITTER)

    # loop over trials
    with Loop(block.current) as trial:
        with Parallel():
            # present stim
            with If(trial.current['modality']=='visual'):
                vstim = Show(Text(trial.current['stim'], font_size=24),
                             duration=VISUAL_DUR)
            with Else():
                astim = Beep(duration=AUDIO_DUR, 
                             freq=Ref(FREQS)[trial.current['stim']])
            with Serial():
                Wait(MIN_RT, stay_active=True)
                If(trial.current['modality']=='visual',
                   Set('stim_time',vstim['show_time']),
                   Set('stim_time',astim['sound_start']))
                kp = KeyPress(keys=RESPS, duration=RESP_DUR, 
                              base_time=Get('stim_time')['time'],
                              correct_resp=trial.current['correct_resp'])
        # log
        Log(trial.current,
            block=block['i'],
            trial=trial['i'],
            stim_on=Get('stim_time'),
            response=kp['pressed'],
            press_time=kp['press_time'],
            rt=kp['rt'],
            correct=kp['correct'])
                  
        # wait jittered isi
        If(trial.current['modality']=='visual',
           Wait(VISUAL_ISI, JITTER),
           Wait(AUDIO_ISI, JITTER))

    # remove orienting stim if auditory
    If(block.current[0]['modality']=='auditory', 
       Unshow(orient))


# finish pulsing
if DO_PULSE:
    Set('keep_pulsing',False)
    serial_exp.__exit__(None, None, None)

# show a thankyou
Wait(1.0)
txt = Text('Thank you!!! The task is complete.')
kp = KeyPress()
Unshow(txt)


if __name__ == '__main__':
    exp.run()


