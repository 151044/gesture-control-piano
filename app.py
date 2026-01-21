"""Main application GUI."""

import tkinter as tk
from tkinter import ttk

from camera import Camera
from config import (
    FRAME_CAPTURE_INTERVAL_MS, CAMERA_DISPLAY_INTERVAL_MS,
    BACKGROUND_COLOR,
    BUTTON_COLOR, BUTTON_ACTIVE_COLOR, INPUT_SIZE
)
from model_handler import ModelHandler
from piano import PianoKeyboard
from tkinter.font import Font


class MusicalGestureApp:
    def __init__(self, root: tk.Tk):
        """
        Initialize the application.
        :param root: The root window.
        """
        self.root: tk.Tk = root
        self.root.title("Musical Gesture Recognition")
        self.root.configure(bg=BACKGROUND_COLOR)

        # Set minimum window size
        self.root.minsize(900, 500)

        # Initialize components
        self.camera: Camera = Camera()
        self.model_handler: ModelHandler = ModelHandler()

        # State variables
        self._is_capturing: bool = False
        self._is_muted: bool = False
        self._camera_update_id: str | None = None
        self._capture_update_id: str | None = None

        # Build the GUI
        self.__create_styles()
        self.__create_widgets()

        # Start camera
        if self.camera.open():
            self.__start_camera_display()
        else:
            self.__show_camera_error()

        self._emoji_font = Font(family="Noto Color Emoji")
        # Bind cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.__on_close)

    @classmethod
    def __create_styles(cls) -> None:
        """Create custom styles for widgets."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure button styles
        style.configure(
            'Control.TButton',
            font=('Arial', 11, 'bold'),
            padding=(20, 10),
            background=BUTTON_COLOR,
            foreground='white'
        )

        style.map('Control.TButton',
                  background=[('active', BUTTON_ACTIVE_COLOR), ('pressed', BUTTON_ACTIVE_COLOR)]
                  )

        style.configure(
            'Active.TButton',
            font=('Arial', 11, 'bold'),
            padding=(20, 10),
            background=BUTTON_ACTIVE_COLOR,
            foreground='white'
        )

        style.configure(
            'Exit.TButton',
            font=('Arial', 11, 'bold'),
            padding=(20, 10),
            background='#d9534f',
            foreground='white'
        )

        style.map('Exit.TButton',
                  background=[('active', '#c9302c'), ('pressed', '#c9302c')]
                  )

    def __create_widgets(self) -> None:
        """Create and arrange all widgets."""
        # Main container frame
        main_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Configure main_frame grid
        main_frame.grid_rowconfigure(0, weight=1)  # Top section expands
        main_frame.grid_rowconfigure(1, weight=0)  # Button section stays fixed
        main_frame.grid_columnconfigure(0, weight=1)

        # Top section: Camera and Piano (resizable paned window)
        top_frame = tk.PanedWindow(
            main_frame,
            orient=tk.HORIZONTAL,
            bg=BACKGROUND_COLOR,
            sashwidth=8,
            sashrelief=tk.RAISED,
            showhandle=False
        )
        top_frame.grid(row=0, column=0, sticky='nsew')

        # Camera section (left)
        camera_frame = tk.LabelFrame(
            top_frame,
            text=" Camera Feed ",
            font=('Arial', 12, 'bold'),
            bg=BACKGROUND_COLOR,
            fg='white',
            padx=10,
            pady=10
        )
        top_frame.add(camera_frame, stretch="always", minsize=200)

        # Configure camera_frame to give priority to the video, but reserve space for status
        camera_frame.grid_rowconfigure(0, weight=1)  # Camera label expands
        camera_frame.grid_rowconfigure(1, weight=0)  # Status label stays fixed
        camera_frame.grid_columnconfigure(0, weight=1)

        self.camera_label = tk.Label(
            camera_frame,
            bg='#1a1a1a',
            text="Initializing camera...",
            fg='white',
            font=('Arial', 12)
        )
        self.camera_label.grid(row=0, column=0, sticky='nsew')

        # Status label for predictions
        self.status_label = tk.Label(
            camera_frame,
            text="Status: Ready",
            font=('Arial', 10),
            bg=BACKGROUND_COLOR,
            fg='#aaaaaa'
        )
        self.status_label.grid(row=1, column=0, sticky='ew', pady=(10, 0))

        # Piano section (right)
        piano_frame = tk.LabelFrame(
            top_frame,
            text=" Piano Keyboard ",
            font=('Arial', 12, 'bold'),
            bg=BACKGROUND_COLOR,
            fg='white',
            padx=10,
            pady=10
        )
        top_frame.add(piano_frame, stretch="always", minsize=200)

        # Configure piano_frame layout
        piano_frame.grid_rowconfigure(0, weight=1)  # Piano container expands
        piano_frame.grid_rowconfigure(1, weight=0)  # Detected note label stays fixed
        piano_frame.grid_columnconfigure(0, weight=1)

        # Create a container for the piano to control its aspect ratio
        piano_container = tk.Frame(piano_frame, bg=BACKGROUND_COLOR)
        piano_container.grid(row=0, column=0, sticky='nsew')

        self.piano = PianoKeyboard(
            piano_container,
            width=400,
            height=250,
            on_key_press=self.__on_piano_key_press
        )
        # Pack piano to expand horizontally but stay centered vertically with max height
        self.piano.pack(expand=True, fill=tk.X, anchor='center')

        # Bind resize event to maintain aspect ratio
        def on_piano_container_resize(event):
            container_width = event.width
            # Maintain approximately 8:5 aspect ratio (width:height)
            target_height = int(container_width * 0.625)
            self.piano.configure(height=target_height)
            self.piano.configure(width=int(target_height * 8 / 5))

        piano_container.bind('<Configure>', on_piano_container_resize)

        # Detected note label
        self.detected_note_label = tk.Label(
            piano_frame,
            text="Detected: --",
            font=('Arial', 14, 'bold'),
            bg=BACKGROUND_COLOR,
            fg='#4CAF50'
        )
        self.detected_note_label.grid(row=1, column=0, sticky='ew', pady=(10, 0))

        # Bottom section: Control buttons (fixed height)
        button_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
        button_frame.grid(row=1, column=0, sticky='ew', pady=(20, 0))

        # Center the buttons
        button_container = tk.Frame(button_frame, bg=BACKGROUND_COLOR)
        button_container.pack(expand=True)

        # Capture toggle button
        self.capture_button = ttk.Button(
            button_container,
            #text="▶ Start Capture",
            text="Start Capture",
            style='Control.TButton',
            command=self.__toggle_capture
        )
        self.capture_button.pack(side=tk.LEFT, padx=10)

        # Mute toggle button
        self.mute_button = ttk.Button(
            button_container,
            #text="🔊 Sound On",
            text="Sound On",
            style='Control.TButton',
            command=self.__toggle_mute
        )
        self.mute_button.pack(side=tk.LEFT, padx=10)

        # Exit button
        self.exit_button = ttk.Button(
            button_container,
            #text="✕ Exit",
            text="Exit",
            style='Exit.TButton',
            command=self.__on_close
        )
        self.exit_button.pack(side=tk.LEFT, padx=10)

    def __start_camera_display(self) -> None:
        """Start the camera display loop."""
        self.__update_camera_display()

    def __update_camera_display(self) -> None:
        """Update the camera display with the latest frame."""
        if self.camera.is_open:
            # Get frame dimensions from the label
            width = max(self.camera_label.winfo_width(), 320)
            height = max(self.camera_label.winfo_height(), 240)

            img = self.camera.get_frame_for_display(width, height)
            if img is not None:
                self.camera_label.configure(image=img, text='')
                self.camera_label.image = img  # Keep reference

        # Schedule next update
        self._camera_update_id = self.root.after(
            CAMERA_DISPLAY_INTERVAL_MS,
            self.__update_camera_display
        )

    def __show_camera_error(self) -> None:
        """Display camera error message."""
        self.camera_label.configure(
            text="Camera not available.\nPlease check your camera connection.",
            image=''
        )

    def __toggle_capture(self) -> None:
        """Toggle photo capturing for model inference."""
        self._is_capturing = not self._is_capturing

        if self._is_capturing:
            self.capture_button.configure(text="⏹ Stop Capture")
            self.status_label.configure(text="Status: Capturing...", fg='#4CAF50')
            self.__start_model_inference()
        else:
            self.capture_button.configure(text="▶ Start Capture")
            self.status_label.configure(text="Status: Stopped", fg='#aaaaaa')
            self.__stop_model_inference()

    def __start_model_inference(self) -> None:
        """Start the model inference loop."""
        self.__run_inference()

    def __run_inference(self) -> None:
        """Run a single inference and schedule the next one."""
        if not self._is_capturing:
            return

        # Get frame for model
        frame = self.camera.get_frame_for_model(INPUT_SIZE)

        if frame is not None:
            # Run prediction
            predicted_note, confidence = self.model_handler.predict(frame)

            if predicted_note is not None and confidence > 0.5:
                # Update UI
                self.detected_note_label.configure(
                    text=f"Detected: {predicted_note} ({confidence:.1%})"
                )

                actual_predicted_note = predicted_note
                if len(predicted_note) == 1 or (len(predicted_note) == 2 and predicted_note[1] == '#'):
                    actual_predicted_note += '4'

                # Play and highlight the note
                self.piano.play_and_highlight(actual_predicted_note)

                self.status_label.configure(
                    text=f"Status: Detected {predicted_note}",
                    fg='#4CAF50'
                )
            else:
                self.status_label.configure(
                    text="Status: No gesture detected",
                    fg='#ff9800'
                )

        # Schedule next inference
        self._capture_update_id = self.root.after(
            FRAME_CAPTURE_INTERVAL_MS,
            self.__run_inference
        )

    def __stop_model_inference(self) -> None:
        """Stop the model inference loop."""
        if self._capture_update_id is not None:
            self.root.after_cancel(self._capture_update_id)
            self._capture_update_id = None

    def __toggle_mute(self) -> None:
        """Toggle audio mute state."""
        self._is_muted = not self._is_muted
        self.piano.set_muted(self._is_muted)

        if self._is_muted:
            self.mute_button.configure(
                    #text="🔇 Sound Off", 
                    text="Sound Off", 
                    )
        else:
            self.mute_button.configure(
                    #text="🔊 Sound On"
                    text="Sound On"
                    )

    def __on_piano_key_press(self, note_name: str):
        """
        Handle piano key press event.
        :param note_name: The name of the pressed note.
        """
        self.detected_note_label.configure(text=f"Played: {note_name}")

    def __on_close(self) -> None:
        """Clean up and close the application."""
        # Stop any running updates
        if self._camera_update_id is not None:
            self.root.after_cancel(self._camera_update_id)

        if self._capture_update_id is not None:
            self.root.after_cancel(self._capture_update_id)

        # Clean up resources
        self.camera.close()
        self.piano.cleanup()

        # Close the window
        self.root.destroy()
