# backend/app/db.py
from __future__ import annotations

import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent / "app.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_session():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db_session() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS scores_self (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            hp INTEGER NOT NULL,
            atk INTEGER NOT NULL,
            def INTEGER NOT NULL,
            spa INTEGER NOT NULL,
            spd INTEGER NOT NULL,
            spe INTEGER NOT NULL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS scores_peer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rater_user_id TEXT NOT NULL,
            target_user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            hp INTEGER NOT NULL,
            atk INTEGER NOT NULL,
            def INTEGER NOT NULL,
            spa INTEGER NOT NULL,
            spd INTEGER NOT NULL,
            spe INTEGER NOT NULL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS scores_teacher (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_user_id TEXT NOT NULL,
            target_user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            hp INTEGER NOT NULL,
            atk INTEGER NOT NULL,
            def INTEGER NOT NULL,
            spa INTEGER NOT NULL,
            spd INTEGER NOT NULL,
            spe INTEGER NOT NULL
        )
        """)

        # Teacher：同一位老師對同一位學生只保留最新一筆（覆寫）
        # 先去除重複（保留每組 teacher+target id 最大的那筆）
        conn.execute("""
        DELETE FROM scores_teacher
        WHERE id NOT IN (
          SELECT MAX(id)
          FROM scores_teacher
          GROUP BY teacher_user_id, target_user_id
        )
        """)

        # 建立唯一索引：同一對 (teacher, target) 只能有一筆
        conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_scores_teacher_teacher_target
        ON scores_teacher (teacher_user_id, target_user_id)
        """)

        # 同一個 rater 對同一個 target 只保留最新一筆（覆寫）
        # 先去除重複資料（避免後面建 UNIQUE index 失敗）
        # 這段會保留每個 (rater_user_id, target_user_id) 中 id 最大的那筆（視為最新）
        conn.execute("""
        DELETE FROM scores_peer
        WHERE id NOT IN (
          SELECT MAX(id)
          FROM scores_peer
          GROUP BY rater_user_id, target_user_id
        )
        """)

        # 建立唯一索引：同一對 (rater, target) 只能有一筆
        conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_scores_peer_rater_target
        ON scores_peer (rater_user_id, target_user_id)
        """)
