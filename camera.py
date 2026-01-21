import cv2
import numpy as np
from PIL import Image, ImageTk

class Camera:
    def __init__(self, camera_index: int = 0):
        """
        Initialize the camera.
        :param camera_index: Index of the camera device to use.
        """
        self.__camera_index: int = camera_index
        self.__video_capture: cv2.VideoCapture | None = None
        self.__is_open: bool = False

    def open(self) -> bool:
        """
        Open the camera connection.
        :return: True if camera opened successfully, False otherwise.
        """
        self.__video_capture = cv2.VideoCapture(self.__camera_index)
        self.__is_open = self.__video_capture.isOpened()
        return self.__is_open

    def close(self) -> None:
        """Release the camera resource."""
        if self.__video_capture is not None:
            self.__video_capture.release()
            self.__is_open = False

    def read_frame(self) -> tuple[bool, np.ndarray]: # tuple[bool, np.ndarray | None]
        """
        Read a frame from the camera.

        :return: A tuple of 2 elements.
        The former is a boolean value of whether the frame was read.
        The latter is the read frame, or None if the frame couldn't be read.
        """
        if not self.__is_open or self.__video_capture is None:
            return False, None

        ret, frame = self.__video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return ret, frame

    def get_frame_for_display(self, max_width: int = 400, max_height: int = 300) -> ImageTk.PhotoImage: # ImageTk.PhotoImage | None
        """
        Get a frame for display.
        :param max_width: Maximum width for the displayed frame.
        :param max_height: Maximum height for the displayed frame.

        :return: The frame converted to an instance of ImageTk.PhotoImage, or None if the frame couldn't be read.
        """
        ret, frame = self.read_frame()
        if not ret or frame is None:
            return None

        # Resize frame to fit display area while maintaining aspect ratio
        h, w = frame.shape[:2]
        scale = min(max_width / w, max_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h))

        # Convert to PhotoImage
        return ImageTk.PhotoImage(Image.fromarray(frame))

    def get_frame_for_model(self, target_size: tuple[int, int] = (224, 224)) -> np.ndarray: # np.ndarray | None
        """
        Get a frame for the ML model.
        :param target_size: Target size for the model input.
        :return: Preprocessed numpy array, or None if frame couldn't be read.
        """
        ret, frame = self.read_frame()
        if not ret or frame is None:
            return None

        frame = cv2.resize(frame, target_size)

        # This is what the website said to normalise idk
        frame = frame.astype(np.float32) / 127.5 - 1

        # model expects a 4D array of shape (1, 224, 224, 3) I believe
        return np.expand_dims(frame, axis=0)

    @property
    def is_open(self) -> bool:
        """Check if camera is open."""
        return self.__is_open
