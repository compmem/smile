from pathlib import Path
from smile.common import *
from smile.questionnaire import csv2loq

# Get the directory of the current script
script_dir = Path(__file__).parent.absolute()

# Define the path to the questionnaire CSV file
csv_file_path = script_dir / "questionnaire_example.csv"

# Initialize the Experiment with given resolution
exp = Experiment()

with Parallel():
    # Load the questionnaire from the CSV file, using Ref to pass the path dynamically
    with UntilDone():
        tt = Questionnaire(loq=Ref(csv2loq, str(csv_file_path)),
                           height=exp.screen.height,
                           width=exp.screen.width,
                           x=0, y=0)
    MouseCursor()

# Log the questionnaire results
Log(tt.results)

# Run the experiment
exp.run()
