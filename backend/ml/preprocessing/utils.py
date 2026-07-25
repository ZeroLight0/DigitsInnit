"""Small helpers for locating and decoding digit images."""

import base64
import binascii
import re
from pathlib import Path

from preprocessing.image_processor import SUPPORTED_EXTENSIONS, PreprocessingError

_DATA_URL_PREFIX = re.compile(r"^data:image/[a-zA-Z0-9.+-]+;base64,", re.IGNORECASE)


def ensure_image_path(image_path: str | Path) -> Path:
    """Return a Path and validate that it points to an existing image file."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    if not path.is_file():
        raise ValueError(f"Expected a file path, got: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported formats: {sorted(SUPPORTED_EXTENSIONS)}"
        )
    return path


def list_images(directory: str | Path) -> list[Path]:
    """Return every supported image inside a directory, sorted by name."""
    root = Path(directory)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    return sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def decode_base64_image(payload: str) -> bytes:
    """Decode a base64 string, with or without a ``data:image/...`` prefix."""
    if not isinstance(payload, str) or not payload.strip():
        raise PreprocessingError("Expected a non-empty base64 image string.")

    encoded = _DATA_URL_PREFIX.sub("", payload.strip())
    # Tolerate base64 that lost its padding in transit.
    encoded += "=" * (-len(encoded) % 4)

    try:
        return base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise PreprocessingError(f"Invalid base64 image data: {error}") from error
