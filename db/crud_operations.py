"""crud_operations.py - the ONLY module that touches sqlite3 / raw SQL.
Every function returns plain int / bool / list[dict].
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "dashboard.db"
VALID_SESSION_STATUSES = {"planned", "in_progress", "completed", "skipped"}


@contextmanager
def get_connection():
    """Connection with foreign keys ON; commit on success, rollback on error, always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_or_create_subject(name: str) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT subject_id FROM subjects WHERE subject_name = ?", (name,)
        ).fetchone()
        if row:
            return row["subject_id"]
        cur = conn.execute("INSERT INTO subjects (subject_name) VALUES (?)", (name,))
        return cur.lastrowid


def get_or_create_category(name: str) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT category_id FROM expense_categories WHERE category_name = ?", (name,)
        ).fetchone()
        if row:
            return row["category_id"]
        cur = conn.execute(
            "INSERT INTO expense_categories (category_name) VALUES (?)", (name,)
        )
        return cur.lastrowid


def add_study_session(user_id, subject_id, session_date, duration_minutes, status) -> int:
    if status not in VALID_SESSION_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_SESSION_STATUSES}.")
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO study_sessions (user_id, subject_id, session_date, duration_minutes, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, subject_id, session_date, duration_minutes, status),
        )
        return cur.lastrowid


def get_study_sessions(user_id, start_date=None, end_date=None) -> list[dict]:
    query = (
        "SELECT s.session_id, s.subject_id, sub.subject_name, s.session_date, "
        "s.duration_minutes, s.status "
        "FROM study_sessions s JOIN subjects sub ON s.subject_id = sub.subject_id "
        "WHERE s.user_id = ?"
    )
    params = [user_id]
    if start_date:
        query += " AND s.session_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND s.session_date <= ?"
        params.append(end_date)
    query += " ORDER BY s.session_date DESC, s.session_id DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def add_expense(user_id, category_id, amount, expense_date, description) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (user_id, category_id, amount, expense_date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, category_id, amount, expense_date, description),
        )
        return cur.lastrowid


def get_expenses(user_id, start_date=None, end_date=None) -> list[dict]:
    query = (
        "SELECT e.expense_id, e.category_id, ec.category_name, e.amount, "
        "e.expense_date, e.description "
        "FROM expenses e JOIN expense_categories ec ON e.category_id = ec.category_id "
        "WHERE e.user_id = ?"
    )
    params = [user_id]
    if start_date:
        query += " AND e.expense_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND e.expense_date <= ?"
        params.append(end_date)
    query += " ORDER BY e.expense_date DESC, e.expense_id DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]
