
import sqlite3
from datetime import datetime

from ..config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    intent TEXT,
    handoff INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE TABLE IF NOT EXISTS user_profiles (
    session_id TEXT PRIMARY KEY,
    nickname TEXT,
    preferred_topics TEXT,
    visit_count INTEGER DEFAULT 1,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
"""


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.executescript(SCHEMA)


def save_message(session_id: str, role: str, content: str, intent: str | None = None, handoff: int = 0):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, intent, handoff) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, intent, handoff),
        )


def get_history(session_id: str, k: int = 8) -> list:

    with _conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, k),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def touch_profile(session_id: str):

    with _conn() as conn:
        conn.execute(
            """INSERT INTO user_profiles (session_id, visit_count, updated_at)
               VALUES (?, 1, ?)
               ON CONFLICT(session_id)
               DO UPDATE SET visit_count = visit_count + 1, updated_at = ?""",
            (session_id, datetime.now().isoformat(), datetime.now().isoformat()),
        )


def get_profile(session_id: str) -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM user_profiles WHERE session_id = ?", (session_id,)
        ).fetchone()
    return dict(row) if row else {}


def stats() -> dict:

    with _conn() as conn:
        total_msgs = conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"]
        sessions = conn.execute(
            "SELECT COUNT(DISTINCT session_id) c FROM messages"
        ).fetchone()["c"]
        intent_rows = conn.execute(
            """SELECT COALESCE(intent, '未分类') intent, COUNT(*) c
               FROM messages WHERE role = 'assistant' GROUP BY intent ORDER BY c DESC"""
        ).fetchall()
        handoff_cnt = conn.execute(
            "SELECT COUNT(DISTINCT session_id) c FROM messages WHERE handoff = 1"
        ).fetchone()["c"]
        recent = conn.execute(
            """SELECT session_id, role, content, intent, handoff, created_at
               FROM messages ORDER BY id DESC LIMIT 20"""
        ).fetchall()
    assistant_total = sum(r["c"] for r in intent_rows) or 1
    return {
        "total_messages": total_msgs,
        "total_sessions": sessions,
        "intent_distribution": [
            {"intent": r["intent"], "count": r["c"], "ratio": round(r["c"] / assistant_total, 3)}
            for r in intent_rows
        ],
        "handoff_sessions": handoff_cnt,
        "handoff_rate": round(handoff_cnt / (sessions or 1), 3),
        "recent_messages": [dict(r) for r in recent],
    }
