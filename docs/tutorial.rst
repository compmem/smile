================================
Smile Tutorial Basics!
================================

Hello Smilers! Today, I will show you how easy it is to start smiling! This tutorial is setup in parts. First, we will show you just how easy it to display a line of text on the screen.  Second, we will demonstrate how *stimulus generation* and *experiment code* is 100% seperate. Third is a tutorial about how to added *User Input*

Hello World, Lets start Smiling!
================================

To start, I'll show you how the simplest *smile* experiment is programmed. Create a directory and add a file named **main.py**
::
	from smile import *

	exp = Experiment()

	Label(text="Hello World, Lets start Smiling!", duration=4)

	exp.run()

Go ahead and run **main.py**. If you do not know how to run a smile program, please refer to the `Running Smile <http://smile.org/RunningSmile.html>`_. You should see a black screen with the words "Hello World, Lets start Smiling!" apearing on the screen for 5 seconds.  What we have done is create a simple Smile **experiment**. When we run ``exp = Experiment()``we are initializing oh default state, and telling out python program that we are about to start defining the states of our program. 

As said in our `What is Smile <http://smile.org/whatissmile.html>`_ page, Smile is a state machine. In your smile program you are tellingthe *experiment* what states, in order defined, it should run. After you have defined the states that your experiment will go through, you add the line ``exp.run()``. This lets the *experiment* know that the definition process is complete, and the *experiment* is ready to run.In the next step, we will see how stimulus generation and stimulus presentation can be seperated with ease in this **Loop** state example.

Looping over Lists! in Style
============================

To start this out, lets define the experiment we are going to create. We are going to present a list of randomly generated numbers to the participant for 2 seconds each and wait 1 second in between each number. Sounds complicated right? Wrong! With smile, all you need to know is a basic idea of what the timing is in your experiment and **Smile** will take care of the rest! Create a new directory called exp2 and create a file called randNum1.py. In the file, lets define the stimulus generation algorithum. 
::
	import random

	def getRandomNumberList(number_of_numbers, max_number):
		temp_list = []
		for i in range(number_of_numbers):
			temp_list.append(random.randrange(max_number))
		return temp_list
	...

Easy. This defines a *function* that returns a list of ``number_of_numbers`` random numbers where the maximum value of any number is less than ``max_number``. From here, we can build an experiment that **Loop**s over the list of numbers. Lets setup the preliminary variables.
::
	#Needed Parameters of the Experiment
	maxNum=100
	numNum=10
	interStimulusDuration=1
	stimulusDuration=2

	listOfNumbers=getRandomNumberList(numNum, maxNum)

	#We are ready to start building the Epxeriment!
	exp = Experiment()
	...

The default state that your *experiment* runs in is the **Serial** state.  **Serial** just means that every other state defined inside ofit is run in order, first in first out. So every state you define after ``exp = Experiment()`` will be exicuted fifo style. Next, we will define a staple of every smile experiment, out **Loop** state. 
::
	with Loop(listOfNumbers) as trial:
		Label(text=str(trial.current), duration=stimulusDuration)
		Wait(interStimulusDuration)

	exp.run()

Let me explain what is happeing here line by line. ``with Loop(listOfNumbers) as trial:`` has a lot of stuff going on.  **Loop** can be sent your list as a parameter.  This tells smile to loop over ``listOfNumbers``. **Loop** also creates a reference variable, in our case we called it ``trial``. ``trial`` acts as a link between us building the experiment, and us running the experiment.  Until ``exp.run()`` is called, ``trial`` will not have a value. The next line defines a **Label** state that displays text for a duration. By default, it displays in the middle of the experiment window. Notice that ``trial.current``. In order to access the numbers from our random list, we need to use ``trial.current`` instead of listOfNumbers[x]. ``trial.current`` is a way to tell smile to access the *current* member of the ``listOfNumbers`` while looping.

.. warning::
	Do not try and access or test the value of trial.current. As it is a reference variable, you will not be able to test the value of it outside of a smile state.  

The final version of **randNum1.py**
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

