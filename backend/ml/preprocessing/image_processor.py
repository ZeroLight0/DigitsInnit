"""MNIST-style preprocessing for handwritten digit images.

This is the single source of truth for turning an arbitrary user image (uploaded
photo or canvas drawing) into the exact tensor shape the trained CNN expects:
``(1, 28, 28, 1)`` float32 in ``[0, 1]``, white ink on a black background.

The pipeline mirrors how the original MNIST digits were normalised, which is
what makes a model trained on MNIST usable on real-world input:

1. decode (alpha channels flattened onto white)
2. grayscale + denoise
3. Otsu threshold with automatic polarity detection (ink becomes white)
4. drop speckle noise, keep the digit's connected components
5. crop to the ink bounding box
6. scale the longest side to 20px, preserving aspect ratio
7. paste into a 28x28 canvas
8. shift so the digit's centre of mass sits at the canvas centre
9. normalise to [0, 1] and add batch/channel dimensions
"""

from pathlib import Path

import cv2
import numpy as np

IMAGE_SIZE = 28
DIGIT_BOX = 20

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# A stroke never covers this much of the frame; if it does, polarity is wrong.
_MAX_INK_FRACTION = 0.6

# Components smaller than this fraction of the largest one are treated as noise.
_MIN_COMPONENT_RATIO = 0.05


class PreprocessingError(ValueError):
    """Raised when an image cannot be turned into a model input."""


class BlankImageError(PreprocessingError):
    """Raised when no ink (i.e. no digit) could be found in the image."""


def preprocess_image(image_path: str | Path) -> np.ndarray:
    """Load an image from disk and return a model-ready tensor."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    if not path.is_file():
        raise PreprocessingError(f"Expected a file path, got: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise PreprocessingError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported formats: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    return preprocess_bytes(path.read_bytes())


def preprocess_bytes(data: bytes) -> np.ndarray:
    """Decode raw image bytes and return a model-ready tensor."""
    if not data:
        raise PreprocessingError("Received an empty image payload.")

    return preprocess_array(_decode(data))


def preprocess_array(image: np.ndarray) -> np.ndarray:
    """Run the pipeline on an already decoded image array."""
    return preprocessing_stages(image)["tensor"]


def preprocessing_stages(image: np.ndarray) -> dict[str, np.ndarray]:
    """Run the pipeline and return every intermediate stage.

    Used by the visualisation helpers and when debugging a bad prediction.
    """
    if image is None or getattr(image, "size", 0) == 0:
        raise PreprocessingError("Received an empty image array.")

    flattened = _flatten_alpha(_as_uint8(image))
    gray = _to_grayscale(flattened)
    denoised = _remove_noise(gray)
    binary = _binarize(denoised)
    cleaned = _remove_specks(binary)
    cropped = _crop_to_ink(cleaned)
    fitted = _fit_to_box(cropped)
    padded = _pad_to_canvas(fitted)
    centered = _center_by_mass(padded)
    normalized = _normalize(centered)

    return {
        "original": flattened,
        "gray": gray,
        "denoised": denoised,
        "binary": binary,
        "cleaned": cleaned,
        "cropped": cropped,
        "fitted": fitted,
        "padded": padded,
        "centered": centered,
        "normalized": normalized,
        "tensor": _prepare_tensor(normalized),
    }


def _decode(data: bytes) -> np.ndarray:
    buffer = np.frombuffer(data, dtype=np.uint8)
    # IMREAD_UNCHANGED keeps the alpha channel so transparent canvas exports
    # can be flattened onto white instead of collapsing to black.
    image = cv2.imdecode(buffer, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise PreprocessingError(
            "Could not decode the image. Supported formats: PNG, JPG, JPEG, WEBP, BMP."
        )
    return image


def _as_uint8(image: np.ndarray) -> np.ndarray:
    """Normalise 16-bit / float images down to 8-bit."""
    if image.dtype == np.uint8:
        return image
    scaled = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
    return scaled.astype(np.uint8)


def _flatten_alpha(image: np.ndarray) -> np.ndarray:
    """Composite any alpha channel onto a white background."""
    if image.ndim == 2:
        return image
    if image.shape[2] == 4:
        colour = image[:, :, :3].astype(np.float32)
        alpha = (image[:, :, 3].astype(np.float32) / 255.0)[..., None]
        blended = colour * alpha + 255.0 * (1.0 - alpha)
        return blended.astype(np.uint8)
    return image[:, :, :3]


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _remove_noise(image: np.ndarray) -> np.ndarray:
    return cv2.GaussianBlur(image, (5, 5), 0)


def _binarize(image: np.ndarray) -> np.ndarray:
    """Otsu threshold, then orient the result so the ink is white (255).

    Uploaded photos are usually dark ink on light paper, while some sources are
    already inverted. Guessing wrong here silently destroys the prediction, so
    the polarity is detected instead of assumed.
    """
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # A light border means the background is the bright side, so flip it.
    if _border_mean(binary) > 127:
        binary = cv2.bitwise_not(binary)

    # Safety net for images whose ink touches every edge.
    if float(np.count_nonzero(binary)) / binary.size > _MAX_INK_FRACTION:
        binary = cv2.bitwise_not(binary)

    return binary


def _border_mean(binary: np.ndarray, width: int = 2) -> float:
    height, image_width = binary.shape
    width = max(1, min(width, height // 2 or 1, image_width // 2 or 1))
    edges = np.concatenate(
        [
            binary[:width].ravel(),
            binary[-width:].ravel(),
            binary[:, :width].ravel(),
            binary[:, -width:].ravel(),
        ]
    )
    return float(edges.mean())


def _remove_specks(binary: np.ndarray) -> np.ndarray:
    """Drop tiny connected components while keeping broken strokes intact."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if count <= 2:  # background plus at most one component
        return binary

    areas = stats[1:, cv2.CC_STAT_AREA]
    threshold = max(2.0, float(areas.max()) * _MIN_COMPONENT_RATIO)

    cleaned = np.zeros_like(binary)
    for index, area in enumerate(areas, start=1):
        if area >= threshold:
            cleaned[labels == index] = 255
    return cleaned


