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

To start this out, lets define the experiment we are going to create. We are going to present a list of predefined words to the participant for 2 seconds each and wait 1 second in between each word. Sounds complicated right? Wrong! With smile, all you need to know is a basic idea of what the timing is in your experiment and **Smile** will take care of the rest! Create a new directory called exp2 and create a file called randWord1.py. In the file, lets define the stimulus.
::
    words=['plank','dear','thopter','initial','pull','complicated','assertain','biggest']
    words.shuffle()	

Easy. Now we have a list of words that are randomly sorted. From here, we can build an experiment that **Loop**s over the list of words. Lets setup the preliminary variables.
::
    #Needed Parameters of the Experiment
    interStimulusDuration=1
    stimulusDuration=2

    #We are ready to start building the Epxeriment!
    exp = Experiment()
    ...

The default state that your *experiment* runs in is the **Serial** state.  **Serial** just means that every other state defined inside of it is run in order, first in first out. So every state you define after ``exp = Experiment()`` will be executed fifo style. Next, we will define a staple of every smile experiment, out **Loop** state. 
::
    with Loop(words) as trial:
        Label(text=str(trial.current), duration=stimulusDuration)
        Wait(interStimulusDuration)

    exp.run()

Let me explain what is happeing here line by line. ``with Loop(words) as trial:`` has a lot of stuff going on.  **Loop** can be sent your list as a parameter.  This tells smile to loop over ``words``. **Loop** also creates a reference variable, in our case we called it ``trial``. ``trial`` acts as a link between us building the experiment, and us running the experiment.  Until ``exp.run()`` is called, ``trial`` will not have a value. The next line defines a **Label** state that displays text for a duration. By default, it displays in the middle of the experiment window. Notice that ``trial.current``. In order to access the numbers from our random list, we need to use ``trial.current`` instead of words[x]. ``trial.current`` is a way to tell smile to access the *current* member of the ``words`` list while looping.

.. warning::
    Do not try and access or test the value of trial.current. As it is a reference variable, you will not be able to test the value of it outside of a smile state.  

The final version of **randWord1.py**
::
    from smile import *
    import random
    
    words = ['plank','dear','thopter','initial','pull','complicated','assertain','biggest']
    random.shuffle(words)	

    #Needed Parameters of the Experiment
    interStimulusDuration=1
    stimulusDuration=2

    #We are ready to start building the Epxeriment!
    exp = Experiment()
    with Loop(words) as trial:
        Label(text=trial.current, duration=stimulusDuration)
        Wait(interStimulusDuration)

    exp.run()

And Now, With user Input!
=========================

The final step for our basic smile tutorial is to add user input and loggin.  Lets define the experiment. Lets say we need to ask the participant to press J if the number of letters on the screen is even, and K if the number letters in the word on the screen is odd. We have to say that the participants have only 4 seconds to answer. In this tutorial I will show you how we can setup our experiment so that when they press a key to answer, the stimulus will drop off the screen and start the next iteration of the loop.  

This tutorial will also teach you how to compare **trial.current** comparisons. Create a directory called NumberRemember and create a file within the directory called randWord2.py. First, we will bring over the word list from the previous file.  We are going to change it a little bit to make sure that the experiment will be able to tell what key is the correct key for each trial.  
::
    words = ['plank','dear','thopter','initial','pull','complicated','assertain','biggest']
    temp = []
    for i in range(len(words)):
        condition = len(words[i])%2
        temp.append({'stimulus':words[i], 'condition':condition})
    words = temp
    words.shuffle()	
    ...

Our list of words is now a list of dictionaries, where ``words[x]['stimulus']`` will give us the word and ``words[x]['condtion']`` will give us weather the words has an even or an odd length. Like in the last example, the next thing we must do is initialize all of our experiment parameters.
::
    #Needed Parameters of the Experiment
    interStimulusDuration=1
    maxResponseTime=4
    keys = ['J','K']

    #We are ready to start building the Epxeriment!
    exp = Experiment()
    ...

This only got changed a little; we changed the line ``stimulusDuration=2`` into ``maxResponseTime=4`` and we added a line about the **keys** that our participant will be pressing.  Next we are going to setup up our basic loop. We will start with the loop from the last example and work from there. 
::
    with Loop(words) as trial:
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
    with Loop(words) as trial:
        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=keys)
        Wait(interStimulusDuration)

    exp.run()	 

