"""
helpers.py - Business-logic layer: turns raw DB rows (from db/crud_operations.py)
into the shapes templates and the JSON API need, and validates request data.
No SQL and no Flask request/response objects here, so everything is easy to test.
"""
import math
from collections import defaultdict
from datetime import date

VALID_STATUSES = {"planned", "in_progress", "completed", "skipped"}


# ---------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------
def calculate_daily_expense_totals(expenses: list[dict]) -> list[dict]:
    """One total per calendar day, sorted oldest first, whatever the input order."""
    totals_by_date: dict = defaultdict(float)
    for expense in expenses:
        totals_by_date[expense["expense_date"]] += expense["amount"]
    return [
        {"date": d, "total": round(total, 2)}
        for d, total in sorted(totals_by_date.items())
    ]


def calculate_running_total(daily_totals: list[dict]) -> list[dict]:
    """Add a cumulative running_total to daily totals given in ascending date order."""
    running = 0.0
    result = []
    for entry in daily_totals:
        running += entry["total"]
        result.append({**entry, "running_total": round(running, 2)})
    return result


def group_study_minutes_by_date(sessions: list[dict]) -> list[dict]:
    """Total COMPLETED minutes per day, oldest first. Planned/skipped don't count."""
    minutes_by_date: dict = defaultdict(int)
    for s in sessions:
        if s["status"] == "completed":
            minutes_by_date[s["session_date"]] += s["duration_minutes"]
    return [{"date": d, "minutes": m} for d, m in sorted(minutes_by_date.items())]


def calculate_daily_study_average(sessions: list[dict], num_days: int) -> float:
    """Average completed study minutes per day across the whole period."""
    if num_days <= 0:
        raise ValueError("num_days must be positive")
    completed_minutes = sum(
        s["duration_minutes"] for s in sessions if s["status"] == "completed"
    )
    return round(completed_minutes / num_days, 1)


def group_expenses_by_category(expenses: list[dict]) -> dict:
    """Total spent per category as {"labels": [...], "values": [...]}, biggest first."""
    totals: dict = defaultdict(float)
    for e in expenses:
        totals[e["category_name"]] += e["amount"]
    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return {
        "labels": [name for name, _ in ordered],
        "values": [round(total, 2) for _, total in ordered],
    }


def format_chart_series(daily_data: list[dict], value_key: str) -> dict:
    """Reshape [{"date": ..., value_key: ...}] into {"labels": [...], "values": [...]}."""
    return {
        "labels": [entry["date"] for entry in daily_data],
        "values": [entry[value_key] for entry in daily_data],
    }


# ---------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------
class ValidationError(Exception):
    """Raised when incoming request data fails validation. Routes catch this
    and turn it into a flashed message + redirect, never a 500."""


def _text(data, field: str) -> str:
    return str(data.get(field) or "").strip()


def _read_date(data, field: str, errors: list) -> str:
    value = _text(data, field)
    if not value:
        errors.append(f"{field} is required")
        return ""
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        errors.append(f"{field} must look like 2026-11-24, got '{value}'")
        return ""


def validate_expense_input(data) -> dict:
    """Return a clean typed dict or raise ValidationError listing every problem."""
    errors = []

    category_name = _text(data, "category_name")
    if not category_name:
        errors.append("category_name is required")

    expense_date = _read_date(data, "expense_date", errors)

    amount_raw = data.get("amount")
    amount = None
    if amount_raw in (None, ""):
        errors.append("amount is required")
    else:
        try:
            amount = float(amount_raw)
            if not math.isfinite(amount):
                errors.append(f"amount must be a number, got '{amount_raw}'")
            elif amount <= 0:
                errors.append("amount must be greater than 0")
        except (TypeError, ValueError):
            errors.append(f"amount must be a number, got '{amount_raw}'")

    if errors:
        raise ValidationError("; ".join(errors))
    return {
        "amount": amount,
        "category_name": category_name,
        "expense_date": expense_date,
        "description": _text(data, "description"),
    }


def validate_study_session_input(data) -> dict:
    """Return a clean typed dict or raise ValidationError listing every problem."""
    errors = []

    subject_name = _text(data, "subject_name")
    if not subject_name:
        errors.append("subject_name is required")

    session_date = _read_date(data, "session_date", errors)

    duration_raw = data.get("duration_minutes")
    duration = None
    if duration_raw in (None, ""):
        errors.append("duration_minutes is required")
    else:
        try:
            duration = int(duration_raw)
            if duration <= 0:
                errors.append("duration_minutes must be greater than 0")
        except (TypeError, ValueError):
            errors.append(f"duration_minutes must be a whole number, got '{duration_raw}'")

    status = _text(data, "status") or "planned"
    if status not in VALID_STATUSES:
        errors.append(f"status must be one of {sorted(VALID_STATUSES)}")

    if errors:
        raise ValidationError("; ".join(errors))
    return {
        "subject_name": subject_name,
        "session_date": session_date,
        "duration_minutes": duration,
        "status": status,
    }