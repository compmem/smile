=================
Advanced SMILEing
=================

Screen Placement of Visual States
=================================

.. image:: _static/purple_box.png
    :width: 375
    :height: 241
    :align: right



In SMILE, any state that displays something to the screen is what is known as
a :py:class:`~smile.video.VisualState`. These states share the ability to set
their size, position, and relative position to each other. Every visual state
has the following basic attributes, and all of the following attributes can be
passed into the initialization of the visual states in your code:

- width

- height

- x

- y

Now, imagine if you would a scenario where you want to place a :py:class:`~smile.video.Label`
400 pixels above a :py:class:`~smile.video.TextInput`, which is 200 pixels to the left
of the bottom right hand corner of your screen. You could try and do the hard
calculation of those numbers by hand, or you could use our relativistic
positioning attributes to do the work for you.

By utilizing the relative position attributes, you can initialize your **VisualStates**
to the left or right, above or below, of each other. Here is how you would
write the above example.

.. code-block:: python
    :linenos:

    from smile.common import *
    exp = Experiment()

    with Parallel():
        lb1 = Label(text="I AM NEAR THE BOTTOM", right=exp.screen.right - 200,
                    bottom=exp.screen.bottom, duration=5)
        lb2 = Label(text="I AM ABOVE THE OTHER LABEL", right=lb1.right,
                    bottom=lb1.top + 400, duration=5)
    exp.run()

In the above example, we used the *right* attribute of the visual
states as both initialization parameters and attributes that we could access from
one state and apply to the next. We also used the attribute *bottom* which works
the exact same way. Here are a list of all the attributes that are in terms of
x, y, width, and height.

- bottom : y

- top : y + height

- left : x

- right : x + width

- center_x : (x + width) / 2

- center_y : (y + height) / 2

You are also able to combine multiple of these together to access a tuple value
that contains both pieces of information. These combined attributes are listed
below in terms of x, y, width, and height.

- center : ((x + width) / 2, (y + height) / 2)

- center_top : ((x + width) / 2, y + height)

- center_bottom : ((x + width) / 2, y)

- left_center : (x, (y + height) / 2)

- left_bottom : (x, y)

- left_top : (x, y + height)

- right_center : (x + width, (y + height) / 2)

- right_bottom : (x + width, y)

- right_top : (x + width, y + height)


Extending Smile
===============

There are cases where you might find yourself using SMILE and that it lacks
the functionality you might need to run your experiment properly. We have
several different ways in which you can **extend** SMILE to make it do the
things that you need it to do. The first of these is a **Subroutine**, which
is a section of state machine code that you might want to run at several
different points in your experiment, kind of like a function. The second is
referred to as **Wrapping Widgets**. You can wrap any widget written and defined
in **Kivy** into a SMILE :py:class:`~smile.video.WidgetState`.

Defining Subroutines
--------------------

In SMILE, we have special states called :py:class:`Subroutines <~smile.state.Subroutine>`.
**Subroutines** are special states that contain small chunks of state machine code
that your main experiment will need to run over and over again. Like a function,
a **Subroutine** is defined with the python `def` followed by the name of the
Subroutine. In SMILE, it is proper practice to name any state with the first
letter of every word a capitol letter.

Below is an example on how to define a **Subroutine** that displays a :py:class:`~smile.video.Label`
that will display a number that counts up from a passed in minimum number.

