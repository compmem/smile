from smile.experiment import Experiment
from smile.state import Wait, Parallel, Loop
from smile.video import Label
from smile.socket_interface import init_socket_outlet, SocketPush
# Initialize the outlet
OUTLET = init_socket_outlet(uniq_ID='SocketMarket', server='localhost',
                            port=1234)

exp = Experiment()

# Signal the beginning of the experiment.
SocketPush(socket=OUTLET, msg="<TRIGGER>300</TRIGGER>")

# Wait for the experiment to start!
Wait(2.)

with Parallel():

    Label(text="We will now push 10 markers.", blocking=False)
    with Loop(10, blocking=False):

        # Create the push state
        push_out = SocketPush(socket=OUTLET, msg="<TRIGGER>55</TRIGGER>")

        # Log send_time if you want easy access
        # Log(name="MARKERS",
        #     push_time=push_out.send_time)

        Wait(1.)

exp.run()
