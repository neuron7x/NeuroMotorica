from __future__ import annotations
from fastapi import FastAPI, Query
from .db import get_db
from ..services.policy_service import PolicyService
from .schemas import OutcomeIn, PolicyRecommendations, Recommendation

app = FastAPI(title="NeuroMotorica Policy API", version="0.5.0")
svc = PolicyService(get_db())

@app.post("/policy/outcome")
def policy_outcome(inp: OutcomeIn) -> dict:
    svc.update_outcome(inp.user_id, inp.exercise_id, inp.cue_text, inp.success, inp.profile)
    return {"status": "ok"}

@app.get("/policy/best/{user_id}/{exercise_id}", response_model=PolicyRecommendations)
def policy_best(
    user_id: str,
    exercise_id: str,
    k: int = Query(3, ge=1, le=10),
    profile: str | None = Query(None, min_length=1),
):
    ranked = svc.topk(user_id, exercise_id, profile=profile, k=k)
    return PolicyRecommendations(
        user_id=user_id,
        exercise_id=exercise_id,
        recommendations=[Recommendation(cue=c, score=s) for c, s in ranked],
    )
