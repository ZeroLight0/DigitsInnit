"""MNIST loading, cached inside ``ml/datasets`` for reproducible runs."""

import logging
from pathlib import Path

import numpy as np

from app.config import DATASETS_DIR

logger = logging.getLogger(__name__)

IMAGE_SIZE = 28
NUM_CLASSES = 10
CACHE_FILENAME = "mnist.npz"


def load_mnist(
    cache_dir: str | Path = DATASETS_DIR,
) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    """Return ``(x_train, y_train), (x_test, y_test)`` as raw uint8 arrays.

    Uses ``ml/datasets/mnist.npz`` when present, otherwise downloads once via
    Keras and writes the cache so later runs (and offline machines) work.
    """
    cache_path = Path(cache_dir) / CACHE_FILENAME

    if cache_path.exists():
        logger.info("Loading MNIST from cache: %s", cache_path)
        with np.load(cache_path, allow_pickle=False) as data:
            return (
                (data["x_train"], data["y_train"]),
                (data["x_test"], data["y_test"]),
            )

    logger.info("MNIST cache missing; downloading via Keras.")
    import keras

    (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache_path,
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
    )
    logger.info("Cached MNIST to %s", cache_path)

    return (x_train, y_train), (x_test, y_test)


def to_model_input(images: np.ndarray) -> np.ndarray:
    """Normalise uint8 images to the ``(n, 28, 28, 1)`` float32 model input."""
    return (images.astype("float32") / 255.0).reshape(-1, IMAGE_SIZE, IMAGE_SIZE, 1)
