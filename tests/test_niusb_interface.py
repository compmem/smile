
from smile.experiment import Experiment
from smile.state import Wait, Parallel, Loop, Debug
from smile.video import Label
from smile.niusb_interface import NIPulse, init_task

exp = Experiment()

# Initialize the outlet
task1 = init_task(task_name="Task1", min_val=0.0, max_val=1.0,
                  chan_path='Dev1/ao0', chan_des="mychan1")
task2 = init_task(task_name="Task2", min_val=0.0, max_val=1.0,
                  chan_path='Dev1/ao1', chan_des="mychan2")

NIPulse(task1, push_vals=[1.0], width=0.10,)
NIPulse(task2, push_vals=[.5], width=0.10,)

# Wait for the experiment to start!
Wait(2.)

with Parallel():

    Label(text="We will now push 10 markers.", blocking=False)
    with Loop(10, blocking=False):

        ni1 = NIPulse(task1, push_vals=[1.0], width=0.10,)
        Wait(1.0)
        ni2 = NIPulse(task2, push_vals=[.5], width=0.10,)

        Wait(until=ni2.pulse_off)
        Wait(1.)
        Debug(a=ni1.pulse_on, b=ni2.pulse_off)

exp.run()
