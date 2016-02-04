from smile.common import *
import random

words = ['plank','dear','thopter','initial','pull','complicated','assertain','biggest']
temp = []

for i in range(len(words)):
    condition = len(words[i])%2
    temp.append({'stimulus':words[i], 'condition':condition})
words = temp
random.shuffle(words)

#Needed Parameters of the Experiment
interStimulusDuration=1
maxResponseTime=4
keys = ['J','K']
#We are ready to start building the Epxeriment!
exp = Experiment()

with Loop(words) as trial:
    Label(text=trial.current['stimulus'])
    with UntilDone():
        kp = KeyPress(keys=keys, duration=maxResponseTime, correct_resp=Ref.getitem(keys,trial.current['condition']))
    Wait(interStimulusDuration)
    Log(name='Loop',
           correct=kp.correct,
           time_to_respond=kp.rt)
    Wait(interStimulusDuration)
exp.run()
