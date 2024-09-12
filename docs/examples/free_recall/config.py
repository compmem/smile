from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()

# Define paths to the stimulus files, relative to the script's location
POOLS_DIR = script_dir / "pools"
LIVING_TXT_PATH = POOLS_DIR / "living.txt"
NONLIVING_TXT_PATH = POOLS_DIR / "nonliving.txt"

# Open and combine the stimulus files with error handling
try:
    living_list = LIVING_TXT_PATH.read_text().splitlines()
    nonliving_list = NONLIVING_TXT_PATH.read_text().splitlines()
except FileNotFoundError as e:
    print(f"Error: Stimulus file not found. {e}")
    exit(1)

stim_list = living_list + nonliving_list

# Open the instructions file, also relative to the script's location
INSTRUCTIONS_PATH = script_dir / 'freekey_instructions.rst'
try:
    INSTRUCT_TEXT = INSTRUCTIONS_PATH.read_text()
except FileNotFoundError as e:
    print(f"Error: Instructions file not found. {e}")
    exit(1)

# Define the Experimental Variables (Constants)
INTER_STIMULUS_INTERVAL = 2
INTER_BLOCK_INTERVAL = 2
STIMULUS_DURATION = 2
PRE_FREE_KEY_INTERVAL = 4
FONT_SIZE = 40
RST_FONT_SIZE = 30
RST_WIDTH = 900
MIN_FREE_KEY_DURATION = 20

NUM_BLOCKS = 2
NUM_PER_BLOCK = [10, 15, 20]
