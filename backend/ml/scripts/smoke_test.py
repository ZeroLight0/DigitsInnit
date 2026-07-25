"""End-to-end check of the digit recognition system, no HTTP server needed.

Renders MNIST test digits as real PNG files (white paper, dark ink, off-centre,
with noise) and pushes them through the same decode -> preprocess -> predict path
the API uses. That catches the failure modes a raw ``model.evaluate`` cannot:
inverted polarity, bad cropping, lost centring.

Run from the ``backend/ml`` directory:

    python -m scripts.smoke_test
    python -m scripts.smoke_test --samples 50 --keep
"""

import argparse
import logging
import tempfile
from pathlib import Path

import cv2
import numpy as np

from app.config import MODEL_PATH
from app.services.predictor import DigitPredictor
from preprocessing.image_processor import BlankImageError, preprocess_bytes
from training.dataset import load_mnist

logging.basicConfig(level=logging.WARNING, format="%(levelname)-8s %(message)s")


def render_as_photo(digit_image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Turn a 28x28 MNIST digit into a messy 'photographed on paper' BGR image."""
    canvas_size = int(rng.integers(180, 320))
    scale = rng.uniform(0.35, 0.65)
    digit_size = max(8, int(canvas_size * scale))

    resized = cv2.resize(digit_image, (digit_size, digit_size), interpolation=cv2.INTER_CUBIC)

    # Dark ink on light paper — the opposite polarity to MNIST.
    paper = np.full((canvas_size, canvas_size), int(rng.integers(225, 255)), dtype=np.uint8)
    top = int(rng.integers(0, canvas_size - digit_size + 1))
    left = int(rng.integers(0, canvas_size - digit_size + 1))
    region = paper[top : top + digit_size, left : left + digit_size]
    paper[top : top + digit_size, left : left + digit_size] = np.minimum(
        region, 255 - resized
    )

    noisy = np.clip(
        paper.astype(np.int16) + rng.normal(0, 6, paper.shape).astype(np.int16), 0, 255
    ).astype(np.uint8)
    return cv2.cvtColor(noisy, cv2.COLOR_GRAY2BGR)


def run(samples: int = 25, model_path: str | Path = MODEL_PATH, keep: bool = False, seed: int = 7) -> int:
    rng = np.random.default_rng(seed)
    (_, _), (x_test, y_test) = load_mnist()
    indices = rng.choice(len(y_test), size=samples, replace=False)

    output_dir = Path(tempfile.mkdtemp(prefix="digitwise_smoke_")) if keep else None
    predictor = DigitPredictor(model_path)

    print(f"Model: {model_path}")
    print(f"Rendering {samples} synthetic photos of MNIST digits...\n")

    correct = 0
    failures: list[str] = []

    for position, index in enumerate(indices):
        expected = int(y_test[index])
        photo = render_as_photo(x_test[index], rng)

        encoded, buffer = cv2.imencode(".png", photo)
        if not encoded:
            failures.append(f"sample {position}: PNG encoding failed")
            continue
        image_bytes = buffer.tobytes()

        if output_dir is not None:
            (output_dir / f"{position:02d}_true{expected}.png").write_bytes(image_bytes)

        try:
            result = predictor.predict_bytes(image_bytes)
        except BlankImageError:
            failures.append(f"sample {position} (true {expected}): pipeline found no digit")
            continue

        got = result["prediction"]
        if got == expected:
            correct += 1
        else:
            failures.append(
                f"sample {position}: true {expected}, predicted {got} "
                f"({result['confidence']:.1f}%)"
            )

    accuracy = correct / samples if samples else 0.0
    print(f"End-to-end accuracy on rendered photos: {correct}/{samples} = {accuracy:.1%}")

    if failures:
        print("\nMismatches:")
        for line in failures:
            print(f"  {line}")

    if output_dir is not None:
        print(f"\nRendered images kept in: {output_dir}")

    # The pipeline is lossy by design (resize, threshold), so allow some slack;
    # anything below this means the preprocessing and the model disagree.
    passed = accuracy >= 0.80
    print("\nRESULT:", "PASS" if passed else "FAIL (expected >= 80%)")
    return 0 if passed else 1


def check_shapes() -> None:
    """Confirm the preprocessing contract independently of the model."""
    blank = np.full((64, 64, 3), 255, dtype=np.uint8)
    encoded, buffer = cv2.imencode(".png", blank)
    assert encoded
    try:
        preprocess_bytes(buffer.tobytes())
    except BlankImageError:
        print("Blank image correctly rejected.")
    else:
        raise AssertionError("A blank image should raise BlankImageError")

    square = np.full((64, 64, 3), 255, dtype=np.uint8)
    cv2.rectangle(square, (20, 10), (34, 50), (0, 0, 0), -1)
    encoded, buffer = cv2.imencode(".png", square)
    tensor = preprocess_bytes(buffer.tobytes())
    assert tensor.shape == (1, 28, 28, 1), tensor.shape
    assert tensor.dtype == np.float32, tensor.dtype
    assert 0.0 <= float(tensor.min()) and float(tensor.max()) <= 1.0
    # Ink must end up white on black, matching MNIST.
    assert float(tensor.max()) > 0.9, "expected white ink after preprocessing"
    print(f"Preprocessing contract OK: shape={tensor.shape}, dtype={tensor.dtype}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=25)
    parser.add_argument("--model", default=str(MODEL_PATH))
    parser.add_argument("--keep", action="store_true", help="Keep the rendered PNGs on disk")
    parser.add_argument("--seed", type=int, default=7)
    arguments = parser.parse_args()

    check_shapes()
    print()
    return run(arguments.samples, arguments.model, arguments.keep, arguments.seed)


if __name__ == "__main__":
    raise SystemExit(main())
