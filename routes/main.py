"""
routes/main.py - Page routes: the dashboard and the two form endpoints.
Only layer that translates between HTTP (request.form, redirects, flash)
and the DB layer (db.crud_operations). No SQL in here.
"""
import sqlite3

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

from db import crud_operations as db
import helpers

main_bp = Blueprint("main", __name__)

# v1 is single-user. The DB setup creates user 1 (demo_student).
DEFAULT_USER_ID = 1


@main_bp.route("/")
def index():
    sessions = db.get_study_sessions(DEFAULT_USER_ID)  # newest first
    expenses = db.get_expenses(DEFAULT_USER_ID)        # newest first
    return render_template("index.html", sessions=sessions, expenses=expenses)


@main_bp.route("/add-expense", methods=["POST"])
def add_expense():
    try:
        clean = helpers.validate_expense_input(request.form)
    except helpers.ValidationError as e:
        flash(f"Couldn't add expense: {e}", "error")
        return redirect(url_for("main.index"))

    try:
        category_id = db.get_or_create_category(clean["category_name"])
        db.add_expense(
            DEFAULT_USER_ID,
            category_id,
            clean["amount"],
            clean["expense_date"],
            clean["description"],
        )
    except sqlite3.Error as e:
        current_app.logger.error("DB error in add_expense: %s", e)
        flash("Something went wrong saving your expense. Please try again.", "error")
        return redirect(url_for("main.index"))

    flash("Expense added.", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/log-study", methods=["POST"])
def log_study():
    try:
        clean = helpers.validate_study_session_input(request.form)
    except helpers.ValidationError as e:
        flash(f"Couldn't log session: {e}", "error")
        return redirect(url_for("main.index"))

    try:
        subject_id = db.get_or_create_subject(clean["subject_name"])
        db.add_study_session(
            DEFAULT_USER_ID,
            subject_id,
            clean["session_date"],
            clean["duration_minutes"],
            clean["status"],
        )
    except sqlite3.Error as e:
        current_app.logger.error("DB error in log_study: %s", e)
        flash("Something went wrong logging your session. Please try again.", "error")
        return redirect(url_for("main.index"))

    flash("Study session logged.", "success")
    return redirect(url_for("main.index"))