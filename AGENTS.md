<!-- bmad:context -->
<!-- Verified 2026-10-22 against ea13f33. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## stockbrokerV2

Static dashboard (plain `index.html` + ES modules in `src/lib/`) for a monthly קרן השתלמות deposit: ranks 7 TASE funds by a risk-adjusted score and suggests a ₪ split. `scripts/fetch_data.py` (Python stdlib only) scrapes bizportal daily and writes `data/funds.json`, which `index.html` reads. Hosted as-is on GitHub Pages from `main`.

## Policy

- No build step, bundler, framework or npm runtime dependency — GitHub Pages serves the files as committed; everything must run as native ES modules.
- No leading `/` in any path — the site lives under `/stockbrokerV2/`, and a leading slash 404s on Pages.
- No secrets, tokens or personal data in the repo — the repo and site are public; the GitHub token the refresh button needs is typed in at runtime and kept only in a JS variable.
- No browser storage (`localStorage`, `sessionStorage`, IndexedDB, cookies) — a stored token would outlive the tab on a public page.
- Never hand-edit `data/funds.json` — generated and committed daily by `.github/workflows/update-data.yml`; pull before pushing, the bot may have landed a newer copy.
- Never force-push to `main` — it would wipe the bot's data commits; pull with rebase instead.

## Where things are

- Pure, unit-tested core: `src/lib/` — conventions in `src/lib/CLAUDE.md` (no fetch/DOM/timers, named exports, JSDoc, one test file per module).
- Fetch-script internals (bizportal quirks, horizon math, failure handling, test rules): `.claude/rules/fetch-script.md`, loaded when editing `scripts/**`.
- Data refresh: `.github/workflows/update-data.yml` — daily 05:00 UTC cron, plus `workflow_dispatch` from the page's refresh button.
- Colors, spacing, fonts: CSS custom properties in `src/styles/tokens.css` — never hard-code a color.
- Homework write-ups: `homework/lessonN/exercise-M.md` (earlier ones predate the lesson split and sit flat at `homework/exercise-N.md`); development prompts: `prompts/`.

## Running and verifying

- `npm run check` (typecheck + lint + JS tests) before every front-end commit — no CI job runs it; the only workflow just runs `scripts/fetch_data.py`.
- `python -m pytest tests -q` runs the Python tests.
- `python scripts/fetch_data.py` regenerates `data/funds.json` locally for testing — don't commit the result by hand.

## Conventions that differ from defaults

- UI text is Hebrew and the page is RTL — match existing wording ("רענן נתונים", "עודכן לאחרונה").
- Show every failure to the user (status text next to the control, plus an alert for auth errors like a 401) — never fail silently.

## Known pitfalls

- bizportal's endpoint is undocumented and may break or be disallowed by its terms; there's no fallback data source yet.
- The suggested-weight score is a heuristic over past returns, not financial advice — the 25/35/40 window weighting and `MIN_WEIGHT` haven't been validated.
- A block sized only by `min-width` (no `width`) inside a `<td>` collapses to that min-width under the default `table-layout: auto` — percentage fills then look visually identical across rows. Give it `width: 100%` too.

<!-- /bmad:context -->
