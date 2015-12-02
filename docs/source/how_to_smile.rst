What is SMILE?
--------------

SMILE is a State Machine Interface Library for Experiments. In broad terms, a state machine is an 
abstract device that stores the current status of relevant input events, then initiates an action depending 
on a predetermined set of rules. The goal of a state machine is to build objects that can be in many possible 
states and to define the rules for transitioning from one of those states to another. The goal of SMILE is to 
create an easy to use State Machine Interface where the hardest part about coding an experiment will end up 
being the stimulus list generation. A common example used to describe a state machine is a stoplight: in this 
case, the three possible states are a red state, a green state, and a yellow state. There is a set order of 
cycling through these states; specifically, red transition so green, green transitions to yellow, and yellow 
cycles back to red. 

Through SMILE, we have developed a state machine interface between the experimenter and Kivy, a python library 
that specializes in creating and displaying things on the screen in the form of widgets. With Smile, you are 
able to build a Psychology experiment without the hassle of handling any of the timing, the logging of data, 
or the presenting of stimulus. 

What is A Hierarchical State Machine?
-------------------------------------







SMILE keeps the task of building an experiment simple by compartimentalizing an experiment into 3 different 
parts, List Generation Runtime, Experimental Build time, and Experimental Runtime.  The idea is that list 
generation and experiment building should be completely seperated so that all you do in SMILE is present 
stimulus. 

Experimental Build time V.S. Runtime
------------------------------------

One of the key properties of SMILE is that 