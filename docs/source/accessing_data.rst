

Accessing your Data from SLOG Files
===================================

In SMILE, each state in your experiment will produce a **.slog** file.  This file uses a special compression that keeps all of the saved data small.  By default, each state will save out all of the important information about itself. 

The *Log* state will save out any information you think might be critical to analysis later. See *Log* for an example on how to use it. 

To access the **.slog** data easily, we created an object called *Log_Reader* to help you read out **.slog** files line by line.  You are also able to access the files column names.

Example
-------

::

    fn = 'log_file.slog'
    lr = Log_Reader(file_name=fn)
    column_names = lr.