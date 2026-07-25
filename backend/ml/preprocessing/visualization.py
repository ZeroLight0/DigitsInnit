"""Visualise the preprocessing pipeline stage by stage.

Run it directly to inspect why an image predicts badly:

    python -m preprocessing.visualization path/to/digit.png
"""

import argparse
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np

from preprocessing.image_processor import PreprocessingError, preprocessing_stages
from preprocessing.utils import ensure_image_path

_STAGES = [
    ("Original", "original"),
    ("Grayscale", "gray"),
    ("Denoised", "denoised"),
    ("Binarised", "binary"),
    ("Despeckled", "cleaned"),
    ("Cropped", "cropped"),
    ("Fitted 20px", "fitted"),
    ("Padded 28x28", "padded"),
    ("Mass-centred", "centered"),
]


def visualize_pipeline(image_path: str | Path, save_to: str | Path | None = None) -> None:
    """Display (or save) each preprocessing stage for a single image."""
    path = ensure_image_path(image_path)

    # Decode from bytes rather than cv2.imread so non-ASCII paths work on Windows.
    buffer = np.frombuffer(path.read_bytes(), dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise PreprocessingError(f"Could not load image: {path}")

    stages = preprocessing_stages(image)

    figure, axes = plt.subplots(1, len(_STAGES), figsize=(2.1 * len(_STAGES), 3))
    for axis, (title, key) in zip(axes, _STAGES):
        frame = stages[key]
        if frame.ndim == 2:
            axis.imshow(frame, cmap="gray", vmin=0, vmax=255)
        else:
            axis.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        axis.set_title(f"{title}\n{frame.shape[1]}x{frame.shape[0]}", fontsize=8)
        axis.axis("off")

    figure.suptitle(f"Preprocessing: {path.name}", fontsize=11)
    figure.tight_layout()

    if save_to is not None:
        target = Path(save_to)
        target.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(target, dpi=140, bbox_inches="tight")
        print(f"Saved pipeline figure to: {target}")
        plt.close(figure)
    else:
        plt.show()

    print("Final tensor shape:", stages["tensor"].shape)
    print(
        "Final tensor range: "
        f"[{stages['tensor'].min():.3f}, {stages['tensor'].max():.3f}]"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="Path to a digit image")
    parser.add_argument(
        "--save-to",
        default=None,
        help="Write the figure to this path instead of opening a window",
    )
    arguments = parser.parse_args()
    visualize_pipeline(arguments.image, arguments.save_to)


if __name__ == "__main__":
    main()
