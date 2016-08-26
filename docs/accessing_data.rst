=============================
Data accessing and Processing
=============================

Saving your Data into SLOG Files
================================

In SMILE, each state will produce what is called a *.slog* file by default.
This file is a specially compressed file composed of all the important data
associated with the state.  It not only logs every parameter, but also
all of the variables listed in the *Logged Attributes* section of the
docstrings. In most cases, every state will save out 2 rows of data to the
*.slog* file.  The first row is the field names, and the second row will be the
data for each of those fields.

The kind of state that write multiple lines out to its associated *.slog* file
is the :py:class:`~smile.state.Log` state.  Wherever the class is inserted into the experiment, the class will log the
values of all of the keywords/argument pairs it is passed.  If the *Log*
exists within a loop, it will write out the values of the keyword/argument
pairs during each iteration of the loop during experimental runtime.  In this
case, the *.slog* file will have the first row be the keywords, and the
subsequent rows be all of the data for each *Log* during each iteration of the
loop.

.. note::

    Every instance of the Log state in the experiment will save to a separate
    file.

Below is an example of a *Log* state.

.. code-block:: python

    with Loop(10) as trial:
        lb = Label(text=trial.i, duration=2)
        Log(trial.current,
            name="looping_log",
            label_appear_time=lb.appear_time['time'])

This example will save 11 rows into a *.slog* file. If **trial.current** is the
first argument for *Log*, then it will save out all of the information about
the looping variable out in different columns.

A Record state will record all of the references given.  It will write a line
to the *.slog* file every time one of the references changes. It will also log
the time at which the given reference changed.

Reading your SLOG files in python
=================================

In order to slog through data, one of two things are first needed to be completed.
The first is to pull the data into python by using the :py:class:`~smile.state.Log`
method called :py:func:`~smile.state.log2dl`. This method converts the *.slog* file to a
list of dictionaries so that you can perform any pythonic functions on it in
order to analyze the data. *log2dl* has one required parameter,
*log_filename*, which should be a string that starts out *log_* and ends with
a user chosen *name* parameter of the *Log* in the user's experiment.

If there are multiple files with the same name, they have trailing *_#* in the
filename. *log2dl* will pull all of the files with the same base name, and
concatenate them into a single list of dictionaries.

The other way data can be access is by converting all of the *.slog* files
to *.csv* files. This can be accomplished by running the :py:func:`~smile.log.Log2csv`
method. This method will take two parameters, *log_filename* and *csv_filename*.
*log_filename* works the same way as in *log2dl*, where a string that is *log_*
plus the name which was provided in the *name* parameter of the *Log* is passed.
If no *csv_filename* is given, then it will be saved as the same name as the
*log_filename* plus *.csv*. From there, one can use their preferred method of
data analysis.
