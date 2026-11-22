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
study-chart, expense-chart,
stat-study, stat-spent, stat-average
Server messages use class `flash-*`. JS messages use `js-message-*`. Never mix them.

## Setup facts
Python 3.10+. DEFAULT_USER_ID = 1. The database setup must create user 1
(demo_student) or the first form submit fails. Chart.js loads from a CDN in base.html.

## UI polish additions (additive, nothing above changed)
- New element IDs (HTML to JS): stat-study, stat-spent, stat-average.
  JS fills them from /api/chart-data (30 days): total study time, total spent, daily_study_average_minutes.
- Tables: rows come newest first. Every row after the 2nd gets class="extra-row" (hidden until "Show all").
  The "Show all" checkbox, label and wrapper markup stay exactly as in dashboard_mockup.html.
- Status badge: <span class="status-badge status-{status}"> where {status} is planned, in_progress, completed or skipped.
- Empty table: <p class="empty-state">...</p> instead of the table.
- Server messages render as <ul class="flashes"><li class="flash flash-{category}">. JS banner: id js-error-banner (JS sets class js-message-banner + js-message-*).
