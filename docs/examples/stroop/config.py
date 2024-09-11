from pathlib import Path
# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()
instruct_text = open(script_dir / 'stroop_instructions.rst', 'r').read()
NUM_BLOCKS = 4
LEN_BLOCKS = 24
RECORD_DURATION = 2
INTER_BLOCK_DURATION = 2
INTER_STIMULUS_INTERVAL = 2
RST_FONT_SIZE = 30
RST_WIDTH = 900
