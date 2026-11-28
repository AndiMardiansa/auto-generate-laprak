import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laprakin.db")


@contextmanager
def get_db():
    """Yield a SQLite connection with row_factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize SQLite tables if they do not exist."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                nim TEXT NOT NULL DEFAULT '',
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "nim" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN nim TEXT NOT NULL DEFAULT ''")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                module_key TEXT NOT NULL,
                module_name TEXT NOT NULL,
                nim TEXT NOT NULL,
                student_name TEXT NOT NULL,
                meeting_number INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                topic_title TEXT NOT NULL,
                pj_assistant TEXT DEFAULT '',
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                word_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
