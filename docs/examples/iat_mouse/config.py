from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()

# RST VARIABLES
RST_FONT_SIZE = 50
RST_WIDTH = 600

# Read instruction files relative to the script location
instruct1 = (script_dir / 'iat_mouse_instructions1.rst').read_text()
instruct2 = (script_dir / 'iat_mouse_instructions2.rst').read_text()
instruct3 = (script_dir / 'iat_mouse_instructions3.rst').read_text()
instruct4 = (script_dir / 'iat_mouse_instructions4.rst').read_text()
instruct5 = (script_dir / 'iat_mouse_instructions5.rst').read_text()
instruct6 = (script_dir / 'iat_mouse_instructions6.rst').read_text()
instruct7 = (script_dir / 'iat_mouse_instructions7.rst').read_text()

# MOUSE MOVING VARIABLES
WARNING_DURATION = 2.0
MOUSE_MOVE_RADIUS = 100
MOUSE_MOVE_INTERVAL = 0.400

# BUTTON VARIABLES
BUTTON_HEIGHT = 150
BUTTON_WIDTH = 200

# GENERAL VARIABLES
FONT_SIZE = 40
INTER_TRIAL_INTERVAL = 0.750
