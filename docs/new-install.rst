============================
Installation of SMILE!
============================

Requirements
============

- SMILE Downloaded from GitHub: `SMILE Download <https://github.com/compmem/smile/master>`_
- Python 3.6 or newer

Use ``python3 --version`` (or ``python --version`` depending on your setup) in the terminal or Command Prompt to check your Python version & upgrade if necessary.

Non-Conda Installation
======================
1. Navigate to the directory where you downloaded SMILE and extract the contents if necessary.

2. In the terminal (or Command Prompt on Windows), navigate to the parent directory of the SMILE project.

3. To keep a clean work environment, create a `virtual environment <https://docs.python.org/3/library/venv.html>` for your SMILE work:

    On Windows, MacOS, & Linux: ::

    python3 -m venv .smile_venv

4. Activate the virtual environment:

    On MacOS & Linux: ::

    $ source .smile_venv/bin/activate

    On Windows: ::

    > .smile_venv\Scripts\activate

5. In the terminal, navigate to the SMILE project directory where the `pyproject.toml` file is located.
    - SMILE uses a `pyproject.toml <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>` file to specify requirements & dependencies for packaging SMILE.

6. Install SMILE:

    a. Base install - SMILE + Kivy:

        On Windows, MacOS, & Linux: ::

        python3 -m pip install .
    
    b. If using the `smile.sound` functionality - SMILE + Kivy + PYO:

        If using the `smile.sound` functionality, include PYO in the install: ::

        python3 -m pip install .[pyo]

