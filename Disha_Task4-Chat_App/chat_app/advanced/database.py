"""
database.py — SQLite persistence layer
========================================
All the raw SQL lives here so app.py stays focused on request/socket
handling. Three tables:

    users    -> username + hashed password (never plain text)
    rooms    -> named chat rooms anyone can create/join
    messages -> permanent history of every message sent in a room

Passwords are hashed with Werkzeug's generate_password_hash (which
uses a salted algorithm under the hood) — the plain password is
never stored anywhere, including in memory longer than necessary.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "chat.db"


def get_connection():
    """
    Each call opens a fresh connection. sqlite3 connections aren't
    safe to share across threads by default, and Flask-SocketIO
    handles requests/events on different threads, so 'open on demand,
    close when done' is the simplest safe pattern here.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't already exist. Safe to call every startup."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms (id)
            )
        """)
        # Guarantee at least one room exists so a first-time user
        # always has somewhere to land.
        conn.execute("""
            INSERT OR IGNORE INTO rooms (name, created_by, created_at)
            VALUES ('general', 'system', ?)
        """, (datetime.now().isoformat(),))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------
# User account operations
# ---------------------------------------------------------------

def create_user(username: str, password_hash: str) -> bool:
    """Returns True on success, False if the username is already taken."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.now().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user(username: str):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return row
    finally:
        conn.close()


# ---------------------------------------------------------------
# Room operations
# ---------------------------------------------------------------

def list_rooms():
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM rooms ORDER BY name COLLATE NOCASE"
        ).fetchall()
    finally:
        conn.close()


def get_room(name: str):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM rooms WHERE name = ?", (name,)
        ).fetchone()
    finally:
        conn.close()


def create_room(name: str, created_by: str) -> bool:
    """Returns True on success, False if the room name is already taken."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO rooms (name, created_by, created_at) VALUES (?, ?, ?)",
            (name, created_by, datetime.now().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ---------------------------------------------------------------
# Message operations
# ---------------------------------------------------------------

def save_message(room_id: int, username: str, content: str) -> str:
    """Stores a message and returns the timestamp string used for it."""
    ts = datetime.now().strftime("%H:%M")
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO messages (room_id, username, content, timestamp) VALUES (?, ?, ?, ?)",
            (room_id, username, content, ts),
        )
        conn.commit()
    finally:
        conn.close()
    return ts


def get_history(room_id: int, limit: int = 50):
    """
    Returns the most recent `limit` messages for a room, oldest first,
    so they can be displayed top-to-bottom in the chat window the way
    a user would expect when they join.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM (
                SELECT * FROM messages
                WHERE room_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC
            """,
            (room_id, limit),
        ).fetchall()
        return rows
    finally:
        conn.close()
