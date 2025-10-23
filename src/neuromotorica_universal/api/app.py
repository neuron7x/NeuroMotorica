from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException

from .schemas import (
    BestCueResp,
    PolicyOutcomeReq,
    PolicyOutcomeResp,
    Session,
    SessionStartReq,
    SessionStartResp,
    SignalReq,
    SignalResp,
    SummaryReq,
    SummaryResp,
)
from ..core.nmj import NMJ
from ..policy.coach import UCB1

app = FastAPI(title="NeuroMotorica Universal API", version="1.0.0")

SESSIONS: dict[str, Session] = {}
POLICY = UCB1(cues=["Faster", "Slower", "Full ROM", "Focus Breath", "Hold Top", "Explosive Up"])


@app.post("/v1/session/start", response_model=SessionStartResp)
def session_start(req: SessionStartReq) -> SessionStartResp:
    sid = f"sess-{len(SESSIONS) + 1}"
    session = Session(id=sid, exercise_id=req.exercise_id, dt=req.dt, nmj=NMJ(dt=req.dt))
    SESSIONS[sid] = session
    return SessionStartResp(session_id=sid)


@app.post("/v1/session/{sid}/signal", response_model=SignalResp)
def session_signal(sid: str, req: SignalReq) -> SignalResp:
    session = SESSIONS.get(sid)
    if session is None:
        raise HTTPException(404, "session not found")
    y = session.nmj.step(req.u)
    session.outputs.append(y)
    return SignalResp(y=y)


@app.get("/v1/policy/best", response_model=BestCueResp)
def policy_best(session_id: Optional[str] = None, k: int = 3) -> BestCueResp:
    if session_id is not None and session_id not in SESSIONS:
        raise HTTPException(404, "session not found")
    cues = POLICY.select(k=k)
    return BestCueResp(cues=cues)


@app.post("/v1/policy/outcome", response_model=PolicyOutcomeResp)
def policy_outcome(req: PolicyOutcomeReq) -> PolicyOutcomeResp:
    POLICY.update(req.cue_text, req.success)
    return PolicyOutcomeResp()


@app.post("/v1/session/{sid}/summary", response_model=SummaryResp)
def session_summary(sid: str, req: SummaryReq) -> SummaryResp:
    session = SESSIONS.get(sid)
    if session is None:
        raise HTTPException(404, "session not found")
    metrics = session.nmj.metrics()
    return SummaryResp(metrics=metrics)


def run() -> None:  # pragma: no cover - convenience entry point
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