The final step for our basic smile tutorial is to add user input and loggin.  Lets define the experiment. Lets say we need to ask the participant to press J if the number on the screen is bigger than the last number presented, and K if the number is smaller than the last number presented. We have to say that the participants have only 4 seconds to answer. In this tutorial I will show you how we can setup our experiment so that when they press a key to answer, the stimulus will drop off the screen and start the next iteration of the loop.  

This tutorial will also teach you how to compare **trial.current** comparisons. Create a directory called NumberRemember and create a file within the directory called numMain.py. First, we will bring over the function we defined earlier called ``getRandomNumberList``.  We are going to change it a little bit to make sure that there aren't any 2 numbers the same next to each other.  
::
	import random

	def getRandomNumberList(number_of_numbers, max_number):
		temp_list = []
		last_number = 0
		for i in range(number_of_numbers):
			temp_number = random.randrange(max_number)
			while(temp_number == last_number):
				temp_number = random.randrange(max_number) 
			temp_list.append(temp_number)
			last_number = temp_number
		return temp_list
	...

Our list gen is only a little more complicated than before but it insures that the numbers presented will not be the same next to each other. Like in the last example, next we have to initialize all of our experiment parameters.
::
	#Needed Parameters of the Experiment
	maxNum=100
	numNum=10
	interStimulusDuration=1
	maxResponseTime=4
	keys = ['J','K']
	listOfNumbers=getRandomNumberList(numNum, maxNum)

	#We are ready to start building the Epxeriment!
	exp = Experiment()
	...

This only got changed a little; we changed the line ``stimulusDuration=2`` into ``maxResponseTime=4`` and we added a line about the **keys** that our participant will be pressing.  Next we are going to setup up our basic loop. We will start with the loop from the last example and work from there. 
::
	with Loop(listOfNumbers) as trial:
		Label(text=str(trial.current), duration=stimulusDuration)
		Wait(interStimulusDuration)

	exp.run()

The first thing we need to add to this loop is the ``UntilDone():`` state. An **UntilDone** state is a state that will run its children in *Serial* until the state above it has finished.Let me give you an example before we edit the loop above. 
:: 
	Label(text='Im on the screen for at most 5 seconds')
	with UntilDone():
		Label(text='Im On the screen for 3 seconds!', duration=3)
		Wait(2)
	...

As you can see, The first *Label* is on the screen for 5 seconds because the **UntilDone** state doesn't end until the second *Label* has ran 3 seconds and the *Wait* has ran 2 seconds.

Now we will implement this state into our loop. 
::
	with Loop(listOfNumbers) as trial:
		Label(text=str(trial.current))
		with UntilDone():
			kp = KeyPress(keys=keys)
		Wait(interStimulusDuration)

	exp.run()	 

This displays the current trial's number until you press a key then waits the inter-stimulus duration that we set earlier.  This isn't exactly what we want, but it is the start we need to fully understand what we are doing. Next we are going to edit ``kp = KeyPress(keys=keys)`` to include our response time duration. We also need to add in the ability to check and see if they answered correct. This will use the ``Set()`` function and the ``Get()`` function. 
::
	...
	Set(LastNumber=listOfNumbers[0])
	with Loop(listOfNumbers) as trial:
		Label(text=str(trial.current))
		with UntilDone():
			with If(Get('LastNumber') > trial.current):
				#If the last number presented is bigger, press the J key
				kp = KeyPress(keys=keys, duration=maxResponseTime ,correct_keys=keys[0])
			with Elif(Get('LastNumber') < trial.current):
				#If the last number presented is smaller, press the K key
				kp = KeyPress(keys=keys, duration=maxResponseTime, correct_keys=keys[1])
			with Else():
				#If this is the first trial? Dont worry about pressing anything. 
				Wait(maxResponseTime)
		Set(LastNumber=trial.current)
		Wait(interStimulusDuration)

	exp.run()

We now added 3 different ``with If()`` type states. ``with If()`` allows us to branch our experiment depending on what the conditions of the stimulus are.  This tool gives us the ability to change the **correct_keys** during experiment runtime. Next I will explain how we obtained the information from experiment run time in order to do the comparison needed for an effective ``If()`` state.  

