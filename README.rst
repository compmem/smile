======
SMILE
======
-----------------------------------------------
State Machine Interface Library for Experiments
-----------------------------------------------

Overview
========

Writing experiments should be simple, the library should be small, and
it should make you happy.

Prepare to SMILE...

Installing SMILE
================

First you need Kivy, which is the primary dependency of SMILE
Sometimes kivy has conflicts with some other packages, so we create a new virtual environment for working with SMILE:

::

    conda create -n smile    
    conda activate smile

Now we can install kivy:

::

    conda install -c conda-forge kivy


If you plan on running SMILE from within Jupyter Notebook (only suggested for development and not data collection), you'll need to install that, too:

::
    
    conda install notebook


Then you can install SMILE right from the GitHub repository:

::
    
    pip install --upgrade git+https://github.com/compmem/smile


All together...

::

    conda create -n smile    
    conda activate smile
    conda install -c conda-forge kivy
    pip install --upgrade git+https://github.com/compmem/smile



Dependencies
============

- `python <https://www.python.org/>`_ (version 3)
- `kivy <http://www.kivy.org/>`_ (version >= 1.8)
- `pyo <http://ajaxsoundstudio.com/software/pyo/>`_ (optional, for audio)


For versioning
==============

::

    git config filter.versioning.smudge 'python versioning.py'
    git config filter.versioning.clean  'python versioning.py --clean'

Add a file to .git called post-checkout with the following.

::

    #!/bin/sh
    cat version.py | python versioning.py --clean | python versioning.py > version.py

For more information visit `Mass Communicating via the Wayback Machine<https://web.archive.org/web/20180823042433/https://mass-communicating.com/code/2013/11/08/python-versions.html>`_


Documentation
=============

For detailed documentation, please visit http://smile-docs.readthedocs.io/

