=====================================================
Instructions on installing and using Smile on Android
=====================================================
:Author: Brandon Jacques <beegjacques@yahoo.com>
:Date: 2015-09-10 
:Revision: 
:Description: This is the step by step guide to running smile experiments on android
            

Preparing your Experiment Directory
===================================
1. Inside your project directory, you need to rename your experiment file to 
   "main.py". This allows a program called Buildozer to find the file that is needed
   to run your experiment.

2. You must then have a folder in your experiment directory that contains all of the 
   smile .py files and call this folder "smile"

3. NOTE : You must add a line to your "main.py" exactly as shown below. If you don't
   include the spaces on either side of the equal sign, buildozer will not compile 
   your experiment for android:
    
    __version__ = "1.0.0"

.. note:: You may put whatever numbers you want inplace of the 1.0.0 but they must be in quotations. 

Installing Buildozer(Your smile for android best friend)
========================================================
Buildozer is a packager that allows linux systems to create a file (.apk) that has
everything you need to run your python program packed into that file. This program
automates the entire process by downloading everything that is needed for the 
program Python-For-Android, including the SDK and NDK for android.

In the terminal, change directory to wherever you want to install buildozer 
(probably just in your documents folder) and then run the following in your terminal
window 

::

    >>>git clone https://github.com/kivy/buildozer.git
    >>>cd buildozer
    >>>sudo python2.7 setup.py install

This installs buildozer and then allows you to run buildozer from any directory.

Customizing your build specifications
=====================================
First things first, we must have buildozer generate a "buildozer.spec" file for our
python program. Run the following line in your terminal in your project directory.

::

    >>>buildozer init

You will see that buildozer has created a file called "buildozer.spec". In this file
we need to make some changes. Open the file with and we will start with editing the "title" line.

::

    title : Whatever you name your Experiment 

Easy, Next we need to edit the source line. This line tells buildozer what files in
the experiment directory to include when packing everything up into your .apk file.

.. note:: We are adding file extentions to the end of this line. Use the format of ",extention". They must have a comma in between each new extention. The py, kv, jpg, png, atlas are the defaults and required to be included.

::

    source.include_exts = py,png,jpg,kv,atlas,mp3,mp4

Next, we will edit the log_level line. If we set log_level to 2 then we are able to 
see all of the logs and the errors if buildozer breaks.

::

    log_level = 2

Finally, we need to edit the requirements line. This line tells buildozer what 
packages to download and include into it's packaged version of pythong. kivy is 
required always for smile, but here you can include packages like "ffmpeg" for 
playing video through smile. 

::

    requirements = kivy,ffmpeg

Building your project with Buildozer
====================================
This next step takes a few minutes to run. Running the next line in your terminal
will download all of the python-for-android files, all of your required packages that 
can be downloaded, package all of your included files that match any of your 
include_exts, and download the SDK and NDK that are needed to compile your python 
code. In your terminal run the following line.

::

    >>>buildozer android debug

.. note:: This process can take a long time depending on how many packages your python
         program requires. 

You will notice the process is complete if the terminal sends you a message saying 
that the application file has been saved in the *bin* folder.

Changing up the blacklist to allow Smile to Run
===============================================
Once buildozer has built your .apk, it also filled your directory with some new 
folders. The important folder for this step is the *.buildozer* folder. We need to 
edit the *blacklist.txt* file to tell buildozer to include *python._csv*, otherwise 
smile cannot run. First, Navagate to the path below.

::

    >>>cd .buildozer/android/platform/python-for-android/dist/myapp/

In This folder, gedit **blacklist.txt**. Under the ``unused binaries python modules`` 
section of the file, put a *#* in fron of the line that has **_csv.so** in it. What the 
new line should look like is presented below

::

    #lib-dynload/_csv.so

.. note:: If you do not comment out this line with *#* then the **_csv.so** will not be
         included in your ".apk" and then smile will break. 

Setting up an Android phone as a Developer to install Homebrew apps
===================================================================
Different android devices have processes that are basically the same for setting up 
a phone in Developer mode.  

1. Navagate to *Settings->About Phone* and tap the *Build Number* button 7 times. 
   This sets up your phone for developer mode. This unlocks a new settings tab 
   called *Developer Options*.

2. Navagate to *Settings->Developer Options* and Enable *USB debugging*. This allows
   your linux machine to send the build version of your python experiment straight to
   your phone. 


Finally Adding your APK to your Phone
=====================================
If you hook up via USB to your linux machine, you will be able to automatically 
upload the .apk to your android phone. With the following line sent into your 
terminal, you rebuild your program with the required python libraries. This line also
sets your terminal to print out the logs from your phone. The line is as follows.

::

    >>>buildozer android debug deploy run logcat

This will open the app on your phone allowing you to see if it works!

.. note:: If your phone isn't unlocked, the experiment will not run from the terminal,
         make sure your phone isn't locked when you run the above line.

.. note:: If it looks like the app breaks before running, press *Ctrl+C*. If you press
         this early enough, then you will be able to *Ctrl+F* and find *python*. This
         will let you find the lines that *kivy* has sent to the log and help you 
         find where and why your smile program broke.  
















