"""Acces la baza de date SQLite + inițializare/migrare schemă."""
import sqlite3
from flask import g, current_app


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _column_exists(conn, table, column):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    return column in cols


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # ---- USERS ----
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT
        )
    """)

    # ---- LICENSES ----
    conn.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            tier TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            activated_at TEXT,
            hwid TEXT,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)
    # Migrare coloane noi pentru tabela licenses existentă
    if not _column_exists(conn, "licenses", "user_id"):
        conn.execute("ALTER TABLE licenses ADD COLUMN user_id INTEGER REFERENCES users(id)")
    if not _column_exists(conn, "licenses", "device_name"):
        conn.execute("ALTER TABLE licenses ADD COLUMN device_name TEXT")

    # ---- DEVICES ----
    conn.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            hwid TEXT NOT NULL,
            device_name TEXT,
            registered_at TEXT NOT NULL,
            last_seen TEXT,
            UNIQUE(user_id, hwid),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ---- OPTIMIZATION HISTORY ----
    conn.execute("""
        CREATE TABLE IF NOT EXISTS optimization_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            license_key TEXT,
            optimization TEXT NOT NULL,
            tier TEXT,
            ran_at TEXT NOT NULL,
            before_state TEXT,
            after_state TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
