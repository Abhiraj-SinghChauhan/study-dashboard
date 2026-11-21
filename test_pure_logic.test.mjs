import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { StudyTimer, formatElapsed } from './static/js/timer.js';
import { buildStudyBarConfig, buildExpensePieConfig } from './static/js/charts.js';

const fixture = JSON.parse(readFileSync('./static/js/fixture.json', 'utf8'));

test('formatElapsed formats seconds, minutes, and hours correctly', () => {
  assert.equal(formatElapsed(0), '00:00');
  assert.equal(formatElapsed(59_000), '00:59');
  assert.equal(formatElapsed(60_000), '01:00');
  assert.equal(formatElapsed(3_661_000), '01:01:01');
});

test('StudyTimer excludes paused time from elapsed total', () => {
  const realNow = Date.now;
  let t = 0;
  Date.now = () => t;
  const timer = new StudyTimer(() => {});
  timer.start(); t += 3000; timer.pause(); t += 50_000; timer.start(); t += 2000; timer.pause();
  assert.equal(timer.getElapsedMs(), 5000);
  Date.now = realNow;
});

test('StudyTimer.reset() zeroes elapsed time and reports it via onTick', () => {
  const seen = [];
  const timer = new StudyTimer((ms) => seen.push(ms));
  timer.start(); timer.reset();
  assert.equal(timer.getElapsedMs(), 0);
  assert.equal(seen[seen.length - 1], 0);
});

test('buildStudyBarConfig maps fixture into a bar config', () => {
  const c = buildStudyBarConfig(fixture);
  assert.equal(c.type, 'bar');
  assert.deepEqual(c.data.labels, ['2026-11-19']);
  assert.deepEqual(c.data.datasets[0].data, [90]);
});

test('buildExpensePieConfig maps fixture into a pie config', () => {
  const c = buildExpensePieConfig(fixture);
  assert.equal(c.type, 'pie');
  assert.deepEqual(c.data.labels, ['Food', 'Transport']);
  assert.deepEqual(c.data.datasets[0].data, [150, 40]);
  assert.equal(c.data.datasets[0].backgroundColor.length, 2);
});

test('buildExpensePieConfig handles an empty category list', () => {
  const c = buildExpensePieConfig({ expenses_by_category: { labels: [], values: [] } });
  assert.deepEqual(c.data.labels, []);
});

test('fixture.json has every key the contract lists', () => {
  for (const k of ['range','study','expenses','expenses_by_category','daily_study_average_minutes']) assert.ok(k in fixture, k);
});

test('fetchChartData reads fixture URL in fixture mode', async () => {
  const urls = [];
  globalThis.fetch = async (u) => { urls.push(String(u)); return { ok: true, json: async () => fixture }; };
  const { fetchChartData } = await import('./static/js/app_api.js');
  const data = await fetchChartData(30);
  assert.ok(urls[0].endsWith('/static/js/fixture.json'), urls[0]);
  assert.deepEqual(data, fixture);
});
