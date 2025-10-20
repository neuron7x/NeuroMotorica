from __future__ import annotations
import sqlite3, pathlib

def get_db(path: str | None = None) -> sqlite3.Connection:
    if path is None:
        path = str(pathlib.Path(__file__).with_name("policy.sqlite3"))
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cue_stats(
            user_id TEXT, exercise_id TEXT, cue_text TEXT,
            success INTEGER DEFAULT 0, failure INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, exercise_id, cue_text)
        )""")
    conn.commit()
    return conn
