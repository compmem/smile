================================
Smile Tutorial Basics!
================================

Hello Smilers! Today, I will show you how easy it is to start smiling! This tutorial is setup in parts. First, 
we will show you just how easy it to display a line of text on the screen.  Second, we will demonstrate how 
*stimulus generation* and *experiment code* is 100% seperate.  Third is a tutorial about how to added *User Input*

Hello World, Lets start Smiling!
================================

To start, I'll show you how the simplest *smile* experiment is programmed. Create a directory and add a file named **main.py**
::
	from smile import *

	exp = Experiment()

	Label(text="Hello World, Lets start Smiling!", duration=4)

	exp.run()

Go ahead and run **main.py**. If you do not know how to run a smile program, please refer to the 
`Running Smile <http://smile.org/RunningSmile.html>`_. You should see a black screen with the words "Hello World, Lets start Smiling!" 
apearing on the screen for 5 seconds.  What we have done is create a simple Smile **experiment**. When we run ``exp = Experiment()``
we are initializing oh default state, and telling out python program that we are about to start defining the states of our program. 

As said in our `What is Smile <http://smile.org/whatissmile.html>`_ page, Smile is a state machine. In your smile program you are telling
the *experiment* what states, in order defined, it should run. After you have defined the states that your experiment will go through, 
you add the line ``exp.run()``. This lets the *experiment* know that the definition process is complete, and the *experiment* is ready to run.
In the next step, we will see how stimulus generation and stimulus presentation can be seperated with ease in this **Loop** state example.

Looping over Lists! in Style
============================

To start this out, lets define the experiment we are going to create. We are going to present a list of randomly generated numbers to 
the participant for 2 seconds each and wait 1 second in between each number. Sounds complicated right? Wrong! With smile, all you need to
know is a basic idea of what the timing is in your experiment and **Smile** will take care of the rest! Create a new directory called 
exp2 and create a file called randNum1.py. In the file, lets define the stimulus generation algorithum. 
::
	import random

	def getRandomNumberList(number_of_numbers, max_number):
		temp_list = []
		for i in range(number_of_numbers):
			temp_list.append(random.randrange(max_number))
		return temp_list

Easy. This defines a *function* that returns a list of ``number_of_numbers`` random numbers where the maximum value of any number is less
than ``max_number``. From here, we can build an experiment that **Loop**s over the list of numbers. Lets setup the preliminary variables.
::
	#Needed Parameters of the Experiment
	maxNum=100
	numNum=10
	interStimulusDuration=1
	stimulusDuration=2

	listOfNumbers=getRandomNumberList(numNum, maxNum)

	#We are ready to start building the Epxeriment!
	exp = Experiment()

The default state that your *experiment* runs in is the **Serial** state.  **Serial** just means that every other state defined inside of
it is run in order, first in first out. So every state you define after ``exp = Experiment()`` will be exicuted fifo style. Next, we will 
define a staple of every smile experiment, out **Loop** state. 
::
	with Loop(listOfNumbers) as trial:
		Label(text=str(trial.current), duration=stimulusDuration)
		Wait(interStimulusDuration)

	exp.run()

Let me explain what is happeing here line by line. ``with Loop(listOfNumbers) as trial:`` has a lot of stuff going on.  **Loop** can be sent
your list as a parameter.  This tells smile to loop over ``listOfNumbers``. **Loop** also creates a reference variable, in our case we called 
it ``trial``. ``trial`` acts as a link between us building the experiment, and us running the experiment.  Until ``exp.run()`` is called, 
``trial`` will not have a value. The next line defines a **Label** state that displays text for a duration. By default, it displays in the 
middle of the experiment window. Notice that ``trial.current``. In order to access the numbers from our random list, we need to use 
``trial.current`` instead of listOfNumbers[x]. ``trial.current`` is a way to tell smile to access the *current* member of the 
``listOfNumbers`` while looping.

.. warning::
	Do not try and access or test the value of trial.current. As it is a reference variable, you will not be able to test the value of it outside of a smile state.  

The following is a complete version of randNum1.py
::
	from smile import *
	import random

	def getRandomNumberList(number_of_numbers, max_number):
		temp_list = []
		for i in range(number_of_numbers):
			temp_list.append(random.randrange(max_number))
		return temp_list
	
	#Needed Parameters of the Experiment
	maxNum=100
	numNum=10
	interStimulusDuration=1
	stimulusDuration=2

	listOfNumbers=getRandomNumberList(numNum, maxNum)

	#We are ready to start building the Epxeriment!
	exp = Experiment()
	with Loop(listOfNumbers) as trial:
		Label(text=str(trial.current), duration=stimulusDuration)
		Wait(interStimulusDuration)

	exp.run()

And Now, With user Input!
=========================

The final step for our basic smile tutorial is to add user input and loggin.  Lets define the experiment. Lets say we need to ask the 
participant to press J if the number on the screen is bigger than the last number presented, and K if the number is smaller than the 
last number presented. 













