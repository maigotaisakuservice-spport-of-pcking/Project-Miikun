import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "logs.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            subject TEXT NOT NULL DEFAULT 'general',
            user_text TEXT NOT NULL,
            ai_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_used_for_training BOOLEAN DEFAULT 0
        )
    """)
    # Long term memory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            memory_key TEXT NOT NULL,
            memory_value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, subject, memory_key)
        )
    """)
    conn.commit()
    conn.close()

def insert_log(session_id, subject, user_text, ai_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (session_id, subject, user_text, ai_text) VALUES (?, ?, ?, ?)",
        (session_id, subject, user_text, ai_text)
    )
    conn.commit()
    conn.close()

def get_memories(session_id, subject):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT memory_key, memory_value FROM long_term_memory WHERE session_id = ? AND (subject = ? OR subject = 'general')",
        (session_id, subject)
    )
    rows = cursor.fetchall()
    conn.close()
    return {row["memory_key"]: row["memory_value"] for row in rows}

def update_memory(session_id, subject, key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO long_term_memory (session_id, subject, memory_key, memory_value)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id, subject, memory_key) DO UPDATE SET
            memory_value = excluded.memory_value,
            updated_at = CURRENT_TIMESTAMP
    """, (session_id, subject, key, value))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
