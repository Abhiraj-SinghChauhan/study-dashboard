/**
 * app_api.js — All fetch() calls to the Flask backend live here, and
 * nowhere else. Nothing in main.js, timer.js, or charts.js should ever
 * call fetch() directly — this is the one file that knows the backend's
 * URLs and response shapes.
 */

// ===== SWITCH =====================================================
// true  = read static/js/fixture.json (use until the Flask API exists)
// false = read the real GET /api/chart-data?days=30 from Flask
const USE_FIXTURE = true;
// ==================================================================

// Resolved relative to THIS file, so it works from python3 -m http.server
// and from Flask (/static/js/fixture.json) without changing anything.
const FIXTURE_URL = new URL("./fixture.json", import.meta.url).href;

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function fetchChartData(days = 30) {
  const url = USE_FIXTURE
    ? FIXTURE_URL
    : `/api/chart-data?days=${encodeURIComponent(days)}`;
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(body.error || `Request failed with status ${response.status}`, response.status);
  }
  return response.json();
}

/**
 * POST to a form-handling route (/add-expense, /log-study). These routes
 * flash a message and redirect (302) on BOTH success and validation
 * failure, ending at the same 200 either way once fetch follows the
 * redirect. response.ok can't tell those two outcomes apart -- so this
 * reads the returned page for a .flash-error element, the one signal that
 * actually distinguishes them.
 *
 * Server messages use class "flash-*"; JS messages use "js-message-*"
 * (see CONTRACTS.md). Never mix them, or this selector would match the
 * JS-owned banner and report every success as a failure.
 *
 * On success, returns the freshly-rendered index page (parsed as a
 * Document) so main.js can pull updated table markup into the live page
 * without a full reload.
 */
async function submitForm(path, data) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(data).toString(),
  });
  if (!response.ok) {
    throw new ApiError(`Request failed with status ${response.status}`, response.status);
  }
  const html = await response.text();
  const doc = new DOMParser().parseFromString(html, "text/html");
  const errorFlash = doc.querySelector(".flash-error");
  if (errorFlash) {
    throw new ApiError(errorFlash.textContent.trim(), response.status);
  }
  return doc;
}

export function submitExpense(data) {
  return submitForm("/add-expense", data);
}

export function submitStudySession(data) {
  return submitForm("/log-study", data);
}