This displays the current trial's number until you press a key then waits the inter-stimulus duration that we set earlier.  This isn't exactly what we want, but it is the start we need to fully understand what we are doing. Next we are going to edit ``kp = KeyPress(keys=keys)`` to include our response time duration. We also need to add in the ability to check and see if they answered correct. This will use the **Ref** class. ``Ref.getitem()`` allows us to use a reference to a number in **trial.current** as the index of the list of keys **keys**
::
    ...
    with Loop(words) as trial:
        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=keys, duration=maxResponseTime, correct_keys=Ref.getitem(keys,trial.current['conditionn']))
        Wait(interStimulusDuration)

    exp.run()
  
The Last thing we need to add to this experiment, at the end of the ``Loop()``, is the **Log**. Log is pretty simple. Where ever you put it in the exepriment, it will run the Log state and will save out a **.csv** file to a folder called **data** in your experiment directory under whatever name you put in the *name* field. 
::
    ...
    Log('name':'Loop',
        'correct':kp.correct,
        'time_to_respond':kp.rp
        ) 
    ...	

With this line, each iteration of the loop in the experiment will save our a line into **Loop.csv** all of the values defined in the ``Log()`` call. The loop will look like this
::
    ...
    with Loop(words) as trial:
        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=keys, duration=maxResponseTime, correct_keys=Ref.getitem(keys,trial.current['conditionn']))
        Wait(interStimulusDuration)
        Log('name':'Loop',
            'correct':kp.correct,
            'time_to_respond':kp.rp
            ) 
    

The final version of **randWord2.py**
::
    from smile import *
    import random
    words = ['plank','dear','thopter','initial','pull','complicated','assertain','biggest']
    temp = []
    for i in range(len(words)):
        condition = len(words[i])%2
        temp.append({'stimulus':words[i], 'condition':condition})
    words = temp
    random.shuffle(words)	

    #Needed Parameters of the Experiment
    interStimulusDuration=1
    maxResponseTime=4
    keys = ['J','K']
    #We are ready to start building the Epxeriment!
    exp = Experiment()

    with Loop(words) as trial:
        Label(text=trial.current['stimulus'])
        with UntilDone():
            kp = KeyPress(keys=keys, duration=maxResponseTime, correct_resp=Ref.getitem(keys,trial.current['condition']))
        Wait(interStimulusDuration)
        Log(name='Loop',
               correct=kp.correct,
               time_to_respond=kp.rt) 
        Wait(interStimulusDuration)
    exp.run()


Now you are ready to get Smiling!


Special Examples
=============================

This section is designed to help you figure out how to use some of the more advnaced states and interesting interactions with some of the states in smile.  We will be going over how to use the *ButtonPress* state, the ** state, and how to define your own *Subrutine* state! 

Subroutine
-----------------------------

This is the tutorial that will teach you how to write your own *Subroutine* state and highlight its importance.  In smile, a *Subroutine* state is used to compartimentalize a block of states that you are bound to use over and over again in different experiments. The one I am going to highlight is a list presentation subroutine. 

Lets create a new directory called **ListPresentTest** and then create a new file in that directory called **listpresent.py**.  The first thing we need to do for our list presentation subroutine is setup the basic imports and define our subroutine. 
::
    from smile import *
    from smile.state import Subroutine
    
    @Subroutine
    def ListPresent(self, listOfWords=[], interStimDur=.5, onStimDur=1, fixation=True, fixDur=1, interOrientDur=.2):
        
    ...

By placeing `@Subroutine` above our subroutine definition, we tell the compiler to treat this as -a smile *Subroutine*. The subroutine will eventually present a fixation cross, wait, present the stimulus, wait again, and then repeat for all of the list items you pass it. Just like calling a function or declaring a state, we will call `ListPresent` in the body of our experiment and pass in those variables in **mainListPresent.py**, which we will create later. 

.. warning::
    Always have *self* as the first argument when defining a subroutine. If you don't your code will not work as intended. 

The cool thing about *Subroutines* is that you can access any of the variables that you declare into `self` outside of the subroutine, so the first thing we are going to do is add a few of these to our subroutine.
::
    ...
    
    @Subroutine
    def ListPresent(self, listOfWords=[], interStimDur=.5, onStimDur=1, fixation=True, fixDur=1, interOrientDur=.2):
        self.timing = []
    
    ...

