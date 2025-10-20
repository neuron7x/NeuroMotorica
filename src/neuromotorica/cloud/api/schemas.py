from __future__ import annotations
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator


class OutcomeMetrics(RootModel[dict[str, float]]):
    """Container for arbitrary numeric outcome telemetry metrics."""

    model_config = ConfigDict(json_schema_extra={"example": {"twitch": 0.41, "snr": 18.2}})

    @field_validator("root")
    @classmethod
    def ensure_numeric(cls, value: dict[str, Any]) -> dict[str, float]:
        cleaned: dict[str, float] = {}
        for key, metric in value.items():
            if not isinstance(metric, (int, float)):
                raise TypeError("Metric values must be numeric.")
            if not key:
                raise ValueError("Metric names must be non-empty strings.")
            cleaned[key] = float(metric)
        return cleaned


class OutcomeIn(BaseModel):
    user_id: str = Field(..., min_length=1)
    exercise_id: str = Field(..., min_length=1)
    cue_text: str = Field(..., min_length=1)
    success: bool
    reps: int | None = Field(default=None, ge=1, description="Number of repetitions attempted.")
    metrics: OutcomeMetrics | None = Field(default=None, description="Telemetry metrics captured for the cue.")
    extended: bool = Field(default=False, description="Whether the extended simulation mode was active.")

class RankedCue(BaseModel):
    cue_text: str
    score: float
