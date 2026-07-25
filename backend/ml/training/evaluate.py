"""Evaluate the trained model.

Run from the ``backend/ml`` directory:

    python -m training.evaluate                        # full MNIST test-set report
    python -m training.evaluate --image path/to/5.png  # end-to-end single image
"""

import argparse
import json
import logging
from pathlib import Path

import numpy as np

from app.config import MODEL_PATH, REPORTS_DIR, SAVED_MODELS_DIR
from app.services.predictor import DigitPredictor
from training.dataset import NUM_CLASSES, load_mnist, to_model_input

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
logger = logging.getLogger("digitwise.evaluate")


def evaluate_model(model_path: str | Path = MODEL_PATH, batch_size: int = 256) -> dict:
    """Score the model on the MNIST test set and write a report."""
    import keras
    from sklearn.metrics import classification_report, confusion_matrix

    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained model not found at {model_path}. Run `python -m training.train` first."
        )

    model = keras.models.load_model(model_path)
    (_, _), (x_test_raw, y_test) = load_mnist()
    x_test = to_model_input(x_test_raw)

    loss, accuracy = model.evaluate(x_test, y_test, batch_size=batch_size, verbose=0)
    probabilities = model.predict(x_test, batch_size=batch_size, verbose=0)
    predictions = probabilities.argmax(axis=1)
    confidences = probabilities.max(axis=1)

    matrix = confusion_matrix(y_test, predictions, labels=list(range(NUM_CLASSES)))
    report = classification_report(
        y_test, predictions, digits=4, labels=list(range(NUM_CLASSES)), zero_division=0
    )
    per_class = {
        str(digit): float(matrix[digit, digit] / max(1, matrix[digit].sum()))
        for digit in range(NUM_CLASSES)
    }

    wrong = np.flatnonzero(predictions != y_test)
    # Most confident mistakes first — those are the informative failures.
    worst = wrong[np.argsort(-confidences[wrong])][:15]

    logger.info("Test loss:     %.4f", loss)
    logger.info("Test accuracy: %.4f (%d/%d correct)", accuracy, len(y_test) - len(wrong), len(y_test))
    logger.info("Mean confidence: %.2f%%", float(confidences.mean()) * 100)
    print("\nPer-class report:\n" + report)
    print("Confusion matrix (rows = true, cols = predicted):")
    print(matrix)

    if worst.size:
        print("\nMost confident mistakes:")
        for index in worst:
            print(
                f"  index {int(index):>5}  true {int(y_test[index])}  "
                f"predicted {int(predictions[index])}  "
                f"confidence {float(confidences[index]) * 100:.2f}%"
            )

    results = {
        "model_path": str(model_path),
        "test_loss": float(loss),
        "test_accuracy": float(accuracy),
        "mean_confidence": float(confidences.mean()),
        "misclassified": int(wrong.size),
        "per_class_accuracy": per_class,
        "confusion_matrix": matrix.tolist(),
        "worst_mistakes": [
            {
                "index": int(index),
                "true": int(y_test[index]),
                "predicted": int(predictions[index]),
                "confidence": float(confidences[index]),
            }
            for index in worst
        ],
    }

    report_path = SAVED_MODELS_DIR / "evaluation_metrics.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info("Wrote %s", report_path)

    _save_confusion_matrix(matrix)

    return results


def evaluate_image(image_path: str | Path, model_path: str | Path = MODEL_PATH) -> dict:
    """Run one image through the exact pipeline the API uses."""
    predictor = DigitPredictor(model_path)
    result = predictor.predict_image(image_path)

    print(f"Image:      {image_path}")
    print(f"Prediction: {result['prediction']}")
    print(f"Confidence: {result['confidence']:.2f}%")
    print("All digits:")
    for digit, score in sorted(
        result["probabilities"].items(), key=lambda item: -item[1]
    ):
        print(f"  {digit}: {score:6.2f}%")

    return result


def _save_confusion_matrix(matrix: np.ndarray) -> None:
    import matplotlib

    matplotlib.use("Agg")  # No display needed when running from a terminal.
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(6.5, 5.5))
    image = axis.imshow(matrix, cmap="Blues")
    axis.set_xlabel("Predicted digit")
    axis.set_ylabel("True digit")
    axis.set_title("MNIST test-set confusion matrix")
    axis.set_xticks(range(NUM_CLASSES))
    axis.set_yticks(range(NUM_CLASSES))
    figure.colorbar(image, ax=axis, shrink=0.85)

    peak = matrix.max()
    for row in range(NUM_CLASSES):
        for column in range(NUM_CLASSES):
            count = int(matrix[row, column])
            if count:
                axis.text(
                    column,
                    row,
                    count,
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if count > peak / 2 else "black",
                )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    target = REPORTS_DIR / "confusion_matrix.png"
    figure.tight_layout()
    figure.savefig(target, dpi=140)
    plt.close(figure)
    logger.info("Wrote %s", target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=str(MODEL_PATH), help="Path to the .keras model")
    parser.add_argument(
        "--image", default=None, help="Evaluate a single image instead of the test set"
    )
    parser.add_argument("--batch-size", type=int, default=256)
    arguments = parser.parse_args()

    if arguments.image:
        evaluate_image(arguments.image, arguments.model)
    else:
        evaluate_model(arguments.model, arguments.batch_size)


if __name__ == "__main__":
    main()
