from smile.common import *
import random

words = ['plank','dear','thopter','initial','pull','complicated','assertain','biggest']
random.shuffle(words)

#Needed Parameters of the Experiment
interStimulusDuration=1
stimulusDuration=2

#We are ready to start building the Epxeriment!
exp = Experiment()
with Loop(words) as trial:
    Label(text=trial.current, duration=stimulusDuration)
    Wait(interStimulusDuration)

exp.run()
