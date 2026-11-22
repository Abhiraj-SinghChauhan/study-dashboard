"""
routes/api.py - JSON endpoint for the JS developer. The response shape is a
contract (docs/CONTRACTS.md): change it only after agreeing with the team.
"""
from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from db import crud_operations as db
import helpers

api_bp = Blueprint("api", __name__, url_prefix="/api")

DEFAULT_USER_ID = 1
MAX_DAYS = 3650


@api_bp.route("/chart-data")
def chart_data():
    """GET /api/chart-data?days=30"""
    days_raw = request.args.get("days", "30")
    try:
        days = int(days_raw)
        if days <= 0 or days > MAX_DAYS:
            raise ValueError
    except ValueError:
        return jsonify({"error": f"'days' must be a whole number from 1 to {MAX_DAYS}, got '{days_raw}'"}), 400

    end = date.today()
    start_date = (end - timedelta(days=days - 1)).isoformat()
    end_date = end.isoformat()

    sessions = db.get_study_sessions(DEFAULT_USER_ID, start_date=start_date, end_date=end_date)
    expenses = db.get_expenses(DEFAULT_USER_ID, start_date=start_date, end_date=end_date)

    daily_study = helpers.group_study_minutes_by_date(sessions)
    running = helpers.calculate_running_total(helpers.calculate_daily_expense_totals(expenses))

    return jsonify({
        "range": {"start": start_date, "end": end_date, "days": days},
        "study": helpers.format_chart_series(daily_study, "minutes"),
        "expenses": {
            "labels": [e["date"] for e in running],
            "amounts": [e["total"] for e in running],
            "running_total": [e["running_total"] for e in running],
        },
        "expenses_by_category": helpers.group_expenses_by_category(expenses),
        "daily_study_average_minutes": helpers.calculate_daily_study_average(sessions, days),
    })