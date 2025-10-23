from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from ..core.nmj import NMJ, SimulationMetrics


class SessionStartReq(BaseModel):
    exercise_id: str = Field(..., min_length=1)
    dt: float = Field(0.01, gt=0.0, le=0.1)


class SessionStartResp(BaseModel):
    session_id: str


class SignalReq(BaseModel):
    u: float = Field(..., ge=0.0, le=1.0)


class SignalResp(BaseModel):
    y: float


class BestCueResp(BaseModel):
    cues: list[str]


class PolicyOutcomeReq(BaseModel):
    cue_text: str
    success: float = Field(..., ge=0.0, le=1.0)


class PolicyOutcomeResp(BaseModel):
    status: Literal["ok"] = "ok"


class SummaryReq(BaseModel):
    pass


class SummaryResp(BaseModel):
    metrics: SimulationMetrics


@dataclass
class Session:
    id: str
    exercise_id: str
    dt: float
    nmj: NMJ
    outputs: list[float] = field(default_factory=list)
