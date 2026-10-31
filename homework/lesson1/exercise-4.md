# Exercise 4 — a Claude 5–style prompt for an on-demand refresh button

> Written after the fact from commit `9c0e979` and its prompt file, `prompts/exercise-4-claude5-style.md`. The prompt header asks for `/effort high`.

## The prompt

The prompt is a short brief with tagged sections: context (the files to read), goal, auth, constraints, and done-when. It says what to achieve and how to prove it, not how many steps to take. The goal was a "רענן נתונים" button that triggers the daily data workflow on demand, waits for it, and re-renders the page.

## What changed

- **`index.html`:** the refresh button sits on the amount card. Clicking it:
  - dispatches the workflow through the GitHub REST API (`/actions/workflows/{WORKFLOW}/dispatches`),
  - polls the runs endpoint for `workflow_dispatch` runs on `main`,
  - loads the new `data/funds.json` from the contents API after success, not from the Pages URL, because Pages redeploys later,
  - disables the button and shows the status text while it runs, and shows the reason next to the button on failure.
- **Token handling:** the user types a fine-grained token into a password input. It is kept in a JS variable for the current tab only. Nothing goes to `localStorage`, because the project rules forbid browser storage.
- **`src/lib/refresh.js`:** pure helpers with no `fetch` and no DOM.
  - `pickDispatchedRun` matches the run that started after the click, using `created_at` with a 30-second skew allowance, because the dispatch endpoint returns no run id.
  - `describeRunState` maps a run to a state and message: "מפעיל…" before the run appears, "מחשב…" while it runs, "טוען נתונים…" on success, and the conclusion on failure.
  - `describeApiError` explains 401, 403, 404, and 422 in Hebrew.
- **`tests/js/refresh.test.js`:** ten tests across those three functions.
- **Styling:** a spinner built with a CSS animation, using existing tokens only.

## What the commit doesn't record

The done-when condition also asked for a manual check: a real token, a visible run under Actions, and a table update. The commit doesn't record that check or any other bugs found along the way.