def _crop_to_ink(binary: np.ndarray) -> np.ndarray:
    coords = cv2.findNonZero(binary)
    if coords is None:
        raise BlankImageError("No digit found in the image — it looks blank.")

    x, y, width, height = cv2.boundingRect(coords)
    return binary[y : y + height, x : x + width]


def _fit_to_box(digit: np.ndarray, box: int = DIGIT_BOX) -> np.ndarray:
    """Scale the longest side to ``box`` px, preserving the aspect ratio."""
    height, width = digit.shape
    scale = box / float(max(height, width))
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    return cv2.resize(digit, (new_width, new_height), interpolation=interpolation)


def _pad_to_canvas(digit: np.ndarray, size: int = IMAGE_SIZE) -> np.ndarray:
    if digit.shape[0] > size or digit.shape[1] > size:
        digit = cv2.resize(digit, (size, size), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((size, size), dtype=digit.dtype)
    height, width = digit.shape
    top = (size - height) // 2
    left = (size - width) // 2
    canvas[top : top + height, left : left + width] = digit
    return canvas


def _center_by_mass(image: np.ndarray) -> np.ndarray:
    """Translate the digit so its centre of mass is the canvas centre."""
    moments = cv2.moments(image)
    if moments["m00"] == 0:
        raise BlankImageError("No digit found in the image — it looks blank.")

    center_x = moments["m10"] / moments["m00"]
    center_y = moments["m01"] / moments["m00"]
    height, width = image.shape

    matrix = np.float32(
        [
            [1, 0, (width - 1) / 2.0 - center_x],
            [0, 1, (height - 1) / 2.0 - center_y],
        ]
    )
    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def _normalize(image: np.ndarray) -> np.ndarray:
    return image.astype("float32") / 255.0


def _prepare_tensor(image: np.ndarray) -> np.ndarray:
    return image.reshape(1, IMAGE_SIZE, IMAGE_SIZE, 1)
