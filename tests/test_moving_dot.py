from smile.experiment import Experiment
from smile.state import UntilDone, Meanwhile, Wait, Loop, Debug
from smile.keyboard import KeyPress
from smile.moving_dot import MovingDots

# A testing set to show all the different things you can change when
# setting motion_props during run-time.
testing_set = [[{"coherence": 0.1, "direction": 0,
                 "direction_variance": 0, "speed": 400},
                {"coherence": 0.5, "direction": 180,
                 "direction_variance": 0, "speed": 50}],
               [{"coherence": 0.5, "direction": 0,
                 "direction_variance": 0, "speed": 50,
                 "lifespan": .6, "lifespan_variance": .5},
                {"coherence": 0.1, "direction": 180,
                 "direction_variance": 10, "speed": 400,
                 "speed_variance": 200}]]
exp = Experiment(background_color=("purple", .3))

Wait(.5)

g = MovingDots(radius=300,
               scale=10,
               num_dots=4,
               motion_props=[{"coherence": 0.25, "direction": 0,
                              "direction_variance": 0},
                             {"coherence": 0.25, "direction": 90,
                              "direction_variance": 0},
                             {"coherence": 0.25, "direction": 180,
                              "direction_variance": 0},
                             {"coherence": 0.25, "direction": 270,
                              "direction_variance": 0}])
with UntilDone():
    KeyPress()
    with Meanwhile():
        g.slide(color='red', duration=4.0)
Wait(.25)

with Loop(4):
    MovingDots()
    with UntilDone():
        KeyPress()

md = MovingDots(radius=300, scale=3, num_dots=200,
                motion_props=[{"coherence": 0.25, "direction": 0,
                               "direction_variance": 0},
                              {"coherence": 0.25, "direction": 180,
                               "direction_variance": 0},])
with UntilDone():
    with Loop(testing_set) as ts:
        Wait(3.)
        md.motion_props = ts.current
    Wait(5.)

Debug(rate=g.widget.refresh_rate)
exp.run(trace=False)
