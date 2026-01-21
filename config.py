"""Configuration constants for the Musical Gesture App."""

# Bunch of timing constants by the magic of the Internet
FRAME_CAPTURE_INTERVAL_MS = 500  # Interval for feeding frames to the model (milliseconds)
CAMERA_DISPLAY_INTERVAL_MS = 30  # Interval for updating camera display (milliseconds)
KEY_HIGHLIGHT_DURATION_MS = 300  # How long a key stays highlighted (milliseconds)

# Piano configuration
OCTAVE_COUNT = 2
STARTING_OCTAVE = 4  # Middle C is C4

# Note definitions for 2 octaves
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Generate all notes for the specified octaves
def get_all_notes():
    """Generate list of all notes for the piano."""
    return [
        f"{note}{octave}" for note in NOTE_NAMES for octave in range(STARTING_OCTAVE, STARTING_OCTAVE + OCTAVE_COUNT)
    ]

ALL_NOTES = get_all_notes()

# White and black key identification
WHITE_NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
BLACK_NOTES = ['C#', 'D#', 'F#', 'G#', 'A#']

# Colours
WHITE_KEY_COLOR = '#FFFFFF'
WHITE_KEY_PRESSED_COLOR = '#90EE90'  # Light green
BLACK_KEY_COLOR = '#1a1a1a'
BLACK_KEY_PRESSED_COLOR = '#32CD32'  # Lime green
BACKGROUND_COLOR = '#2b2b2b'
BUTTON_COLOR = '#404040'
BUTTON_ACTIVE_COLOR = '#4CAF50'

# Audio configuration
SAMPLE_RATE = 44100
NOTE_DURATION = 0.3  # seconds

# Model configuration
MODEL_PATH = "model/keras_model.h5"
LABELS_PATH = "model/labels.txt"
INPUT_SIZE = (224, 224)