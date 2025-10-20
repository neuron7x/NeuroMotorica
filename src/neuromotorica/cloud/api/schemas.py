from __future__ import annotations
from pydantic import BaseModel, Field

class OutcomeIn(BaseModel):
    user_id: str = Field(..., min_length=1)
    exercise_id: str = Field(..., min_length=1)
    cue_text: str = Field(..., min_length=1)
    success: bool

class RankedCue(BaseModel):
    cue_text: str
    score: float
