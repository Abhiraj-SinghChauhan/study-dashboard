/**
 * charts.js — Turns a GET /api/chart-data response into rendered Chart.js
 * charts. The config-building functions are pure (data in, config object
 * out) and deliberately don't touch the DOM or Chart.js's constructor, so
 * they're testable with a plain JSON fixture and no browser at all. Only
 * DashboardCharts below needs a real <canvas> and the global `Chart`
 * (loaded from a CDN in base.html).
 */

const CATEGORY_COLORS = [
  "#4c6ef5", "#f76707", "#2f9e44", "#e64980", "#ae3ec9", "#1098ad", "#f59f00",
];

/** Bar chart: minutes studied per day. */
export function buildStudyBarConfig(apiResponse) {
  return {
    type: "bar",
    data: {
      labels: apiResponse.study.labels,
      datasets: [{
        label: "Minutes studied",
        data: apiResponse.study.values,
        backgroundColor: "#4c6ef5",
      }],
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, title: { display: true, text: "Minutes" } } },
    },
  };
}

/** Pie chart: expense breakdown by category. */
export function buildExpensePieConfig(apiResponse) {
  const byCategory = apiResponse.expenses_by_category;
  return {
    type: "pie",
    data: {
      labels: byCategory.labels,
      datasets: [{
        data: byCategory.values,
        backgroundColor: byCategory.labels.map((_, i) => CATEGORY_COLORS[i % CATEGORY_COLORS.length]),
      }],
    },
    options: { responsive: true },
  };
}

export class DashboardCharts {
  constructor(studyCanvas, expenseCanvas) {
    this.studyCanvas = studyCanvas;
    this.expenseCanvas = expenseCanvas;
    this.studyChart = null;
    this.expenseChart = null;
  }

  /** Rebuild both charts from a fresh API response. Destroys the previous
   * Chart instance first -- Chart.js does not update in place from a new
   * config, and skipping destroy() leaks canvases and duplicates tooltips. */
  render(apiResponse) {
    this.studyChart?.destroy();
    this.expenseChart?.destroy();
    this.studyChart = new Chart(this.studyCanvas, buildStudyBarConfig(apiResponse));
    this.expenseChart = new Chart(this.expenseCanvas, buildExpensePieConfig(apiResponse));
  }
}
