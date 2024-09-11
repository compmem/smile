import random
import string
from pathlib import Path

# config vars
NUM_TRIALS = 2
# The trials, shuffled, for the stimulus generation.
NUM_ITEMS = [2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4]
random.shuffle(NUM_ITEMS)
ITEMS = string.ascii_lowercase

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()
# instructions writen in another document
instruct_text = open(script_dir / 'stern_instructions.rst', 'r').read()

RSTFONTSIZE = 30
RSTWIDTH = 900
STUDY_DURATION = 1.2
STUDY_ISI = .4
RETENTION_INTERVAL = 1.0

# KeyPress stuff
RESP_KEYS = ['J', 'K']
RESP_DELAY = .2
ORIENT_DURATION = 1.0
ORIENT_ISI = .5
ITI = 1.0
FONTSIZE = 30
