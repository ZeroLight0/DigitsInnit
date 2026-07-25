# DigitWise — ML Service

Handwritten digit recognition. A CNN trained on MNIST is served over FastAPI and
consumed by the Node API (`backend/api`), which the React frontend calls.

```
frontend  ──▶  backend/api (Express, :5000)  ──▶  backend/ml (FastAPI, :8000)  ──▶  mnist_cnn.keras
```

## Layout

| Path | Purpose |
| --- | --- |
| `app/main.py` | FastAPI app, CORS, startup model preload |
| `app/config.py` | Paths and limits, all overridable by env var |
| `app/routes/predict.py` | `/predict/image`, `/predict/drawing`, `/health` |
| `app/services/predictor.py` | Loads the model once, runs inference |
| `app/schemas.py` | Response contract shared with the frontend |
| `preprocessing/image_processor.py` | **The** image pipeline (used by API *and* training) |
| `preprocessing/utils.py` | Path validation, base64 / data-URL decoding |
| `preprocessing/visualization.py` | Plot every preprocessing stage for one image |
| `training/dataset.py` | MNIST loading, cached in `datasets/mnist.npz` |
| `training/train.py` | Build, train, and save the CNN |
| `training/evaluate.py` | Test-set report, confusion matrix, single-image check |
| `training/visualize.py` | Learning curves, sample predictions, mistakes |
| `scripts/smoke_test.py` | End-to-end check on synthetic "photos" of digits |

## Setup

From `backend/ml`:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
python -m pip install -r requirements.txt
```

## Train the model

The service needs `saved_models/mnist_cnn.keras`. Create it:

```bash
python -m training.train             # ~15 epochs, ~99.4% test accuracy
python -m training.train --epochs 3  # fast run for a working demo
```

Writes `saved_models/mnist_cnn.keras`, `training_metrics.json`, and
`training_history.json`. MNIST is downloaded once and cached to
`datasets/mnist.npz`.

## Run the service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
# or: python -m app.main
```

Interactive docs at <http://localhost:8000/docs>.

> Run uvicorn from `backend/ml` — both `app` and `preprocessing` are imported as
> top-level packages.

## Verify

```bash
python -m scripts.smoke_test          # decode -> preprocess -> predict, end to end
python -m training.evaluate           # MNIST test-set report + confusion matrix
python -m training.evaluate --image path/to/digit.png
python -m training.visualize          # figures into reports/
python -m preprocessing.visualization path/to/digit.png --save-to reports/stages.png
```

## API

### `POST /predict/image` · `POST /predict/drawing`

Both accept either shape, because the Node API sends multipart for file uploads
and JSON base64 for canvas drawings:

```bash
curl -F "image=@digit.png" http://localhost:8000/predict/image

curl -H "Content-Type: application/json" \
     -d '{"image":"data:image/png;base64,iVBORw0..."}' \
     http://localhost:8000/predict/drawing
```

Response:

```json
{
  "prediction": 7,
  "confidence": 99.42,
  "probabilities": { "0": 0.01, "1": 0.02, "7": 99.42, "...": 0.0 }
}
```

`prediction` and `confidence` are the fields the frontend reads
(`frontend/src/lib/predict-api.ts`) — don't rename them.

| Status | Meaning |
| --- | --- |
| 400 | No image sent, or the image/base64 could not be decoded |
| 413 | Larger than the upload limit (5 MB) |
| 422 | Decoded fine, but no digit was found (blank canvas) |
| 503 | `saved_models/mnist_cnn.keras` is missing — train it |

### `GET /health`

```json
{ "status": "ok", "model_loaded": true, "model_path": "...\\saved_models\\mnist_cnn.keras" }
```

`status` is `degraded` when the model has not loaded.

## Preprocessing

Model accuracy on real input depends almost entirely on this pipeline, so
training and serving deliberately share one module:

1. decode with the alpha channel intact, then flatten transparency onto white
2. grayscale, Gaussian blur
3. Otsu threshold with **automatic polarity detection** — the ink always ends up
   white on black, whether the source was dark-on-light or light-on-dark
4. drop speckle noise via connected components (broken strokes survive)
5. crop to the ink bounding box
6. scale the longest side to 20 px, preserving aspect ratio
7. paste into a 28×28 canvas
8. translate so the centre of mass is the canvas centre
9. scale to `[0, 1]`, reshape to `(1, 28, 28, 1)`

Steps 5–8 are how the original MNIST digits were normalised; skipping them is the
usual reason a 99%-accurate model fails on user drawings.

## Configuration

| Variable | Default |
| --- | --- |
| `DIGITWISE_MODEL_PATH` | `saved_models/mnist_cnn.keras` |
| `DIGITWISE_SAVED_MODELS_DIR` | `saved_models/` |
| `DIGITWISE_DATASETS_DIR` | `datasets/` |
| `DIGITWISE_REPORTS_DIR` | `reports/` |
| `DIGITWISE_MAX_UPLOAD_BYTES` | `5242880` (5 MB) |
| `DIGITWISE_PRELOAD_MODEL` | `1` |
| `DIGITWISE_CORS_ORIGINS` | `*` (comma-separated list) |

The Node API finds this service via `ML_SERVICE_URL` in `backend/api/.env`
(default `http://localhost:8000`).
