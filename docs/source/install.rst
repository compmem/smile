============================
Installation of Smile!
============================

:Author: Brandon Jacques <beegjacques@yahoo.com>
:Date: 2015-10-13 
:Revision: 2.0.0
:Description: This is the step by step guide to installing smile on various platforms

Getting ready to SMILE? Then you are in the correct place. This guide will tell you how to install SMILE and the package that SMILE is dependant on, Kivy! To start out, we will install Kivy

Kivy Install
----------------------------

The first thing to look at is what O.S. you are running.  On all 3 major systems you are able to install kivy with no problem into your default python build. If you are running Windows, however, there is a portable version of Kivy that includes all of the dependencies so you don't have to go hunting around for the correct version that works on your machine. Below are a list of links to the appropriate Kivy install tutorial for your O.S. Veiw the General Installation guide

    -`General Installation Guide <http://kivy.org/docs/installation/installation.html>`_

    -`Windows Portable Install <http://kivy.org/docs/installation/installation-windows.html>`_

    -`OSX App Install <http://kivy.org/docs/installation/installation-macosx.html>`_

    -`Linux Packages Install <http://kivy.org/docs/installation/installation-linux.html>`_

.. warning::

    Smile Requires Kivy 1.8 or 1.9 to work properly.  
    
.. warning::
    
    If you are installing on Mac, please download and install Continume Anaconda first.
    It allows for you to have an easy to use package manager for python and it comes 
    with a code editor. 

Next we shall download and install smile.

SMILE Install
------------------------------

Pretty simple stuff here. Download the smile package from github `here <https://github.com/compmem/smile/tree/kivy>`_. Extract the Zip file downloaded from github, then navigate to newly extracted folder and run setup.py. 

Youll have to do different things depending on the platform you are running on. The instructions are detailed below.


If you are running on Windows and installed Portable Kivy
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
First, find the path to the portable kivy's python. It is inside your portable kivy folder in a folder called *Python27*.  Then, in your command prompt, navigate to the downloaded *smile-kivy* folder. While inside this folder run the following Command. 

::

    >C:\path\to\kivy\kivy-2.7 -m pip install -e C:\path\to\smile\ .
    
This installs smile to the portable version of kivy. This is important so you don't have to copy smile into every experiment directory you code. 

To run a smile experiment, first navigate to the folder kivy folder in a command prompt.  Inside this folder, you are able to call `kivy-2.7` and send whatever experiment you want to it. Below is an example

::

    >kivy-2.7 <path to smile experiment> [options]

If you would like to call kivy from your command line like you would call python, and run any experiment from the directory it is located in, you must run the following line to add kivy to your build *PATH*. `C:\Path\To\Kivy` is just the path to wherever you saved the portable kivy folder.

::

    >setx PATH "%PATH%;C:\Path\To\Kivy"

.. warning::
    If you don't type this line correctly, or if you don't add the right path to kivy, you could risk damaging your computer. Use this powerful command at your own risk. 
    
If you did this, you are able to run **kivy-2.7** from any folder, that way you can just run `>kivy-2.7 experiment_name.py` in the directory your experiment is in, where **experiment_name.py** is replaced with what you called your experiment.

::

    >kivy-2.7 experiment_name.py [options]
    
For the different command line options, refer to `Running Smile<runningsmile.html>`_.    

If you are running on Mac and you setup the kivy command line option
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

For those of you who installed on Mac, you should have added kivy.app to your applications folder and ran the makesysmlinks program that added a kivy command to your terminal. Since the Mac version of Kivy uses the default python distribution on your machine, all you have to do is run *setup.py* in python and it will install smile to your machine. Then, all you have to do to run any smile experiment on mac is use the `kivy` command followed by the pathname of the experiment and whatever options you want to add.

Navigate to the extracted smile download folder in your terminal, or if you are using **Anaconda** you should use the *Anaconda Termial*, and run the following command.

::

    $kivy -m pip install .

This will install smile to whatever python directory Kivy is using on your machine. Then to run an exeriment, navigate to wherever your smile experiment is saved run the next line, where **experiment_name.py** is replaced with what you called your experiment.

::

    $kivy exerpiment_name.py [options]

For the different command line options, refer to `Running Smile<runningsmile.html>`_.    

If you are running Linux and installed Kivy via apt-get or pip
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

If you installed Kivy via *aptitude* then you are able to just install smile via the pip command. Navigate to the smile download folder and run the following line in your command prompt. 

::

    $pip install .
    
    
Then to run a smile experiment, navigate to where your smile experiment is saved and run the next line, where **experiment_name.py** is replaced with what you called your experiment.

::

    $python experiment_name.py [options]

For the different command line options, refer to `Running Smile<runningsmile.html>`_.    

Verification Step
-----------------

Please verify now that you have installed kivy and smile correctly by running *video.py* in the */smile/* folder inside your smile download folder. 

If the program finishes without error, then you have installed correctly! Congrats! Move onto the `Smile Tutorial<tutorial.html>`_ to teach you smiling basics.

Installing PYO for smile.sound
------------------------------

If you would like to use smile's sound functionallity you need to download PYO onto your machine. 

On Windows and Mac, just follow the following link and download the version for your OS

On Linux, run the following line to install pyo to your machine. 

::

    sudo aptitude install python-pyo

With PYO installed you are able to call **Beep** and **SoundFile** in your experiments.

.. note:
    
    You must import smile.sound by hand at the top of your experiment. You cannot `from smile import *` to get *smile.sound*.

Troubleshooting
---------------

This section is used to show you how to fix common problems with your install. 

Windows Troubleshooting
+++++++++++++++++++++++

*If you accidentally installed smile to your person python distribution* instead of kivy's python distribution, you will recieve an error similar to `ImportError: No module named smile` when trying to import smile. 

The solution is to first, delete smile from your personal python distribuiton. Navigate to the smile download folder in your command promt and run the following. 

::
    
    >python -m pip uninstall .
    
Then, install smile to kivy's python distribution.

::

    >kivy-2.7 -m pip install .
    
*If you are trying to replace an older version of smile*, or if you just need to upgrade your currect version, you must run the following command while the command promt is in the smile download folder

::

    >kivy-2.7 -m pip install . --update
    
Mac Troubleshooting
+++++++++++++++++++

To be added when problems are found.

Linux Troubleshooting
+++++++++++++++++++++

To be added when problems are found.