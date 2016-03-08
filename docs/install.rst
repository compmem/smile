============================
Installation of SMILE!
============================

Getting ready to SMILE? Then you are in the right place. This guide will tell
you how to install SMILE and the package that SMILE is dependant upon, Kivy!
Scroll down to the appropriate operating system and follow the directions provided
to install Kivy, SMILE, and any needed extra packages.

Installing SMILE on Windows
===========================


Before you attempt to do anything, the first step should be installing
Anaconda. Anaconda is a python distribution that contains scientific python
packages such as numpy or matplotlib. If you already have python installed,
Anaconda will install all of it's scientific packages to that distribution.
Below is a link to the Anaconda install page. Make sure to download the 32 bit
distribution of Anaconda, and the 2.7 version of python. Install it, and make
sure both check boxes are checked when installing. These check boxes will
register Anaconda as the default python of your system. Advanced users who don't
want Anaconda to be their default python will want to uncheck the bottom
check-box.

    -`Anaconda Download Page <https://www.continuum.io/downloads>`_

The next thing you need to download and install is *Kivy*. Anaconda allows you
to install Kivy and its dependencies with ease. The first thing you are going to
do is open up your Anaconda 32bit command prompt and run the following line to
install Kivy's dependencies.

.. note:

    Run the following as one line in your command prompt

::

    > pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew kivy.deps.gstreamer --extra-index-url https://kivy.org/downloads/packages/simple/

Then, run the following command in your Anaconda 32bit command prompt to install
Kivy to the Anaconda python.

::

    > pip install kivy

After running the last command, it is now time to download SMILE. Download
SMILE from the github link provided and then extract it.

    -`SMILE Download <https://github.com/compmem/smile/tree/master>`_

Now, in your Anaconda command-prompt, navigate to the newly extracted smile download
folder that contains setup.py and run the following line.

::

    > pip install .

The final thing you need to install to gain access to all of SMILE's
functionallity is PYO. PYO is used to play and record sound with SMILE. Download
and install the windows version of PYO from their website. The link is provided
below.

    -`PYO Download <http://ajaxsoundstudio.com/software/pyo/>`_

.. note:

    When PYO asks for a directory to install to, choose `C:\Python27`. If that
    folder doesn't already exist, create it and then attempt to install PYO into
    that folder

With that, you are finished installing SMILE. Congrats! Head over to
`SMILE Tutorial<tutorial.html>`_ to start SMILING.

Windows Troubleshooting
-----------------------

*If you are trying to replace an older version of SMILE*, or if you just need
to upgrade your currect version, you must run the following command while the
Anaconda command promt is in the SMILE download folder.

::

    > pip install . --upgrade


Installing SMILE on Mac
=======================

The first step is to download and install kivy. The following link will take you
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
functionallity is PYO. Download and install the Mac version of PYO from their
website. The link is provided below.

    -`PYO Download <http://ajaxsoundstudio.com/software/pyo/>`_

With that, you are finished installing SMILE. Congrats! Head over to
`SMILE Tutorial<tutorial.html>`_ to start SMILING.

Mac Troubleshooting
-------------------

*If you are trying to replace an older version of SMILE*, or if you just need
to upgrade your currect version, you must run the following command while the
Anaconda command promt is in the SMILE download folder.

::

    $ kivy -m pip install . --upgrade


Installing SMILE with Linux
===========================

SMILE requires Kivy to run properly, but if you would like to use the
smile.sound functionallity, you need to download and install PYO aswell. Run
the following in your command line to install both Kivy and PYO at the same
time.

::

    $ sudo aptitude install python-pyo python-kivy

Then, download SMILE from github and extract it to a place you can find later.
The download link is the following:

    -`SMILE Download <https://github.com/compmem/smile/tree/kivy>`_

Next, navigate to the newly extracted smile folder that contains setup.py, and
run the following line in your terminal window.

::

    $ python -m pip install .

This will add SMILE to your python distribuiton.

With that, you are finished installing SMILE. Congrats! Head over to
`SMILE Tutorial<tutorial.html>`_ to start SMILING.

Linux Troubleshooting
---------------------

To be added when problems are found.
