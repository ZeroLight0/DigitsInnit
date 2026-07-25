"""FastAPI entrypoint for the DigitWise ML service.

Run from the ``backend/ml`` directory so that both the ``app`` and
``preprocessing`` packages are importable:

    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, MODEL_PATH, PRELOAD_MODEL
from app.routes.predict import router as predict_router
from app.services.predictor import ModelNotAvailableError, get_predictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("digitwise.ml")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Warm the model at startup so the first request is not the slow one."""
    if PRELOAD_MODEL:
        try:
            get_predictor().load()
        except ModelNotAvailableError as error:
            # Start anyway: /health reports the problem and predictions return
            # 503, which beats a container that refuses to boot.
            logger.warning("Starting without a model. %s", error)
    else:
        logger.info("Model preloading disabled; loading on first request.")

    yield


app = FastAPI(
    title="DigitWise ML Service",
    description="Handwritten digit recognition over a CNN trained on MNIST.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # Credentialed requests cannot use a wildcard origin; the browser rejects it.
    allow_credentials=CORS_ORIGINS != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)


@app.get("/", summary="Service metadata")
async def root() -> dict:
    predictor = get_predictor()
    return {
        "service": "DigitWise ML Service",
        "version": app.version,
        "model_loaded": predictor.is_loaded,
        "model_path": str(MODEL_PATH),
        "endpoints": ["/predict/image", "/predict/drawing", "/health", "/docs"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
