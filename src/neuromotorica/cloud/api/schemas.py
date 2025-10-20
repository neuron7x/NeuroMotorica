from __future__ import annotations
from pydantic import BaseModel, Field

class OutcomeIn(BaseModel):
    user_id: str = Field(..., min_length=1)
    exercise_id: str = Field(..., min_length=1)
    cue_text: str = Field(..., min_length=1)
    success: bool
    profile: str | None = Field(None, min_length=1)

class Recommendation(BaseModel):
    cue: str
    score: float


class PolicyRecommendations(BaseModel):
    user_id: str
    exercise_id: str
    recommendations: list[Recommendation]
