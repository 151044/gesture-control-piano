import queue
import threading
import tkinter as tk
from typing import Callable

import numpy as np

from config import (
    WHITE_NOTES, WHITE_KEY_COLOR, WHITE_KEY_PRESSED_COLOR,
    BLACK_KEY_COLOR, BLACK_KEY_PRESSED_COLOR,
    STARTING_OCTAVE, OCTAVE_COUNT,
    SAMPLE_RATE, NOTE_DURATION
)

# Try to import audio libraries
try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Warning: sounddevice not installed. Audio will be disabled.")
    print("Install with: pip install sounddevice")


class NoteFrequencies:
    """Calculate note frequencies based on A4 = 440Hz."""

    A4_FREQ = 440.0
    A4_MIDI = 69

    @classmethod
    def get_frequency(cls, note_name: str) -> float:
        """
        Get the frequency for a note name like 'C4' or 'F#5'.
        :param note_name: Note name with octave (e.g., 'C4', 'F#5').
        :return: Frequency in Hz.
        """
        # Parse note name
        if '#' in note_name:
            note = note_name[:2]
            octave = int(note_name[2:])
        else:
            note = note_name[0]
            octave = int(note_name[1:])

        # Get semitone offset from C
        note_offsets = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
        }

        # Calculate MIDI number
        midi_number = (octave + 1) * 12 + note_offsets[note]

        # Calculate frequency
        return cls.A4_FREQ * (2 ** ((midi_number - cls.A4_MIDI) / 12))


class AudioPlayer:
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        """Initializes the audio player."""
        self.__sample_rate: int = sample_rate
        self.__is_muted: bool = False
        self.__audio_queue: queue.Queue[tuple[float, float]] = queue.Queue()
        self.__stop_event: threading.Event = threading.Event()

        if AUDIO_AVAILABLE:
            self._audio_thread = threading.Thread(target=self.__audio_worker, daemon=True)
            self._audio_thread.start()

    def __generate_note(self, frequency: float, duration: float) -> np.ndarray:
        """
        Generate a piano-like tone.
        :param frequency: Frequency in Hz.
        :param duration: Duration in seconds.
        :return: Audio samples as a numpy array.
        """
        t = np.linspace(0, duration, int(self.__sample_rate * duration), False)

        # Generate harmonics for a more piano-like sound
        tone = np.zeros_like(t)
        harmonics = [1.0, 0.5, 0.25, 0.125, 0.0625]

        for i, amplitude in enumerate(harmonics, 1):
            tone += amplitude * np.sin(2 * np.pi * frequency * i * t)

        # Apply envelope (ADSR-like)
        attack = int(0.01 * self.__sample_rate)
        decay = int(0.1 * self.__sample_rate)

        envelope = np.ones_like(t)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[-decay:] = np.linspace(1, 0, decay)

        tone = tone * envelope

        # Normalize
        tone = tone / np.max(np.abs(tone)) * 0.5

        return tone.astype(np.float32)

    def __audio_worker(self) -> None:
        """Worker thread for playing audio."""
        while not self.__stop_event.is_set():
            try:
                frequency, duration = self.__audio_queue.get(timeout=0.1)
                if not self.__is_muted:
                    samples = self.__generate_note(frequency, duration)
                    sd.play(samples, self.__sample_rate)
                    sd.wait()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Audio playback error: {e}")

    def play_note(self, note_name: str, duration: float = NOTE_DURATION) -> None:
        """
        Play a note.
        :param note_name: Note name with octave (e.g., 'C4').
        :param duration: Duration in seconds.
        """
        if not AUDIO_AVAILABLE:
            return

        frequency = NoteFrequencies.get_frequency(note_name)

        # Clear queue to stop any currently playing note
        while not self.__audio_queue.empty():
            try:
                self.__audio_queue.get_nowait()
            except queue.Empty:
                break

        self.__audio_queue.put((frequency, duration))

    def set_muted(self, muted: bool) -> None:
        """Set mute state."""
        self.__is_muted = muted

    def stop(self) -> None:
        """Stop the audio player."""
        self.__stop_event.set()
        if AUDIO_AVAILABLE:
            sd.stop()


