import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, date

def init_db():
    """Initialize YourDiary database with users, diary entries, and tasks"""
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Diary entries (messages) table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    conn.commit()
    conn.close()
    print("✅ YourDiary database initialized successfully")

def get_user_by_username(username):
    """Get user by username"""
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, password):
    """Create a new YourDiary user"""
    hashed_password = generate_password_hash(password)
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def save_message(user_id, message):
    """Save a diary entry"""
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_messages (user_id, message) VALUES (?, ?)', (user_id, message))
    conn.commit()
    conn.close()

def get_user_messages(user_id, limit=None):
    """Get user diary entries"""
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()
    if limit:
        cursor.execute('SELECT message, timestamp FROM user_messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?', (user_id, limit))
    else:
        cursor.execute('SELECT message, timestamp FROM user_messages WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    messages = cursor.fetchall()
    conn.close()
    return messages

# Task management functions
def add_task(user_id, title, description='', priority='medium', due_date=None):
    """Add a new task"""
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO tasks (user_id, title, description, priority, due_date) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, title, description, priority, due_date if due_date else None))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"YourDiary Error adding task: {e}")
        conn.close()
        return False

def get_user_tasks(user_id):
    """Get all tasks for a user"""
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, description, priority, status, due_date, created_at 
        FROM tasks 
        WHERE user_id = ? 
        ORDER BY 
            CASE WHEN status = 'completed' THEN 1 ELSE 0 END,
            CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
            created_at DESC
    """, (user_id,))

    tasks = []
    for row in cursor.fetchall():
        task = {
            'id': row[0], 'title': row[1], 'description': row[2],
            'priority': row[3], 'status': row[4], 'due_date': row[5], 'created_at': row[6]
        }
        tasks.append(task)

    conn.close()
    return tasks

def update_task_status(task_id, status, user_id):
    """Update task status"""
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND user_id = ?
        """, (status, task_id, user_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"YourDiary Error updating task: {e}")
        conn.close()
        return False

def delete_task(task_id, user_id):
    """Delete a task"""
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"YourDiary Error deleting task: {e}")
        conn.close()
        return False

def get_task_stats(user_id):
    """Get task statistics for a user"""
    conn = sqlite3.connect('yourdiary.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'pending'", (user_id,))
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'completed'", (user_id,))
    completed = cursor.fetchone()[0]

    today = date.today().isoformat()
    cursor.execute("""
        SELECT COUNT(*) FROM tasks 
        WHERE user_id = ? AND status = 'pending' AND due_date < ?
    """, (user_id, today))
    overdue = cursor.fetchone()[0]

    conn.close()

    return {'total': total, 'pending': pending, 'completed': completed, 'overdue': overdue}
