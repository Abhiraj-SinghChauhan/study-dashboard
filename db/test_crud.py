"""Tests for db/crud_operations.py. Run from repo root:  py -m pytest db/test_crud.py -v"""
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crud_operations as crud
import db_init


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Fresh temp-file DB per test (':memory:' won't work: each connection is a new DB)."""
    db_path = tmp_path / "test_dashboard.db"
    monkeypatch.setattr(crud, "DB_PATH", db_path)
    monkeypatch.setattr(db_init, "DB_PATH", db_path)
    db_init.initialize_database()
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("INSERT INTO users (user_id, username) VALUES (1, 'test_user')")
        conn.commit()
    return db_path


def test_add_and_get_study_session(temp_db):
    subj = crud.get_or_create_subject("DSA")
    crud.add_study_session(1, subj, "2026-11-01", 45, "completed")
    rows = crud.get_study_sessions(1)
    assert len(rows) == 1
    assert rows[0]["subject_name"] == "DSA"
    assert rows[0]["duration_minutes"] == 45


def test_get_or_create_is_idempotent(temp_db):
    assert crud.get_or_create_subject("DSA") == crud.get_or_create_subject("DSA")
    assert crud.get_or_create_category("Food") == crud.get_or_create_category("Food")


def test_invalid_status_rejected(temp_db):
    subj = crud.get_or_create_subject("DSA")
    with pytest.raises(ValueError):
        crud.add_study_session(1, subj, "2026-11-01", 45, "bogus")


def test_foreign_key_violation_raises(temp_db):
    with pytest.raises(sqlite3.IntegrityError):
        crud.add_study_session(1, 9999, "2026-11-01", 45, "completed")


def test_date_range_filter(temp_db):
    subj = crud.get_or_create_subject("DSA")
    crud.add_study_session(1, subj, "2026-11-01", 30, "completed")
    crud.add_study_session(1, subj, "2026-11-15", 30, "completed")
    rows = crud.get_study_sessions(1, start_date="2026-11-10", end_date="2026-11-30")
    assert [r["session_date"] for r in rows] == ["2026-11-15"]


def test_expense_roundtrip_and_injection_is_inert(temp_db):
    cat = crud.get_or_create_category("Food")
    payload = "'; DROP TABLE expenses; --"
    crud.add_expense(1, cat, 50.0, "2026-11-01", payload)
    rows = crud.get_expenses(1)
    assert rows[0]["description"] == payload
    assert rows[0]["category_name"] == "Food"
