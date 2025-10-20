from __future__ import annotations

import os
import pathlib
import sqlite3


SCHEMA_VERSION = 3


def _create_base_schema(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cue_stats(
            user_id TEXT,
            exercise_id TEXT,
            profile TEXT DEFAULT '',
            cue_text TEXT,
            success INTEGER DEFAULT 0,
            failure INTEGER DEFAULT 0,
            reps INTEGER,
            metrics TEXT,
            extended INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, exercise_id, profile, cue_text)
        )
        """
    )


def _migrate_to_v3(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("ALTER TABLE cue_stats RENAME TO cue_stats_old")
    _create_base_schema(cur)
    select_stmt = (
        """
        INSERT INTO cue_stats(user_id, exercise_id, profile, cue_text, success, failure, reps, metrics, extended)
        SELECT user_id, exercise_id, '' AS profile, cue_text, success, failure, reps, metrics,
               COALESCE(extended, 0) AS extended
        FROM cue_stats_old
        """
    )
    cur.execute(select_stmt)
    cur.execute("DROP TABLE cue_stats_old")


def _ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    _create_base_schema(cur)

    cur.execute("PRAGMA table_info(cue_stats)")
    info_rows = cur.fetchall()
    existing_columns = {row[1]: row for row in info_rows}
    pk_columns = [row[1] for row in info_rows if row[5] > 0]

    needs_profile_migration = "profile" not in existing_columns or pk_columns != [
        "user_id",
        "exercise_id",
        "profile",
        "cue_text",
    ]

    if needs_profile_migration:
        _migrate_to_v3(conn)
        cur = conn.cursor()

    cur.execute("PRAGMA table_info(cue_stats)")
    info_rows = cur.fetchall()
    existing_columns = {row[1] for row in info_rows}

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
    if os.environ.get("PYTEST_CURRENT_TEST"):
        conn = sqlite3.connect(":memory:", check_same_thread=False)
    else:
        if path is None:
            path = str(pathlib.Path(__file__).with_name("policy.sqlite3"))
        conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn
