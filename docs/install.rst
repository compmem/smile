============================
Installation of SMILE!
============================

Getting ready to SMILE? Then you are in the right place. This guide will tell
you how to install SMILE and the package that SMILE is dependent upon, Kivy!
Scroll down to the appropriate operating system and follow the directions
provided to install Kivy, SMILE, and any extra needed packages.

Installing SMILE on Windows
===========================

Before installing anything, make sure that you have python installed and that
you can run python through your command prompt.

Also, it is important to have pip installed to your python. Without pip
you will not be able to run the commands needed to install SMILE. To install
*pip*, click the link below and follow the instructions.

    -`Get pip <https://pip.pypa.io/en/stable/installing/>`_


The next thing you need to install after *pip* is *kivy*. *Kivy* is the display
backend for SMILE. Note that you do not need to know anything about how to use
kivy to figure out how to use SMILE.

To install kivy on your windows machine, run the following line in your command
prompt.

::

    > python -m pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew
    > python -m pip install kivy.deps.gstreamer --extra-index-url https://kivy.org/downloads/packages/simple/

Then run this line in your command prompt.

::

    > python -m pip install kivy

.. note::

    If you run into any trouble installing kivy onto your windows machine, please check the kivy website for more detailed instructions.


After running the last command, it is now time to download SMILE. Download
SMILE from the github link provided and then extract it.

    -`SMILE Download <https://github.com/compmem/smile/tree/master>`_

Now, in your command prompt, navigate to the newly extracted smile download
folder that contains setup.py and run the following line.

::

    > python -m pip install .

The final thing you need to install to gain access to all of SMILE's
functionality is PYO. PYO is used to play and record sound with SMILE. Download
and install the windows version of PYO from their website. The link is provided
below.

    -`PYO Download <http://ajaxsoundstudio.com/software/pyo/>`_

.. note::

    When PYO asks for a directory to install to, choose `C:\Python27`. If that folder doesn't already exist, create it and then attempt to install PYO into that folder

With that, you are finished installing SMILE. Congrats! Head over to
:ref:`The SMILE Tutorial <smile_tutorial>` to start SMILING. This will cover a more
advance look into how SMILE works.

Sync Pulsing on Windows
-----------------------

To use sync pulsing on windows via the parallel port, you must install
**Inpout32**, or include *inpout32.dll* in the same folder as your experiment.

Windows Troubleshooting
-----------------------

*If you are trying to replace an older version of SMILE*, or if you just need
to upgrade your current version, you must run the following command while the
Anaconda command prompt is in the SMILE download folder.

::

    > pip install . --upgrade

*If you would like to use any of the audio options of SMILE*, pyo is required. If
you find that you can't install pyo, it is because you are not using the 32 bit
version of Python. You can install SMILE on 64 versions of Python, but you will
lose the ability to play sound files. Your ability to play sound while
presenting a **video** file, however, will not be inhibited.

*If you are trying to install SMILE to an Anaconda distribution of python*, you
must use 64 bit. We have found that the 32 bit version of GStreamer that
Anaconda provides will not work well with Kivy, and will error out. Please use
the 64 bit version of Anaconda if you choose to install SMILE to it.

*If you are installing SMILE to a Python separate from Anaconda, but still have*
*Anaconda installed on that machine*, you may encounter a weird pathing error.
We are still looking into what causes it, and it doesn't happen to everyone, but
we would still like you to be aware that you may run into some problems.

Installing SMILE on Mac
=======================

The first step is to download and install Kivy. The following link will take you
to the Mac-Kivy install guide.

    -`Mac-Kivy Install Guide <http://kivy.org/docs/installation/installation-macosx.html>`_

After you install Kivy, you must download and install SMILE. The following is a
link to the SMILE download page, where you will download the zip, and extract
it to an easy to find place.

    -`SMILE Download <https://github.com/compmem/smile/tree/master>`_

Now, all you have to do is open the terminal and navigate to the
newly extracted smile download folder. This folder should contain setup.py. Run
the following line to install SMILE to your special Kivy distribution of python.

::

    $ kivy -m pip install .

Easy. SMILE should have installed without any issue.

The final thing you need to install to gain access to all of SMILE's
functionality is PYO. Download and install the Mac version of PYO from their
website. The link is provided below.

    -`PYO Download <http://ajaxsoundstudio.com/software/pyo/>`_

With that, you are finished installing SMILE. Congrats! Head over to
:ref:`The SMILE Tutorial <smile_tutorial>` to start SMILING. This will cover a more
advance look into how SMILE works.

Mac Troubleshooting
-------------------

*If you are trying to replace an older version of SMILE*, or if you just need
to upgrade your current version, you must run the following command while the
Anaconda command prompt is in the SMILE download folder.

::

    $ kivy -m pip install . --upgrade

*If you require any additional packages to run your experiment*, you must use
**kivy** to install them. Like above, you use the *kivy -m pip install* line to
install any additional packages to the python that is linked to kivy.

Installing SMILE with Linux
===========================

SMILE requires Kivy to run properly, but if you would like to use the
smile.sound functionality, you need to download and install PYO as well. Run
the following in your command line to install both Kivy and PYO at the same
time.

::

    $ sudo aptitude install python-pyo python-kivy

If you are running something besides a Debian based linux system, the above line
will look different. It depends on your prefered package manager.

Then, download SMILE from github and extract it to a place you can find later.
The download link is the following:

    -`SMILE Download <https://github.com/compmem/smile/tree/kivy>`_

Next, navigate to the newly extracted smile folder that contains setup.py, and
run the following line in your terminal window.

::

    $ python -m pip install .

This will add SMILE to your python distribution.

With that, you are finished installing SMILE. Congrats! Head over to
:ref:`The SMILE Tutorial <smile_tutorial>` to start SMILING. This will cover a more
advance look into how SMILE works.

Sync pulsing on Linux
---------------------

To use sync pulsing on linux over a parallel port, you must install
`PyParallel <https://github.com/pyparallel/pyparallel/>`_. Install it via *pip*
or your favorite package manager.

Linux Troubleshooting
---------------------

To be added when problems are found.
