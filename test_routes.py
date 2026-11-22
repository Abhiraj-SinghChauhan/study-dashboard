"""
test_routes.py - pytest suite for the Flask routing layer.
Run with: pytest test_routes.py -v
"""
import sqlite3
from datetime import date

import pytest

import helpers
from app import create_app
from db import crud_operations as db
from db.db_init import initialize_database


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """A fresh temp-file database (with user 1) for every test."""
    path = tmp_path / "test_dashboard.db"
    monkeypatch.setattr("db.crud_operations.DB_PATH", path)
    monkeypatch.setattr("db.db_init.DB_PATH", path)
    initialize_database()
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO users (user_id, username) VALUES (1, 'test_user')")
    return path


@pytest.fixture
def client(db_path):
    return create_app(testing=True).test_client()


# ---- pages and forms ------------------------------------------------
def test_index_loads_with_contract_element_ids(client):
    r = client.get("/")
    assert r.status_code == 200
    for element_id in [
        b'id="study-form"', b'id="expense-form"', b'id="sessions-section"',
        b'id="expenses-section"', b'id="study-chart"', b'id="expense-chart"',
        b'id="js-error-banner"', b'id="stat-average"',
    ]:
        assert element_id in r.data


def test_base_has_viewport_chartjs_and_module_script(client):
    html = client.get("/").get_data(as_text=True)
    assert 'name="viewport"' in html
    assert "chart.js" in html.lower()
    assert '<script type="module"' in html and "js/main.js" in html


