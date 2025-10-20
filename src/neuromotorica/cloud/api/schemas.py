from __future__ import annotations

from datetime import datetime
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
    metrics: OutcomeMetrics | None = Field(
        default=None, description="Telemetry metrics captured for the cue."
    )
    extended: bool = Field(default=False, description="Whether the extended simulation mode was active.")


class RankedCue(BaseModel):
    cue_text: str
    score: float


class SensorCapabilities(BaseModel):
    heart_rate: bool = False
    imu: bool = False
    emg: bool = False


class SessionStartRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    exercise_id: str = Field(..., min_length=1)
    sensor_caps: SensorCapabilities
    metadata: dict[str, str] = Field(default_factory=dict)


class SessionStartResponse(BaseModel):
    session_id: str
    started_at: datetime


class SignalIn(BaseModel):
    ts: datetime
    emg: list[float] | None = None
    imu: list[float] | None = None
    hr: int | None = Field(default=None, ge=0, le=255)


class SessionSummaryIn(BaseModel):
    metrics: dict[str, float]


class SessionSummaryOut(BaseModel):
    session_id: str
    status: str
    metrics: dict[str, float]


class ReplicaSyncRecord(BaseModel):
    id: str = Field(..., min_length=1)
    version: int = Field(..., ge=0)
    payload: Any


class ReplicaSyncIn(BaseModel):
    batch: list[ReplicaSyncRecord] = Field(default_factory=list)


class ReplicaSyncOut(BaseModel):
    status: str
    synced: int
