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

# load all the states
from smile import *
from smile.pulse import Pulse

# make some ordered groupings
from pyglet.graphics import OrderedGroup

background = OrderedGroup(0)
foreground = OrderedGroup(1)

# create an experiment
#exp = Experiment()
exp = Experiment(screen_ind=0, resolution=(1024,768), pyglet_vsync=False)

# pulse vars
DO_PULSE = True
PULSE_ISI = 2.0
PULSE_JITTER = 2.0

# back color
BACK_COLOR = (.25,.25,.25,1.0)

# stim config
BOX_WIDTH = 75
BOX_HEIGHT = 75
BOX_OFFSET = 150
ORIENT_SIZE = 54
BOX_COLORS = [(0,255,0,255),(0,0,255,255)]
RANDOM_MAPPING = True
if RANDOM_MAPPING:
    # shuffle the box colors relative to response
    random.shuffle(BOX_COLORS)
# response config
RESPS = ['F','J']

# list def
items = [{'color':BOX_COLORS[0], 'condition':'+', 'side':'L', 'correct_resp':RESPS[0]},
         {'color':BOX_COLORS[1], 'condition':'+', 'side':'R', 'correct_resp':RESPS[1]},
         {'color':BOX_COLORS[0], 'condition':'-', 'side':'R', 'correct_resp':RESPS[0]},
         {'color':BOX_COLORS[1], 'condition':'-', 'side':'L', 'correct_resp':RESPS[1]},
         #{'color':BOX_COLORS[0], 'condition':'~', 'side':'C', 'correct_resp':RESPS[0]},
         #{'color':BOX_COLORS[1], 'condition':'~', 'side':'C', 'correct_resp':RESPS[1]}
]
# total trials must be multiple of len(items)
NUM_REPS = 8
NUM_TRIALS = len(items)*NUM_REPS
trials = items*NUM_REPS
random.shuffle(trials)

# timing
ISI = 1.0
JITTER = .5
MIN_RT = .050

# do the actual experiment
BackColor(BACK_COLOR)

# start pulsing
if DO_PULSE:
    Set('keep_pulsing',True)
    with Parallel():
        with Loop(conditional=Get('keep_pulsing')):
            # send the pulse
            pulse=Pulse()
            # wait a tiny bit to make sure the end time is registered
            Wait(.015, stay_active=True)
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

# present the mapping
with Parallel():
    tm = Text('Response Mapping:', 
              y=exp['window'].height//2 + 100,
              font_size=24)
    to = Text('+', font_size=ORIENT_SIZE)
    rl = Rectangle(x=to['x'] - BOX_OFFSET, width=BOX_WIDTH, height=BOX_HEIGHT,
                   color=BOX_COLORS[0])
    rr = Rectangle(x=to['x'] + BOX_OFFSET, width=BOX_WIDTH, height=BOX_HEIGHT,
                   color=BOX_COLORS[1])
    tlk = Text('Press '+RESPS[0], x=rl['x'],
               y=rl['y']-BOX_HEIGHT//2-25, anchor_y='top')
    trk = Text('Press '+RESPS[1], x=rr['x'],
               y=rr['y']-BOX_HEIGHT//2-25, anchor_y='top')
    tb = Text('Press SPACEBAR to begin the next block.', 
              y=exp['window'].height//2 - 250,
              font_size=18)

# wait for keypress to move on
KeyPress(keys=['SPACE'])
Parallel([Unshow(t) for t in [tm,to,rl,rr,tlk,trk,tb]])

# wait before starting
Wait(ISI, JITTER)

# Put up orient
orient = Text('+', font_size=ORIENT_SIZE, group=background)

# loop over trials
with Loop(trials) as trial:
    # see where to put the stim
    Set('offset',0)
    If(trial.current['side']=='L',
       Set('offset',-BOX_OFFSET),
       If(trial.current['side']=='R',
          Set('offset',BOX_OFFSET)))

    # show the stim
    with Parallel():
        rect = Rectangle(x=Get('offset')+Ref(exp['window'],'width')//2, 
                         width=BOX_WIDTH, height=BOX_HEIGHT,
                         color=trial.current['color'],
                         group=foreground)
        with Serial():
            # wait some before accepting input
            Wait(MIN_RT)
            kp = KeyPress(keys=RESPS,
                          base_time=rect['last_flip']['time'],
                          correct_resp=trial.current['correct_resp'])
            Unshow(rect)

    # Log the trial
    Log(subject=exp.subj,
        info=exp.info,
        trial_num=trial['i'],
        condition=trial.current['condition'],
        resp=kp['pressed'],
        rt=kp['rt'],
        color=trial.current['color'],
        side=trial.current['side'],
        test_time=rect['last_flip'],
        correct=kp['correct'])

    # wait the ISI
    Wait(ISI, JITTER)

# unshow the orient
Unshow(orient)

Text('Done!!!', font_size=24)

# finish pulsing
if DO_PULSE:
    Set('keep_pulsing',False)
    serial_exp.__exit__(None, None, None)


if __name__ == '__main__':
    exp.run()


