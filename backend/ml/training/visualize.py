"""Figures for the trained model: learning curves and sample predictions.

Run from the ``backend/ml`` directory:

    python -m training.visualize
"""

import argparse
import json
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Write PNGs; no interactive display required.
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from app.config import MODEL_PATH, REPORTS_DIR, SAVED_MODELS_DIR  # noqa: E402
from training.dataset import load_mnist, to_model_input  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
logger = logging.getLogger("digitwise.visualize")

HISTORY_PATH = SAVED_MODELS_DIR / "training_history.json"


def plot_training_curves(history_path: str | Path = HISTORY_PATH) -> Path | None:
    """Plot accuracy and loss per epoch from the saved training history."""
    path = Path(history_path)
    if not path.exists():
        logger.warning("No training history at %s; run `python -m training.train` first.", path)
        return None

    history = json.loads(path.read_text(encoding="utf-8"))
    epochs = range(1, len(history.get("loss", [])) + 1)

    figure, (accuracy_axis, loss_axis) = plt.subplots(1, 2, figsize=(11, 4))

    for key, label in (("accuracy", "train"), ("val_accuracy", "validation")):
        if key in history:
            accuracy_axis.plot(epochs, history[key], marker="o", markersize=3, label=label)
    accuracy_axis.set_title("Accuracy")
    accuracy_axis.set_xlabel("Epoch")
    accuracy_axis.set_ylabel("Accuracy")
    accuracy_axis.grid(alpha=0.3)
    accuracy_axis.legend()

    for key, label in (("loss", "train"), ("val_loss", "validation")):
        if key in history:
            loss_axis.plot(epochs, history[key], marker="o", markersize=3, label=label)
    loss_axis.set_title("Loss")
    loss_axis.set_xlabel("Epoch")
    loss_axis.set_ylabel("Loss")
    loss_axis.grid(alpha=0.3)
    loss_axis.legend()

    figure.suptitle("DigitWise CNN training")
    figure.tight_layout()
    return _save(figure, "training_curves.png")


def plot_sample_predictions(
    model_path: str | Path = MODEL_PATH,
    count: int = 24,
    only_mistakes: bool = False,
    seed: int = 0,
) -> Path | None:
    """Grid of test digits with the predicted label and confidence."""
    path = Path(model_path)
    if not path.exists():
        logger.warning("No model at %s; run `python -m training.train` first.", path)
        return None

    import keras

    model = keras.models.load_model(path)
    (_, _), (x_test_raw, y_test) = load_mnist()
    probabilities = model.predict(to_model_input(x_test_raw), batch_size=256, verbose=0)
    predictions = probabilities.argmax(axis=1)
    confidences = probabilities.max(axis=1)

    if only_mistakes:
        pool = np.flatnonzero(predictions != y_test)
        if pool.size == 0:
            logger.info("No misclassifications to plot.")
            return None
        # Highest-confidence errors are the ones worth looking at.
        indices = pool[np.argsort(-confidences[pool])][:count]
    else:
        indices = np.random.default_rng(seed).choice(len(y_test), size=count, replace=False)

    columns = 6
    rows = int(np.ceil(len(indices) / columns))
    figure, axes = plt.subplots(rows, columns, figsize=(1.7 * columns, 2.0 * rows))
    for axis, index in zip(np.ravel(axes), indices):
        axis.imshow(x_test_raw[index], cmap="gray", vmin=0, vmax=255)
        correct = predictions[index] == y_test[index]
        axis.set_title(
            f"pred {predictions[index]} ({confidences[index] * 100:.1f}%)\ntrue {y_test[index]}",
            fontsize=8,
            color="green" if correct else "red",
        )
        axis.axis("off")
    for axis in np.ravel(axes)[len(indices) :]:
        axis.axis("off")

    figure.suptitle("Misclassified test digits" if only_mistakes else "Sample test predictions")
    figure.tight_layout()
    return _save(figure, "mistakes.png" if only_mistakes else "sample_predictions.png")


def _save(figure, filename: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    target = REPORTS_DIR / filename
    figure.savefig(target, dpi=140, bbox_inches="tight")
    plt.close(figure)
    logger.info("Wrote %s", target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=str(MODEL_PATH))
    parser.add_argument("--history", default=str(HISTORY_PATH))
    parser.add_argument("--samples", type=int, default=24)
    arguments = parser.parse_args()

    plot_training_curves(arguments.history)
    plot_sample_predictions(arguments.model, arguments.samples)
    plot_sample_predictions(arguments.model, arguments.samples, only_mistakes=True)


if __name__ == "__main__":
    main()
