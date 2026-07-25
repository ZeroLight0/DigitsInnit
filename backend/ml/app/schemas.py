"""Response models for the ML service.

The frontend reads ``prediction`` and ``confidence`` (see
``frontend/src/lib/predict-api.ts``), and the Node API forwards this object
verbatim, so those two field names are part of the contract.
"""

from pydantic import BaseModel, ConfigDict, Field


class PredictionResponse(BaseModel):
    prediction: int = Field(..., ge=0, le=9, description="Predicted digit, 0-9")
    confidence: float = Field(
        ..., ge=0, le=100, description="Confidence for the predicted digit, in percent"
    )
    probabilities: dict[str, float] = Field(
        default_factory=dict,
        description="Confidence in percent for every digit, keyed by digit",
    )


class HealthResponse(BaseModel):
    # ``model_*`` collides with pydantic's protected namespace; these names are
    # part of the health payload, so opt out of the warning instead of renaming.
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_loaded: bool
    model_path: str


class ErrorResponse(BaseModel):
    detail: str
