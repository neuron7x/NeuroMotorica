from __future__ import annotations

import pathlib
import sqlite3


SCHEMA_VERSION = 2


def _ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cue_stats(
            user_id TEXT,
            exercise_id TEXT,
            cue_text TEXT,
            success INTEGER DEFAULT 0,
            failure INTEGER DEFAULT 0,
            reps INTEGER,
            metrics TEXT,
            extended INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, exercise_id, cue_text)
        )
    """)

    cur.execute("PRAGMA table_info(cue_stats)")
    existing_columns = {row[1] for row in cur.fetchall()}

    if "reps" not in existing_columns:
        cur.execute("ALTER TABLE cue_stats ADD COLUMN reps INTEGER")
    if "metrics" not in existing_columns:
        cur.execute("ALTER TABLE cue_stats ADD COLUMN metrics TEXT")
    if "extended" not in existing_columns:
        cur.execute("ALTER TABLE cue_stats ADD COLUMN extended INTEGER DEFAULT 0")
        cur.execute("UPDATE cue_stats SET extended = 0 WHERE extended IS NULL")

    cur.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()


def get_db(path: str | None = None) -> sqlite3.Connection:
    if path is None:
        path = str(pathlib.Path(__file__).with_name("policy.sqlite3"))
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn
