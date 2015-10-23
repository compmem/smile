============================
Installation of Smile!
============================

:Author: Brandon Jacques <beegjacques@yahoo.com>
:Date: 2015-10-13 
:Revision: 2.0.0
:Description: This is the step by step guide to installing smile on various platforms

Getting ready to SMILE? Then you are in the correct place. This guide will tell you how to install SMILE and the package that SMILE is dependant on, Kivy! To start out, we will install Kivy

Installing SMILE on Windows
---------------------------

The first thing you need to download and install for this installation is *Kivy*. Follow the link provided and download the Windows specific version of Kivy. 

    -`Windows Portable Install <http://kivy.org/docs/installation/installation-windows.html>`_
    
Run the **.exe** you just downloaded and then tell the program to extract Kivy into a location that you know will be easy to find later, like your *Documents* folder or your *Program Files* folder.

This extracts a portable version of Kivy to your computer. We will need this to run SMILE. The next thing we are going to do is add Kivy to your build path. This allows you to call `kivy-2.7` from any directory in the command prompt. 

::
    
    > setx PATH "%PATH%;C:\Path\To\Kivy"

Run this line but replace `C:\Path\To\Kivy` with the path to the folder containing the file **kivy-2.7**. The quotes are needed.

.. warning ::
    
    Be very careful not to mess up this command.
    
After running the last command, it is now time to download SMILE. Download SMILE from the github link provided and then extract it. 

    -`SMILE Download <https://github.com/compmem/smile/tree/kivy>`_

Now, in your command prompt, navigate to the newly extracted smile download folder that contains setup.py and run the following line.

::
    
    > kivy -m pip install .

This installs SMILE to Kivy's portable version of python, that isn't connected to your version of python at all. 

The final thing you need to install to gain access to all of SMILE's functionallity is PYO. Download and install the windows version of PYO from their website. The link is provided below.

    -`PYO Download <http://ajaxsoundstudio.com/software/pyo/>`_

With that, you are finished installing SMILE. Congrats! Head over to `Smile Tutorial<tutorial.html>`_ to start SMILING. 


Windows Troubleshooting
+++++++++++++++++++++++

*If you accidentally installed smile to your person python distribution* instead of kivy's python distribution, you will recieve an error similar to `ImportError: No module named smile` when trying to import smile. 

The solution is to first, delete smile from your personal python distribuiton. Navigate to the smile download folder in your command promt and run the following. 

::
    
    > python -m pip uninstall .
    
Then, install smile to kivy's python distribution.

::

    > kivy-2.7 -m pip install .
    
*If you are trying to replace an older version of smile*, or if you just need to upgrade your currect version, you must run the following command while the command promt is in the smile download folder

::

    > kivy-2.7 -m pip install . --update


Installing SMILE on Mac
-----------------------

If you are installing on Mac, please download and install Continume Anaconda first. It allows for you to have an easy to use package manager for python and it comes with a code editor. The following link will take you to the Anaconda Download page.

    -`Anaconda Download <https://www.continuum.io/downloads>`_

Anaconda uses your local version of Python, so any of the packages available to your python will be available to anaconda and any packages installed with anaconda will be available to your python. 

The next step is to download and install kivy. The following link will take you to the Mac-Kivy install guide.

    -`Mac-Kivy Install Guide <http://kivy.org/docs/installation/installation-macosx.html>`_
    
After you install Kivy, you must download and install SMILE. The following is a link to the smile download page, where you will download the zip, and extract it to an easy to find place.

    -`SMILE Download <https://github.com/compmem/smile/tree/kivy>`_

Now, all you have to do is open the Anaconda Command Prompt and navigate to the newly extracted smile download folder. This folder should contain setup.py. Run the following line to install SMILE to your python ditribution

::
    
    $ pip install .
    
Easy, smile should have installed without any issue. 

The final thing you need to install to gain access to all of SMILE's functionallity is PYO. Download and install the Mac version of PYO from their website. The link is provided below.

    -`PYO Download <http://ajaxsoundstudio.com/software/pyo/>`_

With that, you are finished installing SMILE. Congrats! Head over to `Smile Tutorial<tutorial.html>`_ to start SMILING. 
    
Mac Troubleshooting
+++++++++++++++++++

To be added when problems are found.


Installing Smile with Linux
---------------------------

SMILE requires Kivy to run properly, but if you would like to use the smild.sound functionallity, you need to download and install PYO aswell. Run the following in your command line to install both Kivy and PYO at the same time. 

::

    $ sudo aptitude install python-pyo python-kivy
    
Then, download SMILE from github and extract it to a place you can find later. The download link is the following. 

    -`SMILE Download <https://github.com/compmem/smile/tree/kivy>`_

Next, navigate to the newly extracted smile folder, that contains setup.py, and run the following line in your command prompt.

::
    
    $ pip install .

This will add SMILE to your python distribuiton. 

With that, you are finished installing SMILE. Congrats! Head over to `Smile Tutorial<tutorial.html>`_ to start SMILING. 

Linux Troubleshooting
+++++++++++++++++++++

To be added when problems are found.