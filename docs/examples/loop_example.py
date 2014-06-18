

# load all the states
from smile import *

# create an experiment
exp = Experiment(screen_ind=0, pyglet_vsync=True)

# set up my list
#trials = ['zero','one','two']
trials = [str(i) for i in range(5)]
GOOD_RT = .5
RESP_KEYS = ['J','K']

Wait(1.0)

with Loop(trials) as trial:
    #Wait(.5)
    with Parallel():
        t = Text(trial.current)
        with Serial():
            Wait(.2)
            key = KeyPress(keys=RESP_KEYS, 
                           base_time=t['last_flip']['time'])
    Unshow(t)
    Set('good',key['rt']<GOOD_RT)
    with If(Get('good')) as if_state:
        with if_state.true_state:
            Show(Text('Awesome'), duration=1.0)
        with if_state.false_state:
            Show(Text('Bummer'), duration=1.0)

    Log(stim_txt=trial.current,
        stim_on=t['last_flip'],
        resp=key['pressed'],
        rt=key['rt'],
        good=Get('good'),
        trial_num=trial['i'])

    Wait(1.0)


Wait(1.0, stay_active=True)


if __name__ == '__main__':
    exp.run()


