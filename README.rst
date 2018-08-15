======
Smile
======
-----------------------------------------------
State Machine Interface Library for Experiments
-----------------------------------------------

Overview
========

Writing experiments should be simple, the library should be small, and
it should make you happy.

Prepare to Smile...


Dependencies
============

- `python <https://www.python.org/>`_ (version 2.7 or 3)
- `kivy <http://www.kivy.org/>`_ (version 1.8 or 1.9)
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

For more information visit `Mass Communicating <https://mass-communicating.com/code/2013/11/08/python-versions.html>`_


Documentation
=============

For detailed documentation, please visit http://smile-docs.readthedocs.io/
