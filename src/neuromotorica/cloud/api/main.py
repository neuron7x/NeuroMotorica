from __future__ import annotations

import logging
import os
from fastapi import FastAPI, Query

from .db import get_db
from ..services.policy_service import PolicyService
from .schemas import OutcomeIn, RankedCue

LOGGER = logging.getLogger(__name__)

FALSEY = {"0", "false", "no", "off"}
TRUTHY = {"1", "true", "yes", "on"}


def _flag_from_env(name: str) -> bool | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip().lower()
    if value in TRUTHY:
        return True
    if value in FALSEY:
        return False
    LOGGER.warning("Unrecognized value '%s' for %s; using default", value, name)
    return None


def _metrics_enabled() -> bool:
    disable_flag = _flag_from_env("NEUROMOTORICA_DISABLE_METRICS")
    if disable_flag is True:
        return False
    enable_flag = _flag_from_env("NEUROMOTORICA_ENABLE_METRICS")
    if enable_flag is not None:
        return enable_flag
    if disable_flag is False:
        return True
    return True


def _setup_metrics(app: FastAPI) -> None:
    if not _metrics_enabled():
        LOGGER.info("Prometheus metrics disabled via environment toggle")
        return
    if getattr(app.state, "_metrics_enabled", False):
        return
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
    except ImportError:  # pragma: no cover - dependency managed via pyproject
        LOGGER.debug("prometheus_fastapi_instrumentator not available; skipping metrics")
        return

    instrumentator = Instrumentator().instrument(app)
    instrumentator.expose(app, include_in_schema=False)
    app.state._metrics_enabled = True
    app.state.metrics_instrumentator = instrumentator
    LOGGER.info("Prometheus metrics instrumentation enabled at /metrics")

app = FastAPI(title="NeuroMotorica Policy API", version="0.5.0")
svc = PolicyService(get_db())

@app.post("/policy/outcome")
def policy_outcome(inp: OutcomeIn) -> dict:
    svc.update_outcome(inp.user_id, inp.exercise_id, inp.cue_text, inp.success)
    return {"status": "ok"}

@app.get("/policy/best/{user_id}/{exercise_id}", response_model=list[RankedCue])
def policy_best(user_id: str, exercise_id: str, k: int = Query(3, ge=1, le=10)):
    ranked = svc.topk(user_id, exercise_id, k=k)
    return [RankedCue(cue_text=c, score=s) for c, s in ranked]

_setup_metrics(app)
