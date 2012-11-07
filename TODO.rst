================
Smile To Do List
================


Approximately in order of importance:

- Subject processing (i.e., put the log files from a subj in their own
  directory.)

- Logging
  - Each State is responsible for creating a dictionary to log the
    most important aspect of that state and write that to a YAML file
    for each experiment.
  - Create a Log state that can pick and choose from other state logs
    to make custom event logs.

- Keyboard input
  - Add event hooks
  - Tracking individual keys
  - Track extended text input

- Mouse input
  - Button presses (what, when, and where)
  - Movement (A list of dicts for each movement during an active
    state)

- Conditional state to allow branching

- Loop state (to allow looping without unraveling into a big sequence)

- Tests (especially to verify timing)

- Plot the DAG with pydot

- Audio playback and recording
  - Should we just use pyaudio b/c we need recording?

- Movie playback (sync with audio)

- Animations (i.e., complex/dynamic visual stimuli)

- Better comments

- Docs (in code and with Sphinx)

- Example experiments

- Upload to github

- Find good smile logo/icon



