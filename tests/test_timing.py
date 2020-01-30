# load all the states
from smile.common import *
from smile.startup import InputSubject

# set the dur and isi for each trial
trials = [{'dur': d, 'isi': i}
          for d, i in zip([.005, .010, .020, .050, .100, .200, .500, 1.0],
                          [.005, .010, .020, .050, .100, .200, .500, 1.0])]

# add in a bunch of fast switches
trials = [{'dur': .005, 'isi': .005}]*10 + trials

# double length, reverse, and repeat
trials = trials*100
trials_copy = trials[:]
trials_copy.reverse()
trials.extend(trials_copy)
print(trials)

# create an experiment
exp = Experiment(background_color='black')

InputSubject()

Wait(1.0)

with Loop(trials) as trial:
    bg = Rectangle(color='WHITE', size=exp.screen.size,
                   duration=trial.current['dur'])
    Wait(until=bg.disappear_time)
    Wait(trial.current['isi'])
    on2 = Rectangle(color='WHITE', size=exp.screen.size,
                    duration=trial.current['dur'])
    Wait(until=on2.disappear_time)
    Wait(trial.current['isi'])
    # log the on and off times
    Log(flush=False,
        name="timing",
        on1=bg.appear_time,
        off1=bg.disappear_time,
        on2=on2.appear_time,
        off2=on2.disappear_time,
        dur=trial.current['dur'],
        isi=trial.current['isi'],
        )

Wait(1.0)

if __name__ == '__main__':
    exp.run()