def test_add_expense_valid(client):
    r = client.post("/add-expense", data={
        "category_name": "Food", "amount": "25.5", "expense_date": "2026-08-01",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b"Expense added." in r.data
    assert b"flash flash-success" in r.data
    assert len(db.get_expenses(1)) == 1


def test_log_study_valid(client):
    r = client.post("/log-study", data={
        "subject_name": "Data Structures", "session_date": "2026-08-01",
        "duration_minutes": "45", "status": "completed",
    }, follow_redirects=True)
    assert b"Study session logged." in r.data
    assert db.get_study_sessions(1)[0]["duration_minutes"] == 45


@pytest.mark.parametrize("payload", [
    {"category_name": "", "amount": "5", "expense_date": "2026-08-01"},
    {"category_name": "Food", "amount": "abc", "expense_date": "2026-08-01"},
    {"category_name": "Food", "amount": "-5", "expense_date": "2026-08-01"},
    {"category_name": "Food", "amount": "inf", "expense_date": "2026-08-01"},
    {"category_name": "Food", "amount": "5", "expense_date": "tomorrow"},
])
def test_invalid_expense_flashes_error_and_writes_nothing(client, payload):
    r = client.post("/add-expense", data=payload, follow_redirects=True)
    assert r.status_code == 200 and b"Couldn" in r.data
    assert b"flash flash-error" in r.data
    assert db.get_expenses(1) == []


@pytest.mark.parametrize("payload", [
    {"subject_name": "", "session_date": "2026-08-01", "duration_minutes": "30"},
    {"subject_name": "DSA", "session_date": "2026-08-01", "duration_minutes": "abc"},
    {"subject_name": "DSA", "session_date": "2026-08-01", "duration_minutes": "-3"},
    {"subject_name": "DSA", "session_date": "2026-08-01", "duration_minutes": "30", "status": "bogus"},
    {"subject_name": "DSA", "session_date": "not-a-date", "duration_minutes": "30"},
])
def test_invalid_study_session_flashes_error_and_writes_nothing(client, payload):
    r = client.post("/log-study", data=payload, follow_redirects=True)
    assert r.status_code == 200 and b"Couldn" in r.data
    assert db.get_study_sessions(1) == []


def test_xss_payload_is_escaped(client):
    payload = "<script>alert(1)</script>"
    client.post("/add-expense", data={
        "category_name": "Food", "amount": "5", "expense_date": "2026-08-01",
        "description": payload,
    })
    r = client.get("/")
    assert payload.encode() not in r.data
    assert b"&lt;script&gt;" in r.data


def test_tables_mark_rows_after_the_second_as_extra(client):
    for day in ("01", "02", "03", "04"):
        client.post("/add-expense", data={
            "category_name": "Food", "amount": "10", "expense_date": f"2026-08-{day}",
        })
    html = client.get("/").get_data(as_text=True)
    assert html.count('<tr class="extra-row"') == 2


def test_empty_state_and_status_badge(client):
    html = client.get("/").get_data(as_text=True)
    assert 'class="empty-state"' in html
    client.post("/log-study", data={
        "subject_name": "DSA", "session_date": "2026-08-01",
        "duration_minutes": "30", "status": "in_progress",
    })
    html = client.get("/").get_data(as_text=True)
    assert 'class="status-badge status-in_progress"' in html


# ---- error handling -------------------------------------------------
def test_unknown_route_returns_custom_404(client):
    r = client.get("/nope")
    assert r.status_code == 404
    assert b"Page not found" in r.data


def test_database_failure_is_flashed_not_raised(client, monkeypatch):
    def boom(*args, **kwargs):
        raise sqlite3.IntegrityError("simulated failure")
    monkeypatch.setattr("routes.main.db.add_expense", boom)
    r = client.post("/add-expense", data={
        "category_name": "Food", "amount": "5", "expense_date": "2026-08-01",
    }, follow_redirects=True)
    assert r.status_code == 200 and b"Something went wrong" in r.data


def test_unhandled_error_shows_custom_500_page(db_path, monkeypatch):
    # TESTING=False, otherwise Flask re-raises instead of using the 500 handler.
    def boom(*args, **kwargs):
        raise RuntimeError("simulated crash")
    monkeypatch.setattr("routes.main.db.get_study_sessions", boom)
    r = create_app(testing=False).test_client().get("/")
    assert r.status_code == 500
    assert b"Something went wrong" in r.data
    assert b"Traceback" not in r.data


# ---- JSON API -------------------------------------------------------
@pytest.mark.parametrize("days", ["abc", "0", "-5", "99999999"])
def test_chart_data_rejects_bad_days_param(client, days):
    r = client.get(f"/api/chart-data?days={days}")
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_chart_data_matches_contract_shape_when_empty(client):
    data = client.get("/api/chart-data?days=30").get_json()
    assert set(data.keys()) == {
        "range", "study", "expenses", "expenses_by_category", "daily_study_average_minutes",
    }
    assert data["range"]["days"] == 30
    assert data["expenses_by_category"] == {"labels": [], "values": []}
    assert data["daily_study_average_minutes"] == 0.0


def test_chart_data_defaults_to_30_days(client):
    assert client.get("/api/chart-data").get_json()["range"]["days"] == 30


def test_chart_data_reports_seeded_data(client):
    today = date.today().isoformat()
    client.post("/log-study", data={
        "subject_name": "DSA", "session_date": today,
        "duration_minutes": "90", "status": "completed",
    })
    client.post("/add-expense", data={
        "category_name": "Food", "amount": "150", "expense_date": today,
    })
    client.post("/add-expense", data={
        "category_name": "Transport", "amount": "40", "expense_date": today,
    })
    data = client.get("/api/chart-data?days=30").get_json()
    assert data["study"] == {"labels": [today], "values": [90]}
    assert data["expenses"]["amounts"] == [190.0]
    assert data["expenses"]["running_total"] == [190.0]
    assert data["expenses_by_category"] == {"labels": ["Food", "Transport"], "values": [150.0, 40.0]}
    assert data["daily_study_average_minutes"] == 3.0


# ---- pure helpers ---------------------------------------------------
def test_group_expenses_by_category_sorts_biggest_first():
    rows = [
        {"category_name": "Transport", "amount": 40.0},
        {"category_name": "Food", "amount": 100.0},
        {"category_name": "Food", "amount": 50.0},
    ]
    assert helpers.group_expenses_by_category(rows) == {
        "labels": ["Food", "Transport"], "values": [150.0, 40.0],
    }


def test_daily_average_divides_by_full_period():
    sessions = [{"status": "completed", "duration_minutes": 90},
                {"status": "planned", "duration_minutes": 500}]
    assert helpers.calculate_daily_study_average(sessions, 30) == 3.0


def test_validator_reports_every_problem_at_once():
    with pytest.raises(helpers.ValidationError) as exc:
        helpers.validate_expense_input({"amount": "abc"})
    message = str(exc.value)
    assert "category_name" in message and "expense_date" in message and "amount" in message