// Pure helpers for the on-demand "refresh data" flow. No fetch, no DOM — the
// network calls live in index.html; this module only interprets their results.

/**
 * @typedef {Object} WorkflowRun
 * @property {number} id
 * @property {string} event - e.g. "workflow_dispatch", "schedule".
 * @property {string} status - "queued" | "in_progress" | "completed" | ...
 * @property {string | null} conclusion - "success" | "failure" | "cancelled" | ... once completed.
 * @property {string} created_at - ISO 8601 timestamp.
 */

/**
 * @typedef {Object} RefreshState
 * @property {'running' | 'success' | 'failed'} phase
 * @property {string} message - Hebrew status text for the UI.
 */

/**
 * Read the run id from a workflow dispatch response body. Since REST API
 * version 2026-03-10 the dispatch endpoint answers 200 with
 * `{ workflow_run_id, run_url, html_url }`; older versions answer 204 with no body.
 * @param {unknown} body - Parsed JSON body, or null when there was none.
 * @returns {number | null} The run id, or null if the body doesn't carry a valid one.
 */
export function dispatchedRunId(body) {
  if (!body || typeof body !== 'object') return null;
  const id = /** @type {{ workflow_run_id?: unknown }} */ (body).workflow_run_id;
  return Number.isSafeInteger(id) && /** @type {number} */ (id) > 0 ? /** @type {number} */ (id) : null;
}

/**
 * Pick the workflow_dispatch run that started after the click. Fallback for
 * when the dispatch response carries no run id (see `dispatchedRunId`): match by
 * creation time, with `skewMs` absorbing clock drift between browser and GitHub.
 * @param {WorkflowRun[]} runs
 * @param {Date} dispatchedAt - Browser time just before the dispatch request.
 * @param {number} [skewMs]
 * @returns {WorkflowRun | null} The earliest matching run, or null if none yet.
 */
export function pickDispatchedRun(runs, dispatchedAt, skewMs = 30_000) {
  const cutoff = dispatchedAt.getTime() - skewMs;
  let best = null;
  for (const run of runs) {
    if (run.event !== 'workflow_dispatch') continue;
    const created = new Date(run.created_at).getTime();
    if (Number.isNaN(created) || created < cutoff) continue;
    if (!best || created < new Date(best.created_at).getTime()) best = run;
  }
  return best;
}

/** @type {Record<import('./i18n.js').Lang, { starting: string, computing: string, loading: string, failed: (c: string) => string }>} */
const RUN_STATE_TEXT = {
  he: { starting: 'מפעיל…', computing: 'מחשב…', loading: 'טוען נתונים…', failed: (c) => `הריצה נכשלה (${c})` },
  en: { starting: 'Starting…', computing: 'Computing…', loading: 'Loading data…', failed: (c) => `Run failed (${c})` },
};

/**
 * Map a workflow run (or its absence) to a UI state.
 * @param {WorkflowRun | null} run - null while the run hasn't appeared yet.
 * @param {import('./i18n.js').Lang} [lang]
 * @returns {RefreshState}
 */
export function describeRunState(run, lang = 'he') {
  const text = RUN_STATE_TEXT[lang] ?? RUN_STATE_TEXT.he;
  if (!run) return { phase: 'running', message: text.starting };
  if (run.status !== 'completed') return { phase: 'running', message: text.computing };
  if (run.conclusion === 'success') return { phase: 'success', message: text.loading };
  return { phase: 'failed', message: text.failed(run.conclusion ?? 'unknown') };
}

/** @type {Record<import('./i18n.js').Lang, Record<number, string>>} */
const API_ERROR_TEXT = {
  he: {
    401: 'הטוקן לא תקין או שפג תוקפו (401)',
    403: 'לטוקן אין הרשאה מתאימה (403)',
    404: 'הריפו או ה-workflow לא נמצאו, או שלטוקן אין גישה (404)',
    422: 'GitHub דחה את הבקשה (422)',
  },
  en: {
    401: 'Token is invalid or expired (401)',
    403: 'Token lacks the required permission (403)',
    404: 'Repo or workflow not found, or the token lacks access (404)',
    422: 'GitHub rejected the request (422)',
  },
};

/** @type {Record<import('./i18n.js').Lang, (status: number) => string>} */
const DEFAULT_API_ERROR = {
  he: (status) => `שגיאת GitHub (${status})`,
  en: (status) => `GitHub error (${status})`,
};

/**
 * Explanation for a failed GitHub API response.
 * @param {number} status - HTTP status code.
 * @param {import('./i18n.js').Lang} [lang]
 * @returns {string}
 * @example describeApiError(404, 'he') // => 'הריפו או ה-workflow לא נמצאו, או שלטוקן אין גישה (404)'
 */
export function describeApiError(status, lang = 'he') {
  const text = API_ERROR_TEXT[lang] ?? API_ERROR_TEXT.he;
  return text[status] ?? (DEFAULT_API_ERROR[lang] ?? DEFAULT_API_ERROR.he)(status);
}

/**
 * Query string for the fallback run-list poll: workflow_dispatch runs on main
 * created since the click, minus `skewMs` for clock drift (matches `pickDispatchedRun`).
 * @param {Date} dispatchedAt - Browser time just before the dispatch request.
 * @param {number} [skewMs]
 * @returns {string}
 */
export function dispatchedRunsQuery(dispatchedAt, skewMs = 30_000) {
  const created = `>=${new Date(dispatchedAt.getTime() - skewMs).toISOString()}`;
  return `event=workflow_dispatch&branch=main&created=${encodeURIComponent(created)}&per_page=10`;
}

/**
 * Whether the poll loop has run out of time.
 * @param {number} startedAtMs
 * @param {number} nowMs
 * @param {number} timeoutMs
 * @returns {boolean}
 */
export function isPastDeadline(startedAtMs, nowMs, timeoutMs) {
  return nowMs - startedAtMs > timeoutMs;
}
