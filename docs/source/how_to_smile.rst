What is SMILE?
--------------

SMILE is a State Machine Interface Library for Experiments. In broad terms, a
state machine is an abstract device that stores the current status of relevant
input events, then initiates an action depending on a predetermined set of
rules. The goal of a state machine is to build objects that can be in many
possible states and to define the rules for transitioning from one of those
states to another. The goal of SMILE is to create an easy to use State Machine
Interface where the hardest part about coding an experiment will be the
stimulus list generation. A common example used to describe a state machine is
a stoplight: in this case, the three possible states are a red state, a green
state, and a yellow state. There is a set order of cycling through these
states; specifically, red transition so green, green transitions to yellow, and
yellow cycles back to red.

Through SMILE, we have developed a state machine interface between the
experimenter and Kivy, a python library that specializes in creating and
displaying stimulus on the screen in the form of widgets. With Smile, you are
able to build a Psychology experiment without the hassle of handling any of the
timing, the logging of data, or the presenting of stimulus. SMILE is concidered
to be a hierarchical state machine.  This is because all of the states in
SMILE have a parent-child relationship that comes into play when dealing with
the timing of multiple states at the same time.

What is A Hierarchical State Machine?
-------------------------------------
A Hierarchical State Machine is a state machine that relies on both the input
and all the previous states' information in order to make a decition as to
which state to go to next. It takes context information from the previous
states and the input parameters of the current state in order to pick the next
state. Another property of a HSM is the parent-child relationship that some
states have.  In the traffic light example, the green state and the yellow
state could be children of the vehicalsGO state, as in when vehicalsGo enters
it would run green state followed by yellow state after a set time. This
parent-child relationship allows a HSM to give control of serveral different
states to a single parent, allowing for the running of several states at once
and a higher level of logical progression between states.

SMILE posesses both of these qualities. SMILE makes takes care of the linking
of states



SMILE keeps the task of building an experiment simple by compartimentalizing an
experiment into 3 different parts, List Generation Runtime, Experimental Build
time, and Experimental Runtime.  The idea is that list generation and
experiment building should be completely seperated so that all you do in SMILE
is present stimulus.

Experimental Build time V.S. Runtime
------------------------------------

One of the key properties of SMILE is that
