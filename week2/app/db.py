"""Database layer: SQLite access for notes and action items.

Uses app.config for paths. All functions that return rows return dict-like
objects (sqlite3.Row) with known keys: see each function's docstring.
"""

from __future__ import annotations

import sqlite3
from typing import Any, List, Optional

from . import config


def ensure_data_directory_exists() -> None:
    """Create data directory if it does not exist."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Return a connection to the app SQLite database. Caller must close or use as context."""
    ensure_data_directory_exists()
    connection = sqlite3.connect(str(config.DB_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create tables if they do not exist. Safe to call on every startup."""
    ensure_data_directory_exists()
    try:
        with get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS action_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id INTEGER,
                    text TEXT NOT NULL,
                    done INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (note_id) REFERENCES notes(id)
                );
                """
            )
            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Database initialization failed: {e}") from e


def _row_to_note(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a notes table row to a plain dict with id, content, created_at."""
    return {"id": row["id"], "content": row["content"], "created_at": row["created_at"]}


def _row_to_action_item(row: sqlite3.Row) -> dict[str, Any]:
    """Convert an action_items table row to a plain dict."""
    return {
        "id": row["id"],
        "note_id": row["note_id"],
        "text": row["text"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
    }


def insert_note(content: str) -> int:
    """Insert a note; returns its id. Raises on DB error."""
    try:
        with get_connection() as conn:
            cur = conn.execute("INSERT INTO notes (content) VALUES (?)", (content,))
            conn.commit()
            return int(cur.lastrowid)
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error: {e}") from e


def list_notes() -> List[dict[str, Any]]:
    """Return all notes as list of dicts with id, content, created_at (newest first)."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, content, created_at FROM notes ORDER BY id DESC"
            ).fetchall()
            return [_row_to_note(r) for r in rows]
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error: {e}") from e


def get_note(note_id: int) -> Optional[dict[str, Any]]:
    """Return a note by id as dict with id, content, created_at, or None if not found."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, content, created_at FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            return _row_to_note(row) if row else None
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error: {e}") from e


def insert_action_items(items: List[str], note_id: Optional[int] = None) -> List[int]:
    """Insert action items; returns their ids in order. Raises on DB error."""
    if not items:
        return []
    try:
        with get_connection() as conn:
            ids: List[int] = []
            for text in items:
                cur = conn.execute(
                    "INSERT INTO action_items (note_id, text) VALUES (?, ?)",
                    (note_id, text),
                )
                ids.append(int(cur.lastrowid))
            conn.commit()
            return ids
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error: {e}") from e


def list_action_items(note_id: Optional[int] = None) -> List[dict[str, Any]]:
    """Return action items as list of dicts (id, note_id, text, done, created_at)."""
    try:
        with get_connection() as conn:
            if note_id is None:
                rows = conn.execute(
                    "SELECT id, note_id, text, done, created_at FROM action_items ORDER BY id DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, note_id, text, done, created_at FROM action_items WHERE note_id = ? ORDER BY id DESC",
                    (note_id,),
                ).fetchall()
            return [_row_to_action_item(r) for r in rows]
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error: {e}") from e


def mark_action_item_done(action_item_id: int, done: bool) -> None:
    """Set done flag for an action item. Raises on DB error (e.g. missing id)."""
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE action_items SET done = ? WHERE id = ?",
                (1 if done else 0, action_item_id),
            )
            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error: {e}") from e
