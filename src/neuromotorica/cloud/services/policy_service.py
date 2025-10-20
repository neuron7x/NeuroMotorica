from __future__ import annotations

import json
from collections.abc import Mapping
import sqlite3
from typing import Any


class PolicyService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _normalize_profile(self, profile: str | None) -> str | None:
        if profile is None:
            return None
        normalized = profile.strip()
        return normalized or None

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
        profile: str | None = None,
    ) -> dict[str, Any]:
        cur = self.conn.cursor()
        metrics_json = json.dumps(dict(metrics)) if metrics is not None else None
        extended_flag: int | None = None if extended is None else int(extended)
        profile_key = self._normalize_profile(profile)
        db_profile = "" if profile_key is None else profile_key
        cur.execute(
            """
            INSERT INTO cue_stats(user_id, exercise_id, profile, cue_text, success, failure, reps, metrics, extended)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, exercise_id, profile, cue_text) DO UPDATE SET
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
                db_profile,
                cue_text,
                1 if success else 0,
                0 if success else 1,
                reps,
                metrics_json,
                extended_flag,
            ),
        )
        self.conn.commit()
        return self.get_outcome(user_id, exercise_id, cue_text, profile=profile_key)

    def topk(
        self,
        user_id: str,
        exercise_id: str,
        *,
        k: int = 3,
        profile: str | None = None,
    ) -> list[tuple[str, float]]:
        cur = self.conn.cursor()
        profile_key = self._normalize_profile(profile)
        params = [user_id, exercise_id]
        rows: list[sqlite3.Row]
        if profile_key is not None:
            cur.execute(
                """
                SELECT cue_text, success, failure FROM cue_stats
                WHERE user_id=? AND exercise_id=? AND profile=?
                """,
                (*params, profile_key),
            )
            rows = cur.fetchall()
            if not rows:
                cur.execute(
                    """
                    SELECT cue_text, SUM(success) AS success, SUM(failure) AS failure
                    FROM cue_stats
                    WHERE user_id=? AND exercise_id=?
                    GROUP BY cue_text
                    """,
                    params,
                )
                rows = cur.fetchall()
        else:
            cur.execute(
                """
                SELECT cue_text, SUM(success) AS success, SUM(failure) AS failure
                FROM cue_stats
                WHERE user_id=? AND exercise_id=?
                GROUP BY cue_text
                """,
                params,
            )
            rows = cur.fetchall()

        ranked = [
            (
                row[0],
                (float(row[1]) + 1.0) / (float(row[1]) + float(row[2]) + 2.0),
            )
            for row in rows
        ]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:k]

    def get_outcome(
        self,
        user_id: str,
        exercise_id: str,
        cue_text: str,
        *,
        profile: str | None = None,
    ) -> dict[str, Any] | None:
        cur = self.conn.cursor()
        profile_key = self._normalize_profile(profile)
        db_profile = "" if profile_key is None else profile_key
        cur.execute(
            """
            SELECT user_id, exercise_id, profile, cue_text, success, failure, reps, metrics, extended
            FROM cue_stats
            WHERE user_id=? AND exercise_id=? AND profile=? AND cue_text=?
        """,
            (user_id, exercise_id, db_profile, cue_text),
        )
        row = cur.fetchone()
        if row is None:
            return None
        metrics_payload = json.loads(row[7]) if row[7] else None
        extended_flag = bool(row[8]) if row[8] is not None else False
        return {
            "user_id": row[0],
            "exercise_id": row[1],
            "profile": row[2] or None,
            "cue_text": row[3],
            "success": row[4],
            "failure": row[5],
            "reps": row[6],
            "metrics": metrics_payload,
            "extended": extended_flag,
        }
