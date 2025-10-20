from __future__ import annotations
import sqlite3

class PolicyService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def update_outcome(
        self,
        user_id: str,
        exercise_id: str,
        cue_text: str,
        success: bool,
        profile: str | None = None,
    ) -> None:
        profile_key = profile or "default"
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO cue_stats(user_id, exercise_id, profile, cue_text, success, failure)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, exercise_id, profile, cue_text) DO UPDATE SET
              success = success + excluded.success,
              failure = failure + excluded.failure
        """,
        (
            user_id,
            exercise_id,
            profile_key,
            cue_text,
            1 if success else 0,
            0 if success else 1,
        ))
        self.conn.commit()

    def topk(self, user_id: str, exercise_id: str, *, profile: str | None = None, k: int = 3):
        profile_key = profile or "default"
        cur = self.conn.cursor()
        cur.execute("""
            SELECT cue_text, success, failure FROM cue_stats
            WHERE user_id=? AND exercise_id=? AND profile=?
        """, (user_id, exercise_id, profile_key))
        rows = cur.fetchall()
        ranked = [(r[0], (r[1] + 1) / (r[1] + r[2] + 2)) for r in rows]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:k]
