"""Digit inference: loads the trained CNN once and serves predictions."""

import logging
import threading
from pathlib import Path
from typing import Any

import numpy as np

from app.config import MODEL_PATH
from preprocessing.image_processor import IMAGE_SIZE, preprocess_bytes

logger = logging.getLogger(__name__)


class ModelNotAvailableError(RuntimeError):
    """Raised when the trained model file is missing or cannot be loaded."""


class DigitPredictor:
    """Thread-safe lazy loader and inference wrapper around the Keras model."""

    def __init__(self, model_path: str | Path = MODEL_PATH) -> None:
        self.model_path = Path(model_path)
        self._model: Any | None = None
        self._lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> Any:
        """Load the model, or return the already loaded one.

        Uvicorn serves requests from a thread pool, so the double-checked lock
        keeps two concurrent first-requests from loading the model twice.
        """
        if self._model is not None:
            return self._model

        with self._lock:
            if self._model is not None:
                return self._model

            if not self.model_path.exists():
                raise ModelNotAvailableError(
                    f"Trained model not found at {self.model_path}. "
                    "Run `python -m training.train` to create it."
                )

            # Imported lazily so the service (and the tests) can import this
            # module without paying TensorFlow's multi-second import cost.
            import keras

            logger.info("Loading model from %s", self.model_path)
            try:
                self._model = keras.models.load_model(self.model_path)
            except Exception as error:  # noqa: BLE001 - surfaced as 503 by the API
                raise ModelNotAvailableError(
                    f"Failed to load model at {self.model_path}: {error}"
                ) from error

            logger.info("Model loaded: %s", self.model_path.name)
            return self._model

    def predict_tensor(self, tensor: np.ndarray) -> dict[str, Any]:
        """Predict from an already preprocessed ``(1, 28, 28, 1)`` tensor."""
        expected = (1, IMAGE_SIZE, IMAGE_SIZE, 1)
        if tensor.shape != expected:
            raise ValueError(f"Expected tensor of shape {expected}, got {tensor.shape}")

        model = self.load()
        probabilities = np.asarray(model.predict(tensor, verbose=0)[0], dtype=np.float64)

        digit = int(np.argmax(probabilities))
        return {
            "prediction": digit,
            "confidence": round(float(probabilities[digit]) * 100.0, 2),
            "probabilities": {
                str(index): round(float(value) * 100.0, 2)
                for index, value in enumerate(probabilities)
            },
        }

    def predict_bytes(self, data: bytes) -> dict[str, Any]:
        """Preprocess raw image bytes and predict the digit."""
        return self.predict_tensor(preprocess_bytes(data))

    def predict_image(self, image_path: str | Path) -> dict[str, Any]:
        """Preprocess an image file and predict the digit."""
        return self.predict_bytes(Path(image_path).read_bytes())


_predictor: DigitPredictor | None = None
_predictor_lock = threading.Lock()


def get_predictor() -> DigitPredictor:
    """Return the process-wide predictor instance."""
    global _predictor
    if _predictor is None:
        with _predictor_lock:
            if _predictor is None:
                _predictor = DigitPredictor()
    return _predictor
