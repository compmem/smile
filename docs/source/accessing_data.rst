

Saving your Data into SLOG Files
================================

In SMILE, each state will produce what is called a **.slog** file by default.  This file is a specially compressed file filled with all of the important data associated with the state.  It logs not only all of the parameters, but also all of the variables listed in the *Logged Attributes* section of the docstrings. In most cases, every state will save out 2 rows of data to the **.slog** file.  The first row is the field names and the second row will the the data for each of those fields. 

The kind of state that writes multiple lines out to its associated **.slog** file is the *Log* state.  Wherever you put it into your experiment, it will log the values of all of the keywords/argument pairs you pass into it.  It your *Log* exists within a loop, it will write out the values of the keyword/argument pairs during each iteration of the loop during experimental runtime.  In this case, the **.slog** file will have the first row be the keywords, and the subsequent rows be all of the data for each *Log* during each iteration of the loop.  

.. note::

    Every instance of the Log state in your experiment will save to a seperate file. 

Below is an example of a *Log* state.

::

    with Loop(10) as trial:
        lb = Label(text=trial.i, duration=2)
        Log(trial.current,
            name="looping_log",
            label_appear_time=lb.appear_time['time'])
          
This example will save 11 rows into a **.slog** file. If ``trial.current`` is the first argument for *Log*, then it will save out all of the information about your looping variable out in different columns. 

A Record state will record all of the references given.  It will write a line to the **.slog** file everytime one of the references changes. It will also log the time at which the given reference changed. 

Reading your SLOG files in python
=================================

In order to use the data that your experiment has collected, you have to either use ``-c`` in the command line when running your experiment to save out a **.csv** file along with all of the **.slog** files, or you have to open **.slog** files with our *Log_Reader* class.

A *Log_Reader* is the class we use to efficiently read out the **.slog** file into python. *Log_Reader* takes a sting filename as a parameter, has an important function, and an important property. The property is ``.field_names``.  This returns a list of strings that are the names of all of the columns. The function is ``.read_record()``.  This will the next row in the **.slog** file, and return a dictionary with the keys being the field names. If the next row is blank or returns EOF, then it will return None.

Below is an example of using *Log_Reader*. 

::

    lr = Log_Reader(filename='/data/logged_file.slog')
    temp = Log_Reader.read_record()
    While(temp != None):
        print temp

This will print out every dictionary that *read_record()* will produce.  

