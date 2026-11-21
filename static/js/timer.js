/**
 * timer.js — Study session stopwatch.
 *
 * DESIGN NOTE: the elapsed time is NEVER computed by counting how many
 * ticks have fired (`ticks * intervalMs`). setInterval does not guarantee
 * it fires exactly on schedule — a backgrounded tab, a slow paint, or a
 * busy main thread can delay or coalesce ticks. Counting ticks accumulates
 * that drift permanently. Instead, every tick re-derives elapsed time from
 * real wall-clock timestamps (Date.now()), so a late or skipped tick only
 * delays *when* the display updates, never *what* it reports.
 */

export class StudyTimer {
  /** @param {(elapsedMs: number) => void} onTick called on every tick and on reset */
  constructor(onTick) {
    this.onTick = onTick;
    this.intervalId = null;
    this.startTimestamp = null; // Date.now() when the current run segment began
    this.accumulatedMs = 0;     // time banked from previous run segments (pre-pause)
    this.state = "idle";        // "idle" | "running" | "paused"
  }

  start() {
    if (this.state === "running") return;
    this.startTimestamp = Date.now();
    this.state = "running";
    this.intervalId = setInterval(() => this._tick(), 250);
  }

  pause() {
    if (this.state !== "running") return;
    this.accumulatedMs += Date.now() - this.startTimestamp;
    clearInterval(this.intervalId);
    this.intervalId = null;
    this.state = "paused";
    this._tick();
  }

  reset() {
    clearInterval(this.intervalId);
    this.intervalId = null;
    this.startTimestamp = null;
    this.accumulatedMs = 0;
    this.state = "idle";
    if (this.onTick) this.onTick(0);
  }

  /** Elapsed time in ms, correct whether running, paused, or idle. */
  getElapsedMs() {
    if (this.state === "running") {
      return this.accumulatedMs + (Date.now() - this.startTimestamp);
    }
    return this.accumulatedMs;
  }

  /** Rounded whole minutes, for submitting to POST /log-study. */
  getElapsedMinutesRounded() {
    return Math.round(this.getElapsedMs() / 60000);
  }

  _tick() {
    if (this.onTick) this.onTick(this.getElapsedMs());
  }
}

/** Format milliseconds as "MM:SS", or "HH:MM:SS" past one hour. */
export function formatElapsed(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return hours > 0
    ? `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`
    : `${pad(minutes)}:${pad(seconds)}`;
}
