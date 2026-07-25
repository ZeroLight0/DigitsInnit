"""Train the digit-recognition CNN on MNIST.

Run from the ``backend/ml`` directory:

    python -m training.train                 # 10 epochs, saves saved_models/mnist_cnn.keras
    python -m training.train --epochs 3      # quick run
    python -m training.train --augment       # enable train-time augmentation (slower on CPU)
"""

import argparse
import json
import logging
from pathlib import Path

from app.config import MODEL_PATH, SAVED_MODELS_DIR
from training.dataset import IMAGE_SIZE, NUM_CLASSES, load_mnist, to_model_input

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
logger = logging.getLogger("digitwise.train")


def build_model(learning_rate: float = 1e-3, augment: bool = True):
    """A small CNN that comfortably reaches ~99% MNIST test accuracy.

    Kept deliberately light (single conv per block, no BatchNorm) so it trains
    in a reasonable time on a CPU-only machine — this is the inference cost
    that matters for a service without a GPU, not just training cost.

    The augmentation layers live inside the model, which keeps ``fit`` simple and
    makes them automatic no-ops at inference time (``training=False``).
    """
    import keras
    from keras import layers

    inputs = keras.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 1), name="image")

    x = inputs
    if augment:
        # Real drawings are never as tidy as MNIST; small affine jitter buys a
        # lot of robustness on canvas and photo input.
        x = layers.RandomTranslation(0.1, 0.1, fill_mode="constant", name="jitter")(x)
        x = layers.RandomRotation(0.06, fill_mode="constant", name="rotate")(x)
        x = layers.RandomZoom(0.1, 0.1, fill_mode="constant", name="zoom")(x)

    x = layers.Conv2D(16, 3, padding="same", activation="relu")(x)
    x = layers.MaxPooling2D(2)(x)
    x = layers.Conv2D(32, 3, padding="same", activation="relu")(x)
    x = layers.MaxPooling2D(2)(x)
    x = layers.Dropout(0.25)(x)

    x = layers.Flatten()(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.4)(x)
    outputs = layers.Dense(NUM_CLASSES, activation="softmax", name="digit")(x)

    model = keras.Model(inputs, outputs, name="digitwise_cnn")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def train(
    epochs: int = 10,
    batch_size: int = 128,
    learning_rate: float = 1e-3,
    validation_split: float = 0.1,
    augment: bool = False,
    output_path: str | Path = MODEL_PATH,
    seed: int = 42,
):
    """Train, evaluate, and save the model. Returns ``(model, history, metrics)``."""
    import keras

    keras.utils.set_random_seed(seed)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    (x_train_raw, y_train), (x_test_raw, y_test) = load_mnist()
    x_train = to_model_input(x_train_raw)
    x_test = to_model_input(x_test_raw)
    logger.info("Train: %s  Test: %s", x_train.shape, x_test.shape)

    model = build_model(learning_rate=learning_rate, augment=augment)
    model.summary(print_fn=logger.info)

    callbacks = [
        keras.callbacks.ModelCheckpoint(
            filepath=str(output_path),
            monitor="val_accuracy",
            mode="max",
            save_best_only=True,
            verbose=1,
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            mode="max",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-5, verbose=1
        ),
    ]

    history = model.fit(
        x_train,
        y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=validation_split,
        callbacks=callbacks,
        verbose=1,
    )

    test_loss, test_accuracy = model.evaluate(x_test, y_test, verbose=0)
    logger.info("Test loss: %.4f", test_loss)
    logger.info("Test accuracy: %.4f", test_accuracy)

    # EarlyStopping restored the best weights, so re-save to be certain the file
    # on disk matches the model we just evaluated.
    model.save(output_path)
    logger.info("Model saved to: %s", output_path)

    metrics = {
        "test_loss": float(test_loss),
        "test_accuracy": float(test_accuracy),
        "epochs_run": len(history.history["loss"]),
        "epochs_requested": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "augmented": augment,
        "seed": seed,
        "train_samples": int(x_train.shape[0]),
        "test_samples": int(x_test.shape[0]),
        "model_path": str(output_path),
    }
    _write_json(SAVED_MODELS_DIR / "training_metrics.json", metrics)
    _write_json(
        SAVED_MODELS_DIR / "training_history.json",
        {key: [float(value) for value in values] for key, values in history.history.items()},
    )

    return model, history, metrics


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Wrote %s", path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--validation-split", type=float, default=0.1)
    parser.add_argument(
        "--augment",
        action="store_true",
        help="Train with random translation/rotation/zoom (more robust, much slower on CPU)",
    )
    parser.add_argument("--output", default=str(MODEL_PATH), help="Where to save the model")
    parser.add_argument("--seed", type=int, default=42)
    arguments = parser.parse_args()

    train(
        epochs=arguments.epochs,
        batch_size=arguments.batch_size,
        learning_rate=arguments.learning_rate,
        validation_split=arguments.validation_split,
        augment=arguments.augment,
        output_path=arguments.output,
        seed=arguments.seed,
    )


if __name__ == "__main__":
    main()
