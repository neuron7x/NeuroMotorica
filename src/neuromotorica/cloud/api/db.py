from __future__ import annotations
import sqlite3, pathlib

def get_db(path: str | None = None) -> sqlite3.Connection:
    if path is None:
        path = str(pathlib.Path(__file__).with_name("policy.sqlite3"))
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cue_stats(
            user_id TEXT,
            exercise_id TEXT,
            profile TEXT NOT NULL DEFAULT 'default',
            cue_text TEXT,
            success INTEGER DEFAULT 0,
            failure INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, exercise_id, profile, cue_text)
        )""")
    _ensure_profiled_schema(conn)
    return conn


def _ensure_profiled_schema(conn: sqlite3.Connection) -> None:
    cur = conn.execute("PRAGMA table_info(cue_stats)")
    columns = {row[1] for row in cur.fetchall()}
    if "profile" not in columns:
        conn.execute("ALTER TABLE cue_stats ADD COLUMN profile TEXT NOT NULL DEFAULT 'default'")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_cue_stats_profiled ON cue_stats(user_id, exercise_id, profile, cue_text)"
    )
    conn.commit()
