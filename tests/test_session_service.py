from __future__ import annotations

from datetime import datetime, timezone

from neuromotorica.cloud.api.db import get_db
from neuromotorica.cloud.services.session_service import SessionService


def test_session_lifecycle() -> None:
    conn = get_db(":memory:")
    service = SessionService(conn)
    session = service.start_session("user", "squat", {"heart_rate": True}, metadata={"locale": "uk"})
    assert session.status == "active"

    now = datetime.now(timezone.utc)
    service.record_signal(session.id, now, emg=[0.1, 0.2], imu=None, hr=120)
    service.finalize_session(session.id, {"reps": 10, "tempo": 1.2})

    stored = service.get_session(session.id)
    assert stored is not None
    assert stored.status == "completed"
