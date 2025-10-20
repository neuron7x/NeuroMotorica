\
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from typing import Dict, Optional
from .schemas import SessionStartReq, SessionStartResp, SignalReq, PolicyOutcomeReq, SummaryReq, SummaryResp, Session
from ..core.nmj import NMJ
from ..policy.coach import UCB1

app = FastAPI(title="NeuroMotorica Universal API", version="1.0.0")

SESSIONS: Dict[str, Session] = {}
POLICY = UCB1(cues=["Faster", "Slower", "Full ROM", "Focus Breath", "Hold Top", "Explosive Up"])

@app.post("/v1/session/start", response_model=SessionStartResp)
def session_start(req: SessionStartReq) -> SessionStartResp:
    sid = f"sess-{len(SESSIONS)+1}"
    sess = Session(id=sid, exercise_id=req.exercise_id, dt=req.dt, nmj=NMJ(dt=req.dt))
    SESSIONS[sid] = sess
    return SessionStartResp(session_id=sid)

@app.post("/v1/session/{sid}/signal")
def session_signal(sid: str, req: SignalReq) -> Dict[str, float]:
    sess = SESSIONS.get(sid)
    if not sess:
        raise HTTPException(404, "session not found")
    y = sess.nmj.step(req.u)
    sess.outputs.append(y)
    return {"y": y}

@app.get("/v1/policy/best", response_model=SummaryResp.__annotations__.get('metrics', dict).__class__ if False else None)
def _type_hint_hack():  # keeps pydantic imports static for tools; not used at runtime
    pass

@app.get("/v1/policy/best")
def policy_best(session_id: Optional[str] = None, k: int = 3):
    cues = POLICY.select(k=k)
    return {"cues": cues}

@app.post("/v1/policy/outcome")
def policy_outcome(req: PolicyOutcomeReq):
    POLICY.update(req.cue_text, req.success)
    return {"status": "ok"}

@app.post("/v1/session/{sid}/summary", response_model=SummaryResp)
def session_summary(sid: str, req: SummaryReq) -> SummaryResp:
    sess = SESSIONS.get(sid)
    if not sess:
        raise HTTPException(404, "session not found")
    metrics = sess.nmj.metrics()
    return SummaryResp(metrics=metrics.__dict__)

def run() -> None:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
