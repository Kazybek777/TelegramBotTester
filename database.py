import sqlite3
from contextlib import contextmanager

DATABASE = "stats.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                total_tests INTEGER DEFAULT 0,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def update_stats(user_id, correct, total):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO users (user_id, total_tests, total_questions, correct_answers)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                total_tests = total_tests + 1,
                total_questions = total_questions + excluded.total_questions,
                correct_answers = correct_answers + excluded.correct_answers
        """, (user_id, total, correct))
        conn.commit()

def get_stats(user_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return dict(row)
        return None

# Новая функция для сброса статистики пользователя
def reset_stats(user_id):
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()