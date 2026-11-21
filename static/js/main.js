/**
 * main.js — Wires timer.js, charts.js, and app_api.js to the actual page
 * markup. This is the only file that assumes specific element IDs exist —
 * everything it imports is markup-agnostic and reusable on its own.
 */
import { StudyTimer, formatElapsed } from "./timer.js";
import { DashboardCharts } from "./charts.js";
import { fetchChartData, submitExpense, submitStudySession, ApiError } from "./app_api.js";

function showMessage(message, kind) {
  const banner = document.getElementById("js-error-banner");
  banner.textContent = message;
  banner.className = kind === "success" ? "js-message-banner js-message-success" : "js-message-banner js-message-error";
  banner.hidden = false;
}

function showError(message) {
  showMessage(message, "error");
}

function clearError() {
  const banner = document.getElementById("js-error-banner");
  banner.hidden = true;
  banner.textContent = "";
}

/** Pull the flash message Flask set for this request out of the freshly
 * fetched page -- it was consumed from the session the moment the
 * redirect was followed, so this is the only chance to show it. */
function extractFlash(freshDoc, selector) {
  const el = freshDoc.querySelector(selector);
  return el ? el.textContent.trim() : null;
}

/** Replace a section's content with the same section pulled from a fresh
 * page fetched from OUR OWN server (already Jinja2-escaped) -- a different
 * trust boundary than inserting raw form data, which always goes through
 * textContent instead. */
function swapSection(freshDoc, sectionId) {
  const fresh = freshDoc.getElementById(sectionId);
  const current = document.getElementById(sectionId);
  if (fresh && current) {
    current.innerHTML = fresh.innerHTML;
  }
}

async function refreshCharts(charts) {
  try {
    const data = await fetchChartData(30);
    charts.render(data);
  } catch (err) {
    // Covers three distinct failure modes identically: a non-200 API
    // response (ApiError), the network/fetch itself failing (TypeError),
    // and a response body that isn't valid JSON (SyntaxError from
    // response.json()) -- all land here, none crash the page.
    showError("Could not load chart data: " + err.message);
  }
}

function initTimer() {
  const display = document.getElementById("timer-display");
  const timer = new StudyTimer((elapsedMs) => {
    display.textContent = formatElapsed(elapsedMs);
  });
  document.getElementById("timer-start").addEventListener("click", () => timer.start());
  document.getElementById("timer-pause").addEventListener("click", () => timer.pause());
  document.getElementById("timer-reset").addEventListener("click", () => timer.reset());
  return timer;
}

function initStudyForm(timer, charts) {
  const form = document.getElementById("study-form");
  const durationField = form.querySelector("[name=duration_minutes]");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();

    if (timer.getElapsedMs() > 0) {
      durationField.value = timer.getElapsedMinutesRounded();
    }
    const formData = Object.fromEntries(new FormData(form).entries());

    if (!formData.subject_name?.trim()) return showError("Subject is required.");
    if (!formData.session_date) return showError("Date is required.");
    const minutes = Number(formData.duration_minutes);
    if (!Number.isFinite(minutes) || minutes <= 0) {
      return showError("Duration must be a positive number of minutes.");
    }

    try {
      const freshDoc = await submitStudySession(formData);
      swapSection(freshDoc, "sessions-section");
      form.reset();
      timer.reset();
      showMessage(extractFlash(freshDoc, ".flash-success") || "Session logged.", "success");
      await refreshCharts(charts);
    } catch (err) {
      showError(err instanceof ApiError ? err.message : "Could not log session: " + err.message);
    }
  });
}

function initExpenseForm(charts) {
  const form = document.getElementById("expense-form");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    const formData = Object.fromEntries(new FormData(form).entries());

    if (!formData.category_name?.trim()) return showError("Category is required.");
    const amount = Number(formData.amount);
    if (!Number.isFinite(amount) || amount <= 0) return showError("Amount must be a positive number.");
    if (!formData.expense_date) return showError("Date is required.");

    try {
      const freshDoc = await submitExpense(formData);
      swapSection(freshDoc, "expenses-section");
      form.reset();
      showMessage(extractFlash(freshDoc, ".flash-success") || "Expense added.", "success");
      await refreshCharts(charts);
    } catch (err) {
      showError(err instanceof ApiError ? err.message : "Could not add expense: " + err.message);
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  const charts = new DashboardCharts(
    document.getElementById("study-chart"),
    document.getElementById("expense-chart"),
  );
  const timer = initTimer();
  initStudyForm(timer, charts);
  initExpenseForm(charts);
  await refreshCharts(charts);
});
