# Exercise 2 — A three-line brief that ships a feature

> Slide 34. Feature: **sortable fund-table columns** (click a header to sort
> by that column, ascending/descending, with an arrow indicator).

## The brief

- **Task:** Make each fund-table column header clickable to sort the table by that column's value, toggling ascending/descending on repeated clicks, with a visual indicator (▲/▼) on the active sort column.
- **Guardrails:** Don't touch `src/lib/`, `scripts/fetch_data.py`, or `data/funds.json`; no new dependencies; only `index.html` and `src/styles/tokens.css` if a genuinely new token is needed.
- **Done when:** `npm run check` passes, and clicking a header sorts the table correctly in both directions (verified live in the browser).

## What shipped

Each header is now a `<button>` wrapping its label span and a sort-indicator span. Clicking it sorts `data.funds` by that column's raw metric (not the formatted display string), with `null`/`undefined` values always sorted last regardless of direction, and ties broken by original order for stability. `colWeight` and `colAmount` share one accessor since amount is a monotonic function of weight for a fixed deposit.

- `npm run check`: typecheck, lint and all 42 JS tests passed, unchanged — this feature lives entirely in `index.html`.
- Verified live with a throwaway Playwright script against a local `python -m http.server`: clicking the score column sorted ascending (`-0.29 → 1.35`) then descending on a second click, the indicator flipped ▲/▼, clicking the fund-name column sorted correctly by Hebrew string, and there were zero console/page errors. The script and the locally-regenerated `data/funds.json` it needed were both discarded afterward — the latter is bot-owned and shouldn't be hand-committed.

**Assumption checked:** that amount and weight sort identically for a fixed deposit. Verified by reading `computeAllocationAmount` — it's `Math.round(weight * totalAmount)`, monotonic in `weight` for any fixed `totalAmount` — so reusing `colWeight`'s accessor for `colAmount` is correct, not just a guess.
