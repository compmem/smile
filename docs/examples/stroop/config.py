from pathlib import Path
# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()
# Read in the instructions
INSTRUCT_TEXT = open(script_dir / 'stroop_instructions.rst', 'r').read()
NUMBER_OF_BLOCKS = 1
NUMBER_OF_TRIALS_PER_BLOCK = 2
RECORD_DURATION = 2
INTER_BLOCK_DURATION = 2
INTER_STIMULUS_INTERVAL = 2
RST_FONT_SIZE = 30
RST_WIDTH = 900
