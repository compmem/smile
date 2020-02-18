from smile.experiment import Experiment
from smile.state import Wait, UntilDone, Serial, Parallel
from smile.dotbot import DotBox


exp = Experiment(background_color="#330000")

Wait(1.0)

DotBox(duration=2.0, backcolor='blue')

db = DotBox(color='red')
with UntilDone():
    db.slide(center=exp.screen.right_top, duration=2.0)
    db.slide(center=exp.screen.left_top, duration=2.0)
    db.slide(center=exp.screen.center, duration=1.0)

db2 = DotBox(color='red', backcolor=(.1, .1, .1, .5))
with UntilDone():
    with Parallel():
        with Serial():
            db2.slide(color='blue', duration=1.0)
            db2.slide(color='olive', duration=1.0)
            db2.slide(color='orange', duration=1.0)
            db2.slide(pointsize=20, duration=1.0)
        db2.slide(size=(400, 400), duration=4.0)

db3 = DotBox(color='green', backcolor='purple', size=(400, 400))
with UntilDone():
    db3.slide(num_dots=50, duration=3.0)

Wait(2.0)
exp.run(trace=False)
