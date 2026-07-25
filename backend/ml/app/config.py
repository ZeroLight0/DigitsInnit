"""Runtime configuration for the DigitWise ML service."""

import os
from pathlib import Path

# .../backend/ml
ML_ROOT = Path(__file__).resolve().parent.parent

SAVED_MODELS_DIR = Path(
    os.getenv("DIGITWISE_SAVED_MODELS_DIR", ML_ROOT / "saved_models")
).resolve()

MODEL_FILENAME = os.getenv("DIGITWISE_MODEL_FILENAME", "mnist_cnn.keras")

MODEL_PATH = Path(os.getenv("DIGITWISE_MODEL_PATH", SAVED_MODELS_DIR / MODEL_FILENAME))

DATASETS_DIR = Path(os.getenv("DIGITWISE_DATASETS_DIR", ML_ROOT / "datasets")).resolve()

REPORTS_DIR = Path(os.getenv("DIGITWISE_REPORTS_DIR", ML_ROOT / "reports")).resolve()

# The Node API already caps uploads at 5 MB; mirror that here so the ML service
# is safe to expose on its own.
MAX_UPLOAD_BYTES = int(os.getenv("DIGITWISE_MAX_UPLOAD_BYTES", 5 * 1024 * 1024))

# Load the model during startup instead of on the first request.
PRELOAD_MODEL = os.getenv("DIGITWISE_PRELOAD_MODEL", "1").lower() not in {
    "0",
    "false",
    "no",
}

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("DIGITWISE_CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
