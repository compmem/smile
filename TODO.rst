================
Smile To Do List
================


Approximately in order of importance:

- (DONE) Subject processing (i.e., put the log files from a subj in
  their own directory.)

- (DONE) Logging
  - Each State is responsible for creating a dictionary to log the
    most important aspect of that state and write that to a YAML file
    for each experiment.
  - Create a Log state that can pick and choose from other state logs
    to make custom event logs.

- (DONE) Variables
  - For custom tracking of stuff throughout the experiment
    (e.g., counting up the num correct for a block)
  - Implemented as Set and Get states

- Keyboard input
  - (DONE) Add event hooks
  - (DONE) Tracking individual keys
  - Track extended text input

- Mouse input
  - Button presses (what, when, and where)
  - Movement (A list of dicts for each movement during an active
    state)

- (DONE) Conditional state to allow branching

- (DONE) Loop state (to allow looping without unraveling into a big sequence)

- Tests (especially to verify timing)

- (DONE) Plot the DAG with pydot

- Audio playback and recording
  - Should we just use pyaudio b/c we need recording?
  - It would also give us the ability to use JACK.

- Movie playback 
  - (DONE) without audio 
  - sync with audio

- EEG sync pulsing

- Animations (i.e., complex/dynamic visual stimuli)

- Better comments

- Docs (in code and with Sphinx)

- (In Progress) Example experiments

- (DONE) Upload to github

- Find good smile logo/icon



