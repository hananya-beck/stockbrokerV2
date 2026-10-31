# Exercise 2 — a six-layer prompt for a relative-time feature

> Written after the fact from commit `d1d117f` and its prompt file, `prompts/exercise-2-six-layer.md`.

## The prompt

The prompt has six layers, each in its own tagged block: role, context with the reason, task, scope and done-when, format, and examples. The task was to show how long ago the funds data was refreshed, next to the "עודכן לאחרונה" date, so stale data is visible at a glance.

## What changed

- **`src/lib/formatting.js`:** new pure function `formatRelativeTime(isoDate, now)`.
  - It takes `now` as a parameter instead of calling `Date.now()`, so it is testable.
  - Under 60 seconds it returns "ממש עכשיו". Otherwise it uses `Intl.RelativeTimeFormat('he', { numeric: 'auto' })`, so one day ago reads "אתמול".
  - An unparseable date returns an empty string.
- **`tests/js/formatting.test.js`:** four tests covering "just now", minutes/hours/days, "yesterday", and an invalid date.
- **`index.html`:** the `#updated` span now shows the relative time in parentheses after the absolute date. Five lines changed.

## Scope the prompt set

Out of scope: no new dependencies, no network or storage calls, no changes to `scripts/fetch_data.py`, `data/`, or the table, and no fixing of other bugs seen along the way. The prompt's done-when condition was `npm run check` green. The commit doesn't record that run's output.
