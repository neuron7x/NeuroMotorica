from __future__ import annotations

import json
from collections.abc import Mapping
import sqlite3
from typing import Any


class PolicyService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def update_outcome(
        self,
        user_id: str,
        exercise_id: str,
        cue_text: str,
        success: bool,
        *,
        reps: int | None = None,
        metrics: Mapping[str, float] | None = None,
        extended: bool | None = None,
    ) -> dict[str, Any]:
        cur = self.conn.cursor()
        metrics_json = json.dumps(dict(metrics)) if metrics is not None else None
        extended_flag: int | None = None if extended is None else int(extended)
        cur.execute(
            """
            INSERT INTO cue_stats(user_id, exercise_id, cue_text, success, failure, reps, metrics, extended)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, exercise_id, cue_text) DO UPDATE SET
              success = cue_stats.success + excluded.success,
              failure = cue_stats.failure + excluded.failure,
              reps = COALESCE(excluded.reps, cue_stats.reps),
              metrics = COALESCE(excluded.metrics, cue_stats.metrics),
              extended = CASE
                  WHEN excluded.extended IS NULL THEN cue_stats.extended
                  ELSE excluded.extended
              END
        """,
            (
                user_id,
                exercise_id,
                cue_text,
                1 if success else 0,
                0 if success else 1,
                reps,
                metrics_json,
                extended_flag,
            ),
        )
        self.conn.commit()
        return self.get_outcome(user_id, exercise_id, cue_text)

    def topk(self, user_id: str, exercise_id: str, k: int = 3):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT cue_text, success, failure FROM cue_stats
            WHERE user_id=? AND exercise_id=?
        """, (user_id, exercise_id))
        rows = cur.fetchall()
        ranked = [(r[0], (r[1] + 1) / (r[1] + r[2] + 2)) for r in rows]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:k]

    def get_outcome(self, user_id: str, exercise_id: str, cue_text: str) -> dict[str, Any] | None:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT user_id, exercise_id, cue_text, success, failure, reps, metrics, extended
            FROM cue_stats
            WHERE user_id=? AND exercise_id=? AND cue_text=?
        """,
            (user_id, exercise_id, cue_text),
        )
        row = cur.fetchone()
        if row is None:
            return None
        metrics_payload = json.loads(row[6]) if row[6] else None
        extended_flag = bool(row[7]) if row[7] is not None else False
        return {
            "user_id": row[0],
            "exercise_id": row[1],
            "cue_text": row[2],
            "success": row[3],
            "failure": row[4],
            "reps": row[5],
            "metrics": metrics_payload,
            "extended": extended_flag,
        }
