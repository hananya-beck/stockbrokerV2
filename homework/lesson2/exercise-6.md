# Exercise 6 — Phase 2: the PRD, with John

> Slide 40. Took the approved backtest brief (`homework/lesson2/exercise-5.md`) to
> `bmad-agent-pm` → **PRD** (`bmad-prd`), Create intent. Then ran it again in Validate
> mode and fixed what it found.

## How this run was done

- Run by the assistant under the instruction to make the calls and record them, not as
  a coached session with John. The brief's open questions were settled as recorded
  decisions, not discussed with Hananya.
- Every product decision and assumption is logged in the run's `.memlog.md`, so each can
  be confirmed or reversed.

## Decisions taken (in `.memlog.md`)

- **Scope held to the brief:** today's suggested weights applied unchanged over history,
  against an equal-weight baseline. Point-in-time recomputed weights stay out, and the PRD
  says so: the MVP cannot show whether the scoring method added value over time.
- **History floor:** the earliest month from which every fund has NAV data. A backtest
  needs at least 6 months, the shortest horizon the scoring already uses. A 12-month
  minimum would have disabled the run today, since the newest fund has about 9 to 10
  months of history.
- **Gap rules:** a fund's units carry their last known NAV forward. A missing fund's
  baseline share is redistributed the same way as its suggested weight, so both lines
  follow one rule. The current, incomplete month is excluded.
- **Pipeline owns history:** the daily pipeline persists each fund's NAV series. The
  source already returns the full series each run, so the first run stores the history
  and no separate backfill is needed. `index.html` makes no bizportal request.
- **Gross of fees and taxes:** the chart and final values say so, and fee modelling is
  deferred.
- **Decided on owner delegation (2026-10-25):** deposits invested at each month's first
  available NAV; a month with no NAV for any fund holds the deposit as cash and is marked;
  the 6-month minimum; and the 5 MB and 2-second targets, which stand.

## What shipped

- `_bmad-output/planning-artifacts/prds/prd-stockbrokerV2-2026-10-24/prd.md` — `status: final`,
  about 1,950 words. Seven functional requirements (FR-1 to FR-7) across two features, the
  backtest run and the NAV history. Two primary success metrics (a usability check and a
  fixture check) and one counter-metric.
- `validation-report.md` — the Validate report. Its markdown twin records the 19 findings
  by severity and how each was handled.
- `review-rubric.md` — the full rubric review from the validation subagent.
- `.memlog.md` — the decision, assumption and change trail.

## Validate pass

- A rubric-walker subagent reviewed the PRD on its own, not anchored on the draft. It
  found 0 critical, 6 high, 4 medium and 9 low findings, with Done-ness clarity rated thin.
- The high findings were the in-sample hindsight bias, the unnamed point-in-time trade-off,
  the history floor, gap valuation, baseline gap handling, and backfill mechanics.
- Every finding was fixed in the PRD. The 5 MB bound it raised is now answered from the
  data, and the later data check changed two of the earlier fixes; both are noted in
  `validation-report.md`.
- The HTML report from the template was not generated. The markdown twin is the record.
- I did not re-run Validate after the fixes, so the grade is not re-scored.

## Done-when, checked

- The PRD is under `_bmad-output/planning-artifacts/` and states the vision, users, and
  requirements without naming an implementation.
- Each requirement traces back to the brief's scope and to the EARS draft in
  `homework/lesson2/exercise-1.md`, where it is not superseded. The superseded wording,
  "that month's suggested weights," is replaced by the fixed-weights rule in FR-2.
- The exercise card's own Goal and Done-when text was not retrievable from the course
  page. These checks come from the PRD workflow's finalize and validate steps.

## Open questions, answered

- **How far back does the source return NAV?** About 1,230 trading days (roughly 4.9
  years) for the five older funds, and 240 and 200 for the two newest. The history floor
  is set by the newest fund, about 9 to 10 months back today.
- **Does the stored history fit 5 MB?** Yes. The seven series total 6,587 points, about
  165 KB as JSON. This is an estimate from the point count, not a measured size.
- The owner delegated these decisions, so nothing is waiting on Hananya.
