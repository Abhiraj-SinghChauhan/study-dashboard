# Contracts (frozen)

## Field names (same in HTML, DB, Python and JS)
subject_name, session_date, duration_minutes, status,
category_name, amount, expense_date, description
status values: planned, in_progress, completed, skipped

## Routes (Flask)
- GET  /                        dashboard page
- POST /log-study               form post, flashes message and redirects
- POST /add-expense             form post, flashes message and redirects
- GET  /api/chart-data?days=30  JSON (shape below)

## /api/chart-data response
JS builds against this example today, using a fixture file.

    {
      "range": {"start": "2026-11-01", "end": "2026-11-30", "days": 30},
      "study": {"labels": ["2026-11-19"], "values": [90]},
      "expenses": {"labels": ["2026-11-19"], "amounts": [150.0], "running_total": [150.0]},
      "expenses_by_category": {"labels": ["Food", "Transport"], "values": [150.0, 40.0]},
      "daily_study_average_minutes": 3.0
    }

## DB functions (db/crud_operations.py, exact names)
- get_or_create_subject(name) -> int
- get_or_create_category(name) -> int
- add_study_session(user_id, subject_id, session_date, duration_minutes, status) -> int
- get_study_sessions(user_id, start_date=None, end_date=None) -> list[dict]
- add_expense(user_id, category_id, amount, expense_date, description) -> int
- get_expenses(user_id, start_date=None, end_date=None) -> list[dict]

## Element IDs (HTML to JS), frozen
js-error-banner, timer-display, timer-start, timer-pause, timer-reset,
study-form, expense-form, sessions-section, expenses-section,
study-chart, expense-chart
Server messages use class `flash-*`. JS messages use `js-message-*`. Never mix them.

## Setup facts
Python 3.10+. DEFAULT_USER_ID = 1. The database setup must create user 1
(demo_student) or the first form submit fails. Chart.js loads from a CDN in base.html.