The two functions needed to do this kind of comparison were the ``Set()`` function and the ``Get()`` function.  **Set** is how we tell smile to set the value of a *experimental runtime variable* that you are able to pull and test in during runtime. You may have noticed that in **Set** there were no single quotes around the variable but in **Get** there were single quotes. This is on purpose. 

The Last thing we need to add to this experiment, after the each ``KeyPress()`` call, is the **Log**. Log is pretty simple. Where ever you put it in the exepriment, it will run the Log state that will save out a **.csv** file to a folder called **data** in your experiment directory under whatever name you put in the *name* field. 
::
	...
	Log(
		'name':'Loop',
		'correct':kp.correct,
		'time_to_respond':kp.rp
		) 
	...
	Log(
		'name':'Loop',
		'correct':kz.correct,
		'time_to_respond':kz.rp
		) 
	

With this line, each iteration of the loop in the experiment will save our a line into **Loop.csv** all of the values defined in the ``Log()`` call. The loop will look like this
::
	...
	Set(LastNumber=listOfNumbers[0])
	with Loop(listOfNumbers) as trial:
		Label(text=str(trial.current))
		with UntilDone():
			with If(Get('LastNumber') > trial.current):
				#If the last number presented is bigger, press the J key
				kp = KeyPress(keys=keys, duration=maxResponseTime ,correct_keys=keys[0])
				Log(
					'name':'Loop',
					'correct':kp.correct,
					'time_to_respond':kp.rp
					) 
			with Elif(Get('LastNumber') < trial.current):
				#If the last number presented is smaller, press the K key
				kz = KeyPress(keys=keys, duration=maxResponseTime, correct_keys=keys[1])
				Log(
					'name':'Loop',
					'correct':kz.correct,
					'time_to_respond':kz.rp
					)
			with Else():
				#If this is the first trial? Dont worry about pressing anything. 
				Wait(maxResponseTime)
		Set(LastNumber=trial.current)
		Wait(interStimulusDuration)
	
.. warning::
	Since this is a state machine, you must assign your **KeyPress** calls to differently named variables, for they will both exist during runtime.  Log will only run if it is in the correct ``If()`` state though, so you dont have to worry about that.

The final version of **numMain.py**
::
	import random
	from smile import *

	def getRandomNumberList(number_of_numbers, max_number):
		temp_list = []
		last_number = 0
		for i in range(number_of_numbers):
			temp_number = random.randrange(max_number)
			while(temp_number == last_number):
				temp_number = random.randrange(max_number) 
			temp_list.append(temp_number)
			last_number = temp_number
		return temp_list

	#Needed Parameters of the Experiment
	maxNum=100
	numNum=10
	interStimulusDuration=1
	maxResponseTime=4
	keys = ['J','K']
	listOfNumbers=getRandomNumberList(numNum, maxNum)

	#We are ready to start building the Epxeriment!
	exp = Experiment()

	Set(LastNumber=listOfNumbers[0])
	with Loop(listOfNumbers) as trial:
		Label(text=str(trial.current))
		with UntilDone():
			with If(Get('LastNumber') > trial.current):
				#If the last number presented is bigger, press the J key
				kp = KeyPress(keys=keys, duration=maxResponseTime ,correct_keys=keys[0])
				Log(
					'name':'Loop',
					'correct':kp.correct,
					'time_to_respond':kp.rp
					) 
			with Elif(Get('LastNumber') < trial.current):
				#If the last number presented is smaller, press the K key
				kz = KeyPress(keys=keys, duration=maxResponseTime, correct_keys=keys[1])
				Log(
					'name':'Loop',
					'correct':kz.correct,
					'time_to_respond':kz.rp
					)
			with Else():
				#If this is the first trial? Dont worry about pressing anything. 
				Wait(maxResponseTime)
		Set(LastNumber=trial.current)
		Wait(interStimulusDuration)


Now you are ready to get Smiling!