class PianoKeyboard(tk.Canvas):
    def __init__(self, parent, octaves: int = OCTAVE_COUNT,
                 starting_octave: int = STARTING_OCTAVE,
                 on_key_press: Callable[[str], None] | None = None,
                 **kwargs):
        """
        Initialize the piano keyboard.
        :param parent: Parent tkinter widget.
        :param octaves: Number of octaves to display.
        :param starting_octave: Starting octave number.
        :param on_key_press: Callback function when a key is pressed.
        """
        # Default size
        width = kwargs.pop('width', 400)
        height = kwargs.pop('height', 200)

        super().__init__(parent, width=width, height=height,
                         bg='#1a1a1a', highlightthickness=0, **kwargs)

        self.__octaves: int = octaves
        self.__starting_octave: int = starting_octave
        self.__on_key_press: Callable[[str], None] | None = on_key_press

        self.__white_keys: dict[str, int] = {}   # note_name -> canvas id
        self.__black_keys: dict[str, int] = {}
        self.__key_rects: dict[str, tuple] = {}  # note_name -> (x1, y1, x2, y2)

        self.__audio_player: AudioPlayer = AudioPlayer()

        self.__create_keyboard()
        self.bind('<Configure>', self.__on_resize)
        self.bind('<Button-1>', self.__on_click)

    def __create_keyboard(self) -> None:
        """Create the piano keyboard."""
        self.delete('all')
        self.__white_keys.clear()
        self.__black_keys.clear()
        self.__key_rects.clear()

        width = self.winfo_width() or 400
        height = self.winfo_height() or 200

        # Calculate key dimensions
        white_keys_per_octave = len(WHITE_NOTES)
        total_white_keys = white_keys_per_octave * self.__octaves

        white_key_width = width / total_white_keys
        white_key_height = height
        black_key_width = white_key_width * 0.6
        black_key_height = height * 0.6

        # Draw white keys first
        white_key_index = 0
        for octave in range(self.__starting_octave, self.__starting_octave + self.__octaves):
            for note in WHITE_NOTES:
                note_name = f"{note}{octave}"
                x1 = white_key_index * white_key_width
                y1 = 0
                x2 = x1 + white_key_width - 2
                y2 = white_key_height

                key_id = self.create_rectangle(
                    x1, y1, x2, y2,
                    fill=WHITE_KEY_COLOR,
                    outline='#333333',
                    width=1,
                    tags=('white_key', note_name)
                )
                self.__white_keys[note_name] = key_id
                self.__key_rects[note_name] = (x1, y1, x2, y2)

                # Add note label
                self.create_text(
                    (x1 + x2) / 2, y2 - 20,
                    text=note_name,
                    font=('Arial', 8),
                    fill='#333333',
                    tags=('label',)
                )

                white_key_index += 1

        # Draw black keys on top
        white_key_index = 0
        for octave in range(self.__starting_octave, self.__starting_octave + self.__octaves):
            for i, note in enumerate(WHITE_NOTES):
                # Determine if there's a black key after this white key
                if note in ['C', 'D', 'F', 'G', 'A']:
                    black_note = note + '#'
                    note_name = f"{black_note}{octave}"

                    x1 = (white_key_index + 1) * white_key_width - black_key_width / 2
                    y1 = 0
                    x2 = x1 + black_key_width
                    y2 = black_key_height

                    key_id = self.create_rectangle(
                        x1, y1, x2, y2,
                        fill=BLACK_KEY_COLOR,
                        outline='#000000',
                        width=1,
                        tags=('black_key', note_name)
                    )
                    self.__black_keys[note_name] = key_id
                    self.__key_rects[note_name] = (x1, y1, x2, y2)

                white_key_index += 1

    def __on_resize(self, _) -> None:
        """Handle resize event."""
        self.__create_keyboard()

    def __on_click(self, event) -> None:
        """Handle mouse click on keyboard."""
        # Check black keys first (they're on top)
        for note_name, (x1, y1, x2, y2) in self.__key_rects.items():
            if '#' in note_name:  # Black key
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    self.highlight_key(note_name)
                    self.__audio_player.play_note(note_name)
                    if self.__on_key_press:
                        self.__on_key_press(note_name)
                    return

        # Check white keys
        for note_name, (x1, y1, x2, y2) in self.__key_rects.items():
            if '#' not in note_name:  # White key
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    self.highlight_key(note_name)
                    self.__audio_player.play_note(note_name)
                    if self.__on_key_press:
                        self.__on_key_press(note_name)
                    return

    def highlight_key(self, note_name: str, duration_ms: int = 300) -> None:
        """
        Highlight a key temporarily.
        :param note_name: Note name to highlight (e.g., 'C4').
        :param duration_ms: How long to keep the key highlighted.
        """
        if '#' in note_name:
            if note_name in self.__black_keys:
                key_id = self.__black_keys[note_name]
                self.itemconfig(key_id, fill=BLACK_KEY_PRESSED_COLOR)
                self.after(duration_ms,
                           lambda: self.itemconfig(key_id, fill=BLACK_KEY_COLOR))
        else:
            if note_name in self.__white_keys:
                key_id = self.__white_keys[note_name]
                self.itemconfig(key_id, fill=WHITE_KEY_PRESSED_COLOR)
                self.after(duration_ms,
                           lambda: self.itemconfig(key_id, fill=WHITE_KEY_COLOR))

    def play_and_highlight(self, note_name: str) -> None:
        """
        Play a note and highlight the corresponding key.
        :param note_name: Note name to play (e.g., 'C4').
        """
        self.highlight_key(note_name)
        self.__audio_player.play_note(note_name)

    def set_muted(self, muted: bool) -> None:
        """Set mute state for audio."""
        self.__audio_player.set_muted(muted)

    def cleanup(self) -> None:
        """Clean up resources."""
        self.__audio_player.stop()
