============================
Installation of SMILE!
============================


Requirements
============

- Python >=3.7 (upper bound Python version restrictions explained in the "If Using Audio" section below)

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

    a. On MacOS, Linux, & Windows Git Bash: 
    
    ::

        $ source .smile_venv/bin/activate

    b. On Windows: 
    
    ::

        > .smile_venv\Scripts\activate

5. Install SMILE on Windows, MacOS, & Linux: 

::

    python3 -m pip install 'smile @ git+https://github.com/compmem/smile.git@master'

**Note:** The above is the base installation of smile. Instructions for optional dependencies required for audio and sync pulsing functionalities are below.


If Using Audio
==============

SMILE uses `PYO <https://github.com/belangeo/pyo>`_ to enable the `smile.sound` audio functionality. 
The current latest version of PYO is 1.0.5, which is compatible with up Python 3.11 on Windows & MacOS, and up to Python 3.10 on Linux.
Check your Python version, ``python3 --version``, and adjust the version you're using as needed.
`Pyenv <https://github.com/pyenv/pyenv>`_ can be a helpful tool for switching between Python versions on the same machine.

Once the correct Python version is in use, the below will install SMILE + SMILE's base requirements + PYO on MacOS, Windows, & Linux
run the following from the terminal with the virtual environment activated:

::

    python3 -m pip install 'smile[pyo] @ git+https://github.com/compmem/smile.git@master'

To only install PYO, relevant if you already did the above base install and now need to add on PYO for audio functionality:

::

    python3 -m pip install pyo

If Using Sync Pulsing
=====================

Linux
-----

SMILE uses `pyparallel <https://github.com/pyserial/pyparallel>`_ to do sync pulsing over a parallel port on Linux.
To install SMILE + SMILE's base requirements + pyparallel on MacOS, Windows, & Linux run the following from the terminal with the virtual environment activated:

::

    python3 -m pip install 'smile[pyparallel] @ git+https://github.com/compmem/smile.git@master'

To only install pyparallel, relevant if you already did the above base install and now need to add on pyparallel for sync pulsing functionality:

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

To install SMILE & optional dependencies for audio functionality & sync pulsing on Linux (not relevant on MacOS and Windows due to further needs to enable sync pulsing), run the following from the terminal with the virtual environment activated:

::

    $ python3 -m pip install 'smile[full] @ git+https://github.com/compmem/smile.git@master'


Next Steps
==========

With SMILE successfully installed, head over to
:ref:`The SMILE Tutorial <smile_tutorial>`_ to start SMILING. The tutorial provides a more
advanced look into how SMILE works & how to use it.