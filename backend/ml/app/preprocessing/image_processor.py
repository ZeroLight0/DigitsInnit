"""Backwards-compatible alias for the canonical preprocessing module.

The real implementation lives in ``preprocessing/image_processor.py`` at the
``backend/ml`` root so the training scripts and the API share exactly one
pipeline. Importing it from two places is how the polarity/centring logic drifts
apart, so this module only re-exports.
"""

from preprocessing.image_processor import (  # noqa: F401
    BlankImageError,
    IMAGE_SIZE,
    PreprocessingError,
    SUPPORTED_EXTENSIONS,
    preprocess_array,
    preprocess_bytes,
    preprocess_image,
    preprocessing_stages,
)

__all__ = [
    "BlankImageError",
    "IMAGE_SIZE",
    "PreprocessingError",
    "SUPPORTED_EXTENSIONS",
    "preprocess_array",
    "preprocess_bytes",
    "preprocess_image",
    "preprocessing_stages",
]
