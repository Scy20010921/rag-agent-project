"""
SQLite 会话持久化模块。
每个会话（session）包含多轮对话消息，存储在本地 SQLite 文件中。
"""
import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

# 数据库文件放在项目根目录（与 main.py 同级）
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "chat_history.db")

# 东八区
TZ = timezone(timedelta(hours=8))


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """建表（幂等）"""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '新对话',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
        CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);
    """)
    conn.commit()
    conn.close()


# ---- Session CRUD ----

def create_session(session_id: str, title: str = "新对话") -> dict:
    now = datetime.now(TZ).isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, title, now, now),
    )
    conn.commit()
    conn.close()
    return {"id": session_id, "title": title, "created_at": now, "updated_at": now}


def list_sessions() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session(session_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT id, title, created_at, updated_at FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(session_id: str):
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def update_session_title(session_id: str, title: str):
    now = datetime.now(TZ).isoformat()
    conn = _get_conn()
    conn.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?", (title, now, session_id))
    conn.commit()
    conn.close()


# ---- Message CRUD ----

def save_message(session_id: str, role: str, content: str):
    now = datetime.now(TZ).isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, role, content, now),
    )
    # 更新会话的 updated_at，自动更新第一条 user 消息作为标题
    conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
    # 如果标题还是"新对话"且这是 user 消息，用消息前 30 字做标题
    title = content.strip()[:30]
    conn.execute(
        "UPDATE sessions SET title = ? WHERE id = ? AND title = '新对话'",
        (title, session_id),
    )
    conn.commit()
    conn.close()


def load_messages(session_id: str) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, role, content, created_at FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# 模块加载时自动建表
init_db()