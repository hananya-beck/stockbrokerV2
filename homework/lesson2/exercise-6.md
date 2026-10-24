# Exercise 6 — Phase 2: the PRD, with John

> Slide 40. Took the approved backtest brief (`homework/lesson2/exercise-5.md`) to
> `bmad-agent-pm` → **PRD** (`bmad-prd`), Create intent.

## How this run was done

- Run by the assistant under the instruction to make the calls and record them, not as
  a coached session with John. The brief's open questions were settled as recorded
  decisions, not discussed with Hananya.
- Every product decision and assumption is logged in the run's `.memlog.md`, so each can
  be confirmed or reversed.

## Decisions taken (in `.memlog.md`)

- **Scope held to the brief:** today's suggested weights applied unchanged over history,
  against an equal-weight baseline. Point-in-time recomputed weights stay out.
- **History floor:** the earliest month from which every fund has NAV data. This answers
  the brief's first open question as a rule; the actual depth depends on the backfill.
- **Pipeline owns history:** the daily pipeline persists each fund's NAV series, and the
  backfill runs through it. `index.html` makes no bizportal request.
- **Gross of fees and taxes:** the result is labeled as such, with fee modelling deferred.
- **Assumed, to confirm:** deposits invested at each month's first available NAV and
  valued at its last; a month with no NAV for any fund holds the deposit as cash and is
  marked.

## What shipped

- `_bmad-output/planning-artifacts/prds/prd-stockbrokerV2-2026-10-24/prd.md` — `status: final`,
  about 1,400 words. Seven functional requirements (FR-1 to FR-7) across two features:
  the backtest run and the NAV history. One primary success metric and a counter-metric.
- `.memlog.md` — the decision and assumption trail, with a finalization entry.
- Polished through `bmad-review` (structure, then prose) before finalizing: removed
  duplicated out-of-scope text, merged two open questions, and made the History floor
  consistent with the gap handling in FR-4.

## Done-when, checked

- The PRD is under `_bmad-output/planning-artifacts/` and states the vision, users, and
  requirements without naming an implementation.
- Each requirement traces back to the brief's scope and to the EARS draft in
  `homework/lesson2/exercise-1.md`, where it is not superseded. The superseded wording,
  "that month's suggested weights," is replaced by the fixed-weights rule in FR-2.
- The exercise card's own Goal and Done-when text was not retrievable from the course
  page. These checks come from the PRD workflow's finalize steps.

## Still open

- Hananya should confirm the two assumptions above and the two open questions in the PRD
  (how far back the history floor can go, and whether the stored history size is
  acceptable for GitHub Pages).
