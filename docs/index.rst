What is SMILE?
==============

.. image:: _static/smile_example.png
    :width: 375
    :height: 241
    :align: right

SMILE is the State Machine Interface Library for Experiments. In broad terms, a
state machine is an abstract device that stores the current status of relevant
input events, then initiates an action depending on a predetermined set of
rules.

The goal when developing SMILE was to create an easy to use experiment building
library that has millisecond accurate timing. SMILE is written so that the end
user doesn't have to worry about things like timing, event handling, or logging
data. With the help of the very powerful **Python** programming language and
**Kivy**, a module create to help make video games, SMILE is able to accomplish
all of its goals!

What does a SMILE experiment look like?
=======================================

Like all programming language tutorials, the best way to start out is with a
simple **Hello, World** program. Below is hello.py, an example of what the
simplest SMILE experiment looks like:

.. code-block:: python

    from smile.common import *

    exp = Experiment()

    Label(text="Hello, World!", duration=5)

    exp.run()

In order to run this experiment from a computer that has SMILE installed, you
would use your favorite OS's command prompt and run the following line:

::

    >> python hello.py -s TestSubject

This would create a full screen window that was black with the words
**Hello, World!** in white across the center of the screen, and just like that
we are SMILEing!

Now let us go through our SMILE experiment line by line and see what each of
them does.

**First** is the line *exp = Experiment()*. This line is the initialization line
for SMILE. This tells SMILE that it should prepare to see states being declared.

**Second** is the line *Label(text="Hello, World!", duration=5)*. **Label** is a
SMILE visual state that displays text onto the screen. Certain SMILE states take
a *duration*, and this state's duration is 5. This means the state will remain
showing on the screen for 5 seconds.

**Third** is the line *exp.run()*. This line signals to SMILE that you have finished
building your experiment and that it is ready to run. SMILE will then run your
experiment from start to finish and exit the experiment window when a
participant has finished.

Whats Next?
===========

In order to get yourself ready to start smiling, the first thing you want to do
is install SMILE and its dependencies. After that is a section that delves
deeper into SMILE and how to write more complicated experiments.

.. toctree::
   :maxdepth: 1

   install
   tutorial
   how_to_smile
   real_examples
   accessing_data
   smile


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

