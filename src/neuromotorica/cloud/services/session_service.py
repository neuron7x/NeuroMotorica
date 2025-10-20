from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Sequence


@dataclass(slots=True)
class SessionRecord:
    id: str
    user_id: str
    exercise_id: str
    sensor_caps: Mapping[str, bool]
    started_at: datetime
    status: str


class SessionService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def start_session(
        self,
        user_id: str,
        exercise_id: str,
        sensor_caps: Mapping[str, bool],
        metadata: Mapping[str, str] | None = None,
    ) -> SessionRecord:
        session_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions(id, user_id, exercise_id, started_at, sensor_caps, metadata, status)
            VALUES(?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                session_id,
                user_id,
                exercise_id,
                started_at.isoformat(),
                json.dumps(dict(sensor_caps)),
                json.dumps(dict(metadata or {})),
            ),
        )
        self.conn.commit()
        return SessionRecord(
            id=session_id,
            user_id=user_id,
            exercise_id=exercise_id,
            sensor_caps=dict(sensor_caps),
            started_at=started_at,
            status="active",
        )

    def record_signal(
        self,
        session_id: str,
        timestamp: datetime,
        emg: Sequence[float] | None,
        imu: Sequence[float] | None,
        hr: int | None,
    ) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO session_signals(session_id, ts, emg, imu, hr)
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                session_id,
                timestamp.isoformat(),
                json.dumps(list(emg)) if emg is not None else None,
                json.dumps(list(imu)) if imu is not None else None,
                hr,
            ),
        )
        self.conn.commit()

    def finalize_session(self, session_id: str, metrics: Mapping[str, float]) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO session_summaries(session_id, metrics, completed_at)
            VALUES(?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET metrics=excluded.metrics, completed_at=excluded.completed_at
            """,
            (session_id, json.dumps(dict(metrics)), datetime.now(timezone.utc).isoformat()),
        )
        cursor.execute(
            """
            UPDATE sessions SET status='completed', completed_at=? WHERE id=?
            """,
            (datetime.now(timezone.utc).isoformat(), session_id),
        )
        self.conn.commit()

    def get_session(self, session_id: str) -> SessionRecord | None:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, user_id, exercise_id, sensor_caps, started_at, status FROM sessions WHERE id=?",
            (session_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return SessionRecord(
            id=row[0],
            user_id=row[1],
            exercise_id=row[2],
            sensor_caps=json.loads(row[3]),
            started_at=datetime.fromisoformat(row[4]),
            status=row[5],
        )

