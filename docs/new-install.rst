============================
Installation of SMILE!
============================


Requirements
============

- SMILE Downloaded from GitHub: `SMILE Download <https://github.com/compmem/smile/master>`_
- Python 3.7 to Python 3.10

Use ``python3 --version`` (or ``python --version`` depending on your setup) in the terminal or Command Prompt to check your Python version & upgrade if necessary.


Base Installation
=================

1. Navigate to the directory where you downloaded SMILE and extract the contents if necessary.

2. In the terminal (or Command Prompt on Windows), navigate to the parent directory of the SMILE project.

3. To keep a clean work environment, create a `virtual environment <https://docs.python.org/3/library/venv.html>`_ for your SMILE work:

    a. On Windows, MacOS, & Linux:
    
    ::

        python3 -m venv .smile_venv

4. Activate the virtual environment:

    a. On MacOS & Linux: 
    
    ::

        $ source .smile_venv/bin/activate

    b. On Windows: 
    
    ::

        > .smile_venv\Scripts\activate

5. In the terminal, navigate to the SMILE project directory where the `pyproject.toml` file is located.

    - SMILE uses a `pyproject.toml <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>`_ file to specify requirements & dependencies for packaging SMILE.

6. Install SMILE on Windows, MacOS, & Linux: 

::

    python3 -m pip install .


Audio Requirements Installation
===============================

SMILE uses `PYO <https://github.com/belangeo/pyo>`_ to enable the `smile.sound` audio functionality. 
The current latest version of PYO is 1.0.5, which is compatible with up Python 3.11 on Windows & MacOS, and up to Python 3.10 on Linux.
Check your Python version, ``python3 --version``, and adjust the version you're using as needed.
`Pyenv <https://github.com/pyenv/pyenv>`_ can be a helpful tool for switching between Python versions on the same machine.

Once the correct Python version is in use, the below will install SMILE + Kivy + PYO on MacOS, Windows, & Linux
run the following from the terminal in the SMILE project directory containing the pyproject.toml file:

::

    python3 -m pip install .[pyo]

To only install PYO:

::

    python3 -m pip install pyo


Sync Pulsing Requirements Installation
======================================

Linux
-----

SMILE uses `pyparallel <https://github.com/pyserial/pyparallel>`_ to do sync pulsing over a parallel port on Linux.
To install SMILE + Kivy + pyparallel on MacOS, Windows, & Linux run the following from the terminal in the SMILE project
directory containing the pyproject.toml file:

::

    python3 -m pip install .[pyparallel]

To only install pyparallel:

::

    python3 -m pip install pyparallel

Windows
-------

To use sync pulsing on windows via the parallel port, you must install
`InpOut32 <https://www.highrez.co.uk/Downloads/InpOut32/>`_, or include *inpout32.dll* in the same folder as your experiment.

MacOS
-----

We are still exploring solutions for sync pulsing over a parallel port on MacOS. 
Please feel free to fork & issue a pull request to contribute.


Full Install
============

To install SMILE & optional dependencies for audio functionality & sync pulsing on Linux,
run the following from the terminal in the directory containing the pyproject.toml file:

::

    $ python3 -m pip install .[full]


Next Steps
==========

With SMILE successfully installed, head over to
:ref:`The SMILE Tutorial <smile_tutorial>`_ to start SMILING. The tutorial provides a more
advanced look into how SMILE works & how to use it.