import os
import sys

# NOTE: This is not the keras in the latest tensorflow
from tf_keras.models import load_model
import numpy as np

from config import MODEL_PATH, LABELS_PATH, ALL_NOTES

class ModelHandler:
    def __init__(self, model_path: str = MODEL_PATH, labels_path: str = LABELS_PATH):
        """
        Initialize the model handler.
        :param model_path: Path to the Keras model.
        :param labels_path: Path to `labels.txt`.
        """
        self.__model_path: str = model_path
        self.__labels_path: str = labels_path
        self.__model = None
        self.__labels: list[str] = []
        self.__model_loaded = False

        self.__load_labels()
        self.__load_model()

    def __load_labels(self) -> None:
        """Load class labels from `labels.txt`."""
        if os.path.exists(self.__labels_path):
            with open(self.__labels_path, 'r') as f:
                self.__labels = [l.strip() for l in f.readlines()]
            print(f"Loaded {len(self.__labels)} labels from {self.__labels_path}")
        else:
            # Default to note names if labels file doesn't exist
            self.__labels = ALL_NOTES.copy()
            print(f"Label file not found. Using default note labels: {self.__labels}")

    def __load_model(self) -> None:
        """Load the Keras model."""
        if os.path.exists(self.__model_path):
            try:
                # Google Teachable Machine is not keras 3 compliant, therefore we use tf_keras,
                # which apparently uses keras 2 API
                self.__model = load_model(self.__model_path, compile=False)
                self.__model_loaded = True
                print(f"Model loaded successfully from {self.__model_path}")
            except Exception as e:
                print(f"Error loading model: {e}.\nExiting.")
                sys.exit(0)
        else:
            print(f"Model file not found at {self.__model_path}. Exiting.")
            sys.exit(0)

    def predict(self, frame: np.ndarray) -> tuple[str, float]: # tuple[str | None, float]
        """
        Make a prediction on a frame.
        :param frame: Preprocessed frame for the model (batch_size, height, width, channels).
        :return: A tuple of (predicted_label, confidence), or (None, 0.0) if prediction fails.
        """
        try:
            predictions = self.__model.predict(frame)
            predicted_index = np.argmax(predictions)
            confidence = predictions[0][predicted_index]

            # Idk how the prediction works, and I'm too lazy to test it out myself
            if predicted_index < len(self.__labels):
                # This assumes there are only 10 classes. If there are > 10, then change it to 3: or 4:
                return self.__labels[predicted_index][len(str(len(self.__labels) - 1)) + 1:], float(confidence)
            else:
                return None, 0.0
        except Exception as e:
            print(f"Prediction error: {e}")
            return None, 0.0

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.__model_loaded

    def get_labels(self) -> list[str]:
        """Get the list of class labels."""
        return self.__labels.copy()