In our subroutine file (let's call it `test_sub.py`) we are going to need to
first import all of SMILE's common states.

.. code-block:: python

    from smile.common import *

That one line *usually* gives us all of the states we need to write an
experiment. Next, we need to write the definition line to our subroutine.

.. code-block:: python

    @Subroutine
    def CountUpFrom(self, minVal):

First, notice the `@Subroutine`. This allows *CountUpFrom* to be a subclass of
*Subroutine*, the general subroutine state.

.. note::

    Please note the *self* as the first argument passed into a subroutine. If you do not pass in self, SMILE will through an error. Please remember to pass in *self* as the first parameter when defining a subroutine.

Now we can write state machine code for inside our **Subroutine**.

.. code-block:: python

    from smile.common import *
    @Subroutine
    def CountUpFrom(self, minVal):
        # Initialize counter, Creates a Set state
        # and sets the variable at Experimental Runtime.
        # After this line, self.counter is a reference object
        # that can be reference anywhere else in this subroutine.
        self.counter = minVal
        # Define the Loop, loop 100 times
        with Loop(100):
            # Apply the plus-equals operator to
            # self.counter to add 5
            self.counter += 5
            # Display the reference self.counter in
            # string form. Ref(str, self.counter) is required
            # to apply the str() function to self.counter during
            # Experimental Runtime instead of Buildtime
            Label(text=Ref(str,self.counter), duration=.2)

Notice, if you will, `self.counter`. This creates a :py:class:`~smile.state.Set`
state that will set a new attribute to your **Subroutine** called `counter` and
will initialize it to `minVal` during :ref:`Experimental Runtime <run_build_time>`_.

Anything initialized with the `self.` will be able to be accessed from outside of
the **Subroutine**.  If we use the above Subroutine as an example, you can
initialize your **Subroutine** as `cup = CountUpFrom()` and call `cup.counter`
to get at the value of the counter. Below is an example of calling this
subroutine during an actual experiment.

.. code-block:: python

    from smile.common import *
    from countup import CountUpFrom

    exp = Experiment()

    # Just like writing any other state declaration
    cuf = CountUpFrom(10)

    # Print out the value of the counter in CountUpFrom
    # To the command line
    Debug(name="Count Up Stuff", end_counter=cuf.counter)
    exp.run()

It is just that easy.

Wrapping Kivy Widgets
---------------------

Currently, most of the visual states in SMILE are *wrapped* Kivy widgets. :py:class:`~smile.video.Rectangle`,
:py:class:`~smile.video.Image`, and :py:class:`~smile.video.Video` are all
examples of Kivy widgets that were wrapped in our `video.py` code and turned
into :py:class:`WidgetStates <~smile.video.WidgetState>`.

If there is a thing you want to do in SMILE, and you can't do it using our states,
and you can't do it by writing a :py:class:`~smile.state.Subroutine`, you have
come to the right place. To write a Kivy widget for SMILE, you only need to
learn a little bit about the SMILE backend and a little bit about Kivy. This
section is only for those who want to write their own widgets!

The `My First Widget<https://kivy.org/docs/tutorials/firstwidget.html>` gives a
good look on how to create a very basic Kivy widget and display it on a Kivy
app, but it is a sufficient start on how to create a Kivy widget none the less.

The example we will be looking at is dotbox.py. We had to write a program that
efficiently wrote tiny dots on the screen in an area, so the most efficient way
to do that is through the creation of a Kivy widget.

Here is the definition of our *DotBox*

.. code-block:: python


    @WidgetState.wrap
    class DotBox(Widget):
        """Display a box filled with random square dots.

        Parameters
        ----------
        num_dots : integer
            Number of dots to draw
        pointsize : integer
            Radius of dot (see `Point`)
        color : tuple or string
            Color of dots
        backcolor : tuple or string
            Color of background rectangle

        """

        # Define the widget Parameters for Kivy
        color = ListProperty([1, 1, 1, 1])
        backcolor = ListProperty([0, 0, 0, 0])
        num_dots = NumericProperty(10)
        pointsize = NumericProperty(5)

In our *DotBox*, we need to pass into our `__init__` method several different
parameters in order to create different kinds of DotBoxes.

- Color : A list of float values that represent the RGBA of the dots

- backcolor : A list of float values that represent the RGBA of the background

- num_dots : The number of random dots to generate

- pointsize : How big to draw the dots, pointsize by pointsize squares in pixels

Next, we are going to declare the `__init__` method for our `DotBox` widget.

.. code-block:: python

    def __init__(self, **kwargs):
        super(type(self), self).__init__(**kwargs)

        # Initialize variables for Kivy
        self._color = None
        self._backcolor = None
        self._points = None

        # Bind the variables to the widget
        self.bind(color=self._update_color,
                  backcolor=self._update_backcolor,
                  pos=self._update,
                  size=self._update,
                  num_dots=self._update_locs)

        # Call update_locs() to initialize the
        # point locations
        self._update_locs()

The `.bind()` method will bind each different attribute of the dot box to a
method callback that they might want to run if any of those attributes change.
An example of this is if in SMILE you create an :py:class:`~smile.video.UpdateWidget`
state where it updates a **DotBox** attribute, lets say the `num_dots` attribute,
the attribute change will cause Kivy to callback the corresponding function
attached with `.bind()`. Now we can define what those functions are.

.. code-block:: python

    # Update self._color.rgba
    def _update_color(self, *pargs):
        self._color.rgba = self.color

    # Update self._backcolor.rgba
    def _update_backcolor(self, *pargs):
        self._backcolor.rgba = self.backcolor

    # Update the locations of the dots, then
    # Call self._update() to redraw
    def _update_locs(self, *pargs):
        self._locs = [random.random()
                      for i in xrange(int(self.num_dots)*2)]
        self._update()

    # Update the size of all of the dots
    def _update_pointsize(self, *pargs):
        self._points.pointsize = self.pointsize

    # Draw the points onto the Kivy Canvas
    def _update(self, *pargs):
        # calc new point locations
        bases = (self.x+self.pointsize, self.y+self.pointsize)
        scales = (self.width-(self.pointsize*2),
                  self.height-(self.pointsize*2))
        points = [bases[i % 2]+scales[i % 2]*loc
                  for i, loc in enumerate(self._locs)]

        # draw them
        self.canvas.clear()
        with self.canvas:
            # set the back color
            self._backcolor = Color(*self.backcolor)

            # draw the background
            Rectangle(size=self.size,
                      pos=self.pos)

            # set the color
            self._color = Color(*self.color)

            # draw the points
            self._points = Point(points=points, pointsize=self.pointsize)

Any visual widget you create in Kivy will require some kind of drawing to the
canvas. In the above example, we use the line `with self.canvas` to define the
area in which we make calls to the graphics portion of Kivy, `kivy.graphics`. We
set the color of what we draw, then draw something. For example, `Color()` sets
the draw color, then `Rectangle()` tells **kivy.graphics** to draw a rectangle
of that color to the screen.

Since this Widget defined in Kivy will be wrapped with a **WidgetState**, you
can assume that this widget will have access to things like `self.pos`, `self.size`,
and obviously things like `self.x, self.y, self.width, self.height`.


dotbox.py in Full
-----------------

.. code-block:: python

    @WidgetState.wrap
    class DotBox(Widget):
        """Display a box filled with random square dots.

        Parameters
        ----------
        num_dots : integer
            Number of dots to draw
        pointsize : integer
            Radius of dot (see `Point`)
        color : tuple or string
            Color of dots
        backcolor : tuple or string
            Color of background rectangle

        """
        color = ListProperty([1, 1, 1, 1])
        backcolor = ListProperty([0, 0, 0, 0])
        num_dots = NumericProperty(10)
        pointsize = NumericProperty(5)

        def __init__(self, **kwargs):
            super(type(self), self).__init__(**kwargs)

            self._color = None
            self._backcolor = None
            self._points = None

            self.bind(color=self._update_color,
                      backcolor=self._update_backcolor,
                      pos=self._update,
                      size=self._update,
                      num_dots=self._update_locs)
            self._update_locs()

        def _update_color(self, *pargs):
            self._color.rgba = self.color

        def _update_backcolor(self, *pargs):
            self._backcolor.rgba = self.backcolor

        def _update_locs(self, *pargs):
            self._locs = [random.random()
                          for i in xrange(int(self.num_dots)*2)]
            self._update()

        def _update_pointsize(self, *pargs):
            self._points.pointsize = self.pointsize

        def _update(self, *pargs):
            # calc new point locations
            bases = (self.x+self.pointsize, self.y+self.pointsize)
            scales = (self.width-(self.pointsize*2),
                      self.height-(self.pointsize*2))
            points = [bases[i % 2]+scales[i % 2]*loc
                      for i, loc in enumerate(self._locs)]
            # points = [[random.randint(int(self.x+self.pointsize),
            #                           int(self.x+self.width-self.pointsize)),
            #            random.randint(int(self.y+self.pointsize),
            #                           int(self.y+self.height-self.pointsize))]
            #           for i in xrange(self.num_dots)]
            # points = [item for sublist in points for item in sublist]

            # draw them
            self.canvas.clear()
            with self.canvas:
                # set the back color
                self._backcolor = Color(*self.backcolor)

                # draw the background
                Rectangle(size=self.size,
                          pos=self.pos)

                # set the color
                self._color = Color(*self.color)

                # draw the points
                self._points = Point(points=points, pointsize=self.pointsize)

.. _setting_in_rt

Setting a variable in RT
========================

Like it is stated in :ref:`Build Time VS Run Time <run_build_time>`, in order to
set a variable in SMILE during **RT**, you must use the `exp.variable_name` syntax.
In this section we are going to be going over more of what happens when calling
that line in SMILE.

Below is a sample experiment where we set `exp.display_me` to a string.

.. code-block:: python

    from smile.common import *
    exp = Experiment()
    exp.display_me = "LETS DISPLAY THIS SECRET MESSAGE"
    Label(text=exp.display_me)
    exp.run()

This is a very simple experiment, but if you don't understand SMILE you might
not understand that `exp.display_me = "LETS DISPLAY THIS SECRET MESSAGE"` actually
creates a :py:class:`~smile.experiment.Set` state. A **Set** state takes a
string `var_name` that refers to a variable in an **Experiment** or to a new variable
that you would like to create, and a `value` that refers to the value that you
would like that variable to take on. The important thing to note is that `value`
can be a reference to a value. If `value` is a reference, it will be evaluated
during **RT**.  Below is an example of what the experiment would look like if we
changed the 3rd line.

.. code-block:: python

    from smile.common import *
    exp = Experiment()
    Set(var_name="display_me", value="LETS DISPLAY THIS SECRET MESSAGE")
    Label(text=exp.display_me)
    exp.run()

Both sample experiments run the exact same way, but the only difference is how
the code looks to you, the end user. The Set state is untimed, so it changes the
value of the variable immediately at enter. For more information look at the
docstring for :py:class:`~smile.experiment.Set` and the code behind the
**smile.experiment.Experiment.set_var()** method.

.. _func_ref_def

Performing Operations and Functions in RT
=========================================

You may or may not have noticed that you can't run your methods during **RT**
and have them run correctly. Look no further because here it will explain why
that happens, and how to fix it.

Since every SMILE experiment is separated into **BT** and **RT**, any calls to
functions or methods without using the proper SMILE syntax will run in **BT**
and not **RT**. In order to run a function or method, you need to use a :py:class:`~smile.ref.Ref`
or a :py:class:`~smile.state.Func`. Like is is stated in :ref:`The Reference Section <ref_def>`
of the state machine document, a **Ref** is a delayed function call.

**When you want to pass in the return value of a function to a SMILE state as a parameter**
then you want to use a **Ref**. The first parameter for a **Ref** call is always
the function you want to run, and the other parameters to that function call
are the rest of the parameters to the **Ref**.

Below is an example of a loop that displays the counter of the loop in a label
on the center of the screen. Since the :py:class:`~smile.state.Loop` counter is
an integer, you must first change it to a string. You can do this by creating a
**Ref** to call `str()`.

.. code-block:: python

    with Loop(100) as lp:
        #This Ref is a delayed function call to str where
        #one of the parameters is a reference. Ref also
        #takes care of evaluating references.
        Label(text=Ref(str, lp.i), duration=0.2)

**When you want to run a function during RT** then you would want to use a **Func**
state. **Func** creates a state that will not run the passed in function call
until the previous state leaves. Here is an example of using a **Func** to generate
the next set of stimulus for each iteration of a **Loop**. To access the return
value of a method or function call, you must access the `.result` attribute of
your **Func** state.

.. code-block:: python

    #Assume DisplayStim is a predefined Subroutine
    #that displays a list of stimulus, and assume that
    #gen_stim is a predefined function that generates
    #that stimulus
    with Loop(10) as lp:
        stim = Func(gen_stim, length=lp.i)
        DisplayStim(stim.result, duration=5)

.. note::

    Remember that you can pass in keyword arguments AND regular arguments into both Func states and Ref calls.

Timing the Screen Refresh VS Timing Inputs
==========================================

Before you read this section, it is important to understand how SMILE displays
each frame of your experiment. SMILE runs on a two buffer system, where when
a frame is being prepared, it is drawn to a *back buffer*. When everything is
drawn and/or ready, the *back buffer* is flipped to the *front buffer*, then the
back buffer is cleared to get ready for more drawing.

So, let's give a more detailed example. Let's say your experiment wants to display
a new :py:class:`~smile.video.Label` onto the screen. The first thing SMILE does
is draw the Label onto the back buffer, then calls for a **Blocking Flip**. A
**Blocking Flip** is when SMILE waits for everything to be finished writing to
the screen, then flips the next time it passes through the event loop if it is
around the flip interval. Then SMILE flips into **NonBlocking Flip** Mode. In
this mode, SMILE will try and flip the buffer as soon as anything changes.
SMILE switches to this mode to allow Kivy to update the screen whenever it needs
to. The other time in a Visual State's lifespan where SMILE calls for a **Blocking Flip**
is when it disappears from the screen. SMILE uses **Blocking Flips** for the
appearance and disappearance of a VisualState to accurately track the timing of
those two events.

In SMILE, the end user can force the 2 different modes of updating the screen using
:py:class:`~smile.video.BlockingFlip` and :py:class:`~smile.video.NonBlockingFlip`.
They both are important, for they both grant the ability to prioritize different
aspects of an experiment, *input* or *output*, when it comes to timing things as
accurately as possible.

A **NonBlockingFlip** is used when the timing of visual stimulus isn't the most
important. If you force SMILE into this mode, you gain a much more accurate
timing of input, like mouse and keyboard. You can force SMILE to do
NonBlockingFlips by putting this state in parallel with whatever you are wanting
to run in NonBlockingFlip Mode. Below is a mini example of such a **Parallel**

.. code-block:: python

    with Parallel() as p:
        NonBlockingFlip()
        Label(text="PRESS NOW!!!")
        kp = KeyPress()

A **BlockingFlip** is used when the timing of a when things appear on the
screen is more important than when the timing of inputs happens. Using this
mode, you can :py:class:`~smile.state.Record` the changes in `exp._last_flip`.
An example of doing that looks something like this.

.. code-block:: python

    with Parallel():
        BlockingFlip()
        vd = Video(source="test_vid.mp4")
        Record(name="video_record", flip=exp._last_flip)


Want to Contribute to SMILE?
============================

SMILE has a GitHub page that, if you find an issue and fix it or want to add
functionality to SMILE, you may make a pullrequest to. At `GitWash <https://github.com/compmem/smile/tree/master/docs/devel/gitwash>`_
you can find documents to better understand how to make use Git and how to make
changes and update SMILE.















