import json
import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "pocketsmart.db"))


def connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                jti TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                budget REAL NOT NULL,
                request_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_recommendations_user_date
                ON recommendations(user_id, created_at DESC);
            """
        )


def create_user(name, email, password_hash):
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        return dict(connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone())


def get_user_by_email(email):
    with connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    with connect() as connection:
        row = connection.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def create_session(jti, user_id, expires_at):
    with connect() as connection:
        connection.execute(
            "INSERT INTO sessions (jti, user_id, expires_at) VALUES (?, ?, ?)",
            (jti, user_id, expires_at),
        )


def get_session(jti, now):
    with connect() as connection:
        row = connection.execute(
            "SELECT user_id FROM sessions WHERE jti = ? AND expires_at > ?", (jti, now)
        ).fetchone()
        return row["user_id"] if row else None


def delete_session(jti):
    with connect() as connection:
        connection.execute("DELETE FROM sessions WHERE jti = ?", (jti,))


def save_recommendation(user_id, category, payload, result):
    with connect() as connection:
        cursor = connection.execute(
            """INSERT INTO recommendations
               (user_id, category, budget, request_json, result_json)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, category, payload["budget"], json.dumps(payload), json.dumps(result)),
        )
        return cursor.lastrowid


def get_history(user_id, limit=30):
    with connect() as connection:
        rows = connection.execute(
            """SELECT id, category, budget, request_json, result_json, created_at
               FROM recommendations WHERE user_id = ?
               ORDER BY created_at DESC, id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [
            {
                **dict(row),
                "request": json.loads(row["request_json"]),
                "result": json.loads(row["result_json"]),
            }
            for row in rows
        ]


def get_recommendation(user_id, recommendation_id):
    with connect() as connection:
        row = connection.execute(
            """SELECT id, category, budget, request_json, result_json, created_at
               FROM recommendations WHERE id = ? AND user_id = ?""",
            (recommendation_id, user_id),
        ).fetchone()
        if not row:
            return None
        return {
            **dict(row),
            "request": json.loads(row["request_json"]),
            "result": json.loads(row["result_json"]),
        }


def get_user_stats(user_id):
    with connect() as connection:
        row = connection.execute(
            """SELECT COUNT(*) AS plan_count, COALESCE(SUM(budget), 0) AS planned_total
               FROM recommendations WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
        return dict(row)