"""
YourDiary — Database Layer
Supports both SQLite (local dev) and PostgreSQL (production).

Set the DATABASE_URL environment variable to use PostgreSQL:
  DATABASE_URL=postgresql://user:password@host:5432/dbname

If DATABASE_URL is not set, falls back to SQLite (yourdiary.db).
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, date

# ─── Connection Factory ───────────────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL", "")


def _get_conn():
    """
    Returns (connection, placeholder, is_postgres).
    - placeholder: "?" for SQLite, "%s" for PostgreSQL
    - is_postgres:  bool, used for schema differences
    """
    url = DATABASE_URL
    if url:
        import psycopg2
        # Render provides postgres:// but psycopg2 requires postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        return conn, "%s", True
    else:
        return sqlite3.connect("yourdiary.db"), "?", False


# ─── Schema Init ──────────────────────────────────────────────────────────────

def init_db():
    """Initialize database tables (creates them if they don't exist)."""
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()

    # Auto-increment primary key differs between SQLite and PostgreSQL
    pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {pk},
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS user_messages (
            id {pk},
            user_id INTEGER,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS tasks (
            id {pk},
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Per-user LSTM model weights stored as binary blob
    weight_col = "BYTEA" if is_pg else "BLOB"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS user_models (
            user_id INTEGER PRIMARY KEY,
            weights {weight_col} NOT NULL,
            entry_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()
    db_type = "PostgreSQL" if is_pg else "SQLite"
    print(f"✅ YourDiary database ({db_type}) initialized successfully")


# ─── User Model (LSTM Weights) Functions ─────────────────────────────────────

def save_user_model_weights(user_id: int, weights_bytes: bytes, entry_count: int = 0) -> bool:
    """
    Persist a user's LSTM model weights as binary data in the database.
    Uses an UPSERT pattern (check + update or insert) for SQLite/PostgreSQL compat.
    """
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()
    try:
        # Wrap bytes for PostgreSQL BYTEA; sqlite3 accepts raw bytes natively
        if is_pg:
            import psycopg2
            data = psycopg2.Binary(weights_bytes)
        else:
            data = weights_bytes

        # Check if a row already exists
        cursor.execute(f"SELECT 1 FROM user_models WHERE user_id = {ph}", (user_id,))
        if cursor.fetchone():
            cursor.execute(
                f"UPDATE user_models "
                f"SET weights = {ph}, entry_count = {ph}, updated_at = CURRENT_TIMESTAMP "
                f"WHERE user_id = {ph}",
                (data, entry_count, user_id)
            )
        else:
            cursor.execute(
                f"INSERT INTO user_models (user_id, weights, entry_count) "
                f"VALUES ({ph}, {ph}, {ph})",
                (user_id, data, entry_count)
            )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"YourDiary Error saving model weights: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()
        return False


def load_user_model_weights(user_id: int):
    """
    Load a user's LSTM model weights from the database.
    Returns (bytes, entry_count) if found, or (None, 0) if not.
    """
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"SELECT weights, entry_count FROM user_models WHERE user_id = {ph}",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return bytes(row[0]), int(row[1] or 0)
        return None, 0
    except Exception as e:
        print(f"YourDiary Error loading model weights: {e}")
        conn.close()
        return None, 0


# ─── User Functions ───────────────────────────────────────────────────────────

def get_user_by_username(username):
    """Return (id, username, hashed_password) or None."""
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, username, password FROM users WHERE username = {ph}", (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def create_user(username, password):
    """Create a new user. Returns True on success, False if username taken."""
    hashed = generate_password_hash(password)
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"INSERT INTO users (username, password) VALUES ({ph}, {ph})",
            (username, hashed)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        # IntegrityError (duplicate username) from both sqlite3 and psycopg2
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()
        return False


# ─── Diary Entry Functions ────────────────────────────────────────────────────

def save_message(user_id, message):
    """Save a diary entry."""
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO user_messages (user_id, message) VALUES ({ph}, {ph})",
        (user_id, message)
    )
    conn.commit()
    conn.close()


def get_user_messages(user_id, limit=None):
    """Return list of (message, timestamp) tuples, newest first."""
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()
    if limit:
        cursor.execute(
            f"SELECT message, timestamp FROM user_messages "
            f"WHERE user_id = {ph} ORDER BY timestamp DESC LIMIT {ph}",
            (user_id, limit)
        )
    else:
        cursor.execute(
            f"SELECT message, timestamp FROM user_messages "
            f"WHERE user_id = {ph} ORDER BY timestamp DESC",
            (user_id,)
        )
    messages = cursor.fetchall()
    conn.close()
    return messages


# ─── Task Functions ───────────────────────────────────────────────────────────

def add_task(user_id, title, description="", priority="medium", due_date=None):
    """Create a new task. Returns True on success."""
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"INSERT INTO tasks (user_id, title, description, priority, due_date) "
            f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph})",
            (user_id, title, description, priority, due_date)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"YourDiary Error adding task: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()
        return False


def get_user_tasks(user_id):
    """Return all tasks for a user as a list of dicts."""
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()

    # CASE expressions are standard SQL — work on both SQLite and PostgreSQL
    cursor.execute(f"""
        SELECT id, title, description, priority, status, due_date, created_at
        FROM tasks
        WHERE user_id = {ph}
        ORDER BY
            CASE WHEN status = 'completed' THEN 1 ELSE 0 END,
            CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
            created_at DESC
    """, (user_id,))

    tasks = []
    for row in cursor.fetchall():
        tasks.append({
            "id":          row[0],
            "title":       row[1],
            "description": row[2],
            "priority":    row[3],
            "status":      row[4],
            "due_date":    str(row[5]) if row[5] else None,
            "created_at":  str(row[6]) if row[6] else None,
        })

    conn.close()
    return tasks


def update_task_status(task_id, status, user_id):
    """Update a task's status. Returns True if a row was affected."""
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"UPDATE tasks SET status = {ph}, updated_at = CURRENT_TIMESTAMP "
            f"WHERE id = {ph} AND user_id = {ph}",
            (status, task_id, user_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"YourDiary Error updating task: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()
        return False


def delete_task(task_id, user_id):
    """Delete a task. Returns True if a row was deleted."""
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"DELETE FROM tasks WHERE id = {ph} AND user_id = {ph}",
            (task_id, user_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"YourDiary Error deleting task: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()
        return False


def get_task_stats(user_id):
    """Return task statistics dict for a user."""
    conn, ph, is_pg = _get_conn()
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM tasks WHERE user_id = {ph}", (user_id,))
    total = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT COUNT(*) FROM tasks WHERE user_id = {ph} AND status = 'pending'",
        (user_id,)
    )
    pending = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT COUNT(*) FROM tasks WHERE user_id = {ph} AND status = 'completed'",
        (user_id,)
    )
    completed = cursor.fetchone()[0]

    today = date.today().isoformat()
    cursor.execute(f"""
        SELECT COUNT(*) FROM tasks
        WHERE user_id = {ph} AND status = 'pending' AND due_date < {ph}
    """, (user_id, today))
    overdue = cursor.fetchone()[0]

    conn.close()
    return {"total": total, "pending": pending, "completed": completed, "overdue": overdue}
