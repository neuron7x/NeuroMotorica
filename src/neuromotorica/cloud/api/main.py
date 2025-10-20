from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, Query, status

from .db import get_db
from .schemas import (
    OutcomeIn,
    RankedCue,
    SessionStartRequest,
    SessionStartResponse,
    SessionSummaryIn,
    SessionSummaryOut,
    SignalIn,
)
from ..services.policy_service import PolicyService
from ..services.session_service import SessionService


app = FastAPI(title="NeuroMotorica Cloud API", version="0.7.0")


@lru_cache()
def _db():  # pragma: no cover - thin wrapper
    return get_db()


def _policy_service() -> PolicyService:
    return PolicyService(_db())


def _session_service() -> SessionService:
    return SessionService(_db())


@app.post("/v1/policy/outcome")
def policy_outcome(inp: OutcomeIn, svc: PolicyService = Depends(_policy_service)) -> dict:
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


@app.get("/v1/policy/best", response_model=list[RankedCue])
def policy_best(
    user_id: str,
    exercise_id: str,
    k: int = Query(3, ge=1, le=10),
    svc: PolicyService = Depends(_policy_service),
):
    ranked = svc.topk(user_id, exercise_id, k=k)
    return [RankedCue(cue_text=c, score=s) for c, s in ranked]


@app.post("/policy/outcome")
def policy_outcome_legacy(inp: OutcomeIn, svc: PolicyService = Depends(_policy_service)) -> dict:
    return policy_outcome(inp, svc)


@app.get("/policy/best/{user_id}/{exercise_id}", response_model=list[RankedCue])
def policy_best_legacy(
    user_id: str,
    exercise_id: str,
    k: int = Query(3, ge=1, le=10),
    svc: PolicyService = Depends(_policy_service),
):
    return policy_best(user_id, exercise_id, k, svc)


@app.post("/v1/session/start", response_model=SessionStartResponse)
def start_session(
    payload: SessionStartRequest,
    svc: SessionService = Depends(_session_service),
):
    record = svc.start_session(
        payload.user_id,
        payload.exercise_id,
        payload.sensor_caps.model_dump(),
        metadata=payload.metadata,
    )
    return SessionStartResponse(session_id=record.id, started_at=record.started_at)


@app.post("/v1/session/{session_id}/signal", status_code=status.HTTP_202_ACCEPTED)
def ingest_signal(
    session_id: str,
    payload: SignalIn,
    svc: SessionService = Depends(_session_service),
):
    if svc.get_session(session_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    svc.record_signal(session_id, payload.ts, payload.emg, payload.imu, payload.hr)
    return {"status": "accepted"}


@app.post("/v1/session/{session_id}/summary", response_model=SessionSummaryOut)
def finalize_session(
    session_id: str,
    payload: SessionSummaryIn,
    svc: SessionService = Depends(_session_service),
):
    session = svc.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    svc.finalize_session(session_id, payload.metrics)
    return SessionSummaryOut(session_id=session_id, status="completed", metrics=payload.metrics)

