from __future__ import annotations
from fastapi import FastAPI, Query

from .db import get_db
from ..services.policy_service import PolicyService
from .schemas import OutcomeIn, RankedCue

app = FastAPI(title="NeuroMotorica Policy API", version="0.5.0")
svc = PolicyService(get_db())

@app.post("/policy/outcome")
def policy_outcome(inp: OutcomeIn) -> dict:
    metrics_payload = inp.metrics.root if inp.metrics is not None else None
    outcome = svc.update_outcome(
        inp.user_id,
        inp.exercise_id,
        inp.cue_text,
        inp.success,
        reps=inp.reps,
        metrics=metrics_payload,
        extended=inp.extended,
    )
    return {"status": "ok", "outcome": outcome}

@app.get("/policy/best/{user_id}/{exercise_id}", response_model=list[RankedCue])
def policy_best(user_id: str, exercise_id: str, k: int = Query(3, ge=1, le=10)):
    ranked = svc.topk(user_id, exercise_id, k=k)
    return [RankedCue(cue_text=c, score=s) for c, s in ranked]
