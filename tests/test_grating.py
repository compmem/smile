


from smile.experiment import Experiment
from smile.state import UntilDone, Wait, Parallel, Serial
from smile.keyboard import KeyPress
from smile.video import Label
from smile.grating import Grating
import math

exp = Experiment(background_color="#4F33FF")

g = Grating(width=250, height=250, contrast=0.1)
with UntilDone():
    KeyPress()
    g.update(bottom=exp.screen.center)
    KeyPress()

g = Grating(width=500, height=500, envelope='Gaussian', frequency=75,
            phase=11.0, color_one='blue', color_two='red', contrast=0.25)
with UntilDone():
    KeyPress()
    g.update(bottom=exp.screen.center)
    KeyPress()

with Parallel():
    g = Grating(width=256, height=256, frequency=20,
                envelope='Circular', std_dev=7.5,
                contrast=0.75,
                color_one='green', color_two='orange')
    lbl = Label(text='Grating!', bottom=g.top)
with UntilDone():
    # kp = KeyPress()
    with Parallel():
        g.slide(phase=-8 * math.pi, frequency=10.,
                bottom=exp.screen.bottom,
                duration=6.)
        g.slide(rotate=90, duration=2.0)
        with Serial():
            Wait(2.0)
            lbl.slide(top=g.bottom, duration=4.)

with Parallel():
    g = Grating(width=1000, height=1000, frequency=10, envelope='Linear',
                std_dev=20, contrast=0.4,
                color_one='blue', color_two='red')
    lbl = Label(text='Grating!', bottom=g.top)
with UntilDone():
    kp = KeyPress()
    with Parallel():
        g.slide(phase=-8 * math.pi, frequency=10.,
                left=exp.screen.left,
                duration=6.)
        g.slide(rotate=90, duration=2.0)
        with Serial():
            Wait(2.0)
            lbl.slide(top=g.bottom, duration=4.)

exp.run(trace=False)
