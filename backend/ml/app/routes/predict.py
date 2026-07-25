"""Prediction endpoints.

Both endpoints accept the two shapes the Node API can send (see
``backend/api/src/services/ml.service.js``):

* ``multipart/form-data`` with an ``image`` file part
* ``application/json`` with ``{"image": "<base64 or data URL>"}``

Raw ``image/*`` bodies are accepted too, which makes the service easy to curl.
"""

import logging

from fastapi import APIRouter, HTTPException, Request, status
# request.form() is a Starlette-level API and returns Starlette's UploadFile,
# not the fastapi.UploadFile subclass used by FastAPI's own File(...) params.
from starlette.datastructures import UploadFile

from app.config import MAX_UPLOAD_BYTES, MODEL_PATH
from app.schemas import ErrorResponse, HealthResponse, PredictionResponse
from app.services.predictor import ModelNotAvailableError, get_predictor
from preprocessing.image_processor import BlankImageError, PreprocessingError
from preprocessing.utils import decode_base64_image

logger = logging.getLogger(__name__)

router = APIRouter()

_FILE_FIELDS = ("image", "file", "drawing")

_PREDICT_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Missing or undecodable image"},
    413: {"model": ErrorResponse, "description": "Image larger than the upload limit"},
    422: {"model": ErrorResponse, "description": "No digit found in the image"},
    503: {"model": ErrorResponse, "description": "Trained model unavailable"},
}


@router.post(
    "/predict/image",
    response_model=PredictionResponse,
    responses=_PREDICT_RESPONSES,
    summary="Predict the digit in an uploaded image",
)
async def predict_image(request: Request) -> PredictionResponse:
    return await _predict(request)


@router.post(
    "/predict/drawing",
    response_model=PredictionResponse,
    responses=_PREDICT_RESPONSES,
    summary="Predict the digit in a canvas drawing",
)
async def predict_drawing(request: Request) -> PredictionResponse:
    return await _predict(request)


@router.get("/health", response_model=HealthResponse, summary="Service health")
async def health() -> HealthResponse:
    predictor = get_predictor()
    loaded = predictor.is_loaded
    return HealthResponse(
        status="ok" if loaded else "degraded",
        model_loaded=loaded,
        model_path=str(MODEL_PATH),
    )


async def _predict(request: Request) -> PredictionResponse:
    image_bytes = await _extract_image_bytes(request)

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit.",
        )

    try:
        return PredictionResponse(**get_predictor().predict_bytes(image_bytes))
    except BlankImageError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    except PreprocessingError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error
    except ModelNotAvailableError as error:
        logger.error("Model unavailable: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error


async def _extract_image_bytes(request: Request) -> bytes:
    """Pull the image out of whichever request shape the caller used."""
    content_type = (request.headers.get("content-type") or "").lower()

    if content_type.startswith("multipart/form-data"):
        return await _from_multipart(request)

    if content_type.startswith("application/json"):
        return _from_json(await _read_json(request))

    if content_type.startswith("image/"):
        body = await request.body()
        if body:
            return body

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Image file is required. Send multipart/form-data with an 'image' "
            "field, or JSON with a base64 'image' value."
        ),
    )


async def _from_multipart(request: Request) -> bytes:
    form = await request.form()
    try:
        for field in _FILE_FIELDS:
            value = form.get(field)
            if isinstance(value, UploadFile):
                data = await value.read()
                if data:
                    return data
            elif isinstance(value, str) and value.strip():
                # Some clients post the data URL as a plain text field.
                return _decode_base64_or_400(value)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file is required in the 'image' field.",
        )
    finally:
        await form.close()


async def _read_json(request: Request) -> dict:
    try:
        payload = await request.json()
    except (ValueError, UnicodeDecodeError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request body is not valid JSON."
        ) from error

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expected a JSON object with an 'image' field.",
        )
    return payload


def _from_json(payload: dict) -> bytes:
    for field in _FILE_FIELDS:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return _decode_base64_or_400(value)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Image is required as a base64 string in the 'image' field.",
    )


def _decode_base64_or_400(value: str) -> bytes:
    try:
        return decode_base64_image(value)
    except PreprocessingError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error