The only variable we will need for testing later is an element to hold all of our timing information to pass out into the experiment. Next lets add the stimulus loop.
::
    ...
    @Subroutine
    def ListPresent(self, listOfWords=[], interStimDur=.5, onStimDur=1, fixDur=1, interOrientDur=.2):
        self.timing = []
        with Loop(listOfThings) as trial:
            fix = Label(text='+' duration=fixDur)
            oriWait = Wait(interOrientDur)
            stim = Label(text=trial.current, duration=onStimDur)
            stimWait(interStimDur)
            self.timing += [Ref(dict,
                                   fix_dur=fix.duration,
                                   oriWait_dur=oriWait.duration,
                                   stim_dur=stim.duration,
                                   stimWait_dur=stimWait.duration)]
    
From here, we have a finished subroutine! We now have to write the **mainListPresent.py**. We just need to generate a list of words and pass it into our new subroutine. 

Below is the finished **mainListPresent.py**
::
    from smile import *
    from listpresent import ListPresent
    import random
    
    WORDS_TO_DISPLAY = ['The', 'Boredom', 'Is', 'The', 'Reason', 'I', 'started', 'Swimming', 'It\'s', 'Also', 'The', 'Reason', 'I','Started', 'Sinking','Questions','Dodge','Dip','Around','Breath','Hold']	
    INTER_STIM_DUR = .5
    STIM_DUR = 1
    INTER_ORIENT_DUR = .2
    ORIENT_DUR = 1
    random.shuffle(WORDS_TO_DISPLAY)
    exp = Experiment()
    
    lp = ListPresent(listOfWords=WORDS_TO_DISPLAY, interStimDur=INTER_STIM_DUR, onStimDur=STIM_DUR, fixDur=ORIENT_DUR, interOrientDur=INTER_ORIENT_DUR)
    Log(name='LISTPRESENTLOG',
        timing=lp.timing)
    exp.run()
    

Below is the finished **listpresent.py**
::
    from smile import *
    from smile.state import Subroutine
    @Subroutine
    def ListPresent(self, listOfWords=[], interStimDur=.5, onStimDur=1, fixDur=1, interOrientDur=.2):
        self.timing = []
        with Loop(listOfWords) as trial:
            fix = Label(text='+', duration=fixDur)
            oriWait = Wait(interOrientDur)
            stim = Label(text=trial.current, duration=onStimDur)
            stimWait = Wait(interStimDur)
            self.timing += [Ref(dict,
                                fix_dur=fix.duration,
                                oriWait_dur=oriWait.duration,
                                stim_dur=stim.duration,
                                stimWait_dur=stimWait.duration)]
        
    
    
    
    
ButtonPress
-----------------------------

This is an example to teach you how to use the state *ButtonPress* and how to use the *MouseCursor* state. This is a simple experiment that allows you to click a button on the screen and then tells you if you chose the correct button. 

An important thing to notice about this code is that *ButtonPress* acts as a *Parellel* state. This means that all of the states defined within *ButtonPress* become its children. The field *correct* that you pass into your *ButtonPress* takes the *name* of the correct button for the participant as a string. 

When defining your *Buttons* within your button press, you should set the *name* attribute of each to something different.  That way, when reviewing the data you get at the end of the experiment, you are able to easily distinguish which button the participant pressed. 

Another things that is important to understand about this code is the *MouseCursor* state.  By default, the experiment hides the mouse cursor. In order to allow your participant to see where they are clicking, you must include a *MouseCursor* state in your *ButtonPress* state. If you ever feel that your participant needs to use the mouse for the duration of an experiment, you are able to call the *MouseCursor* state just after you assign your *Experiment* variable.  

The final version of **buttonPressExample.py**
::
    from smile import *
    
    exp = Experiment()
    
    #From here you can see setup for a ButtonPress state.
    with ButtonPress(correct='left', duration=5) as bp:
        MouseCursor()
        Button(name='left', text='left', left = exp.screen.left, bottom=exp.screen.bottom)
        Button(name='right', text='right', right = exp.screen.right, bottom=exp.screen.bottom)
        Label(text='PRESS THE LEFT BUTTON FOR A CORRECT ANSWER!')
    Wait(.2)
    with If(bp.correct):
        Label(text='YOU PICKED CORRECT',color='GREEN',duration=1)
    with Else():
        Label(text='YOU WERE DEAD WRONG',color='RED',duration=1)
    exp.run()
    
    
