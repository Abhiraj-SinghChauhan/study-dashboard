"""db_init.py - builds dashboard.db from schema.sql and seeds demo data.
Run from the repo root:  python db/db_init.py
"""
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

DB_PATH = BASE_DIR / "dashboard.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def initialize_database(reset: bool = False) -> None:
    """Create dashboard.db from schema.sql. reset=True deletes any existing DB first."""
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        # executescript is safe: schema.sql is a static file we wrote.
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
        print(f"Database initialized at {DB_PATH}")
    finally:
        conn.close()


def seed_sample_data() -> None:
    """Create demo user (user_id 1) plus a few sample sessions and expenses."""
    import crud_operations as crud

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, email) "
            "VALUES (1, 'demo_student', 'demo@example.com')"
        )
        conn.commit()
    finally:
        conn.close()

    dsa = crud.get_or_create_subject("Data Structures")
    os_id = crud.get_or_create_subject("Operating Systems")
    food = crud.get_or_create_category("Food")
    transport = crud.get_or_create_category("Transport")

    crud.add_study_session(1, dsa, "2026-11-19", 90, "completed")
    crud.add_study_session(1, os_id, "2026-11-20", 60, "planned")
    crud.add_expense(1, food, 150.0, "2026-11-19", "Canteen lunch")
    crud.add_expense(1, transport, 40.0, "2026-11-19", "Bus fare")
    print("Sample data seeded.")


if __name__ == "__main__":
    initialize_database(reset=True)
    seed_sample_data()
