# Exercise 5 — Phase 1: the brief, with Mary

> Slide 39. Brought the v2 goal (backtest simulator, `homework/lesson2/exercise-1.md`)
> to `bmad-agent-analyst` → **CB** (`bmad-product-brief`), Coaching path.

## What Mary pushed back on

- **The EARS draft assumed data that doesn't exist.** "Apply that month's suggested
  allocation weights" implies either a stored historical NAV series or point-in-time
  recomputed scores — neither exists. `scripts/fetch_data.py` fetches the full daily
  series every run but only persists the computed trailing metrics; the raw series is
  discarded. Settled on testing *today's* fixed weights retroactively, not re-deriving
  the score at each historical point — the bigger version is a rejected alternative in
  `addendum.md`, flagged as a plausible v3 once this epic's history data exists.
- **Motivation, named plainly rather than assumed:** trust/validation — sanity-check
  whether the risk-adjusted score beats naive equal-weighting before trusting it with
  real money, not just a course exercise.
- **Audience and stakes, right-sized the brief itself:** just Hananya, one-time sanity
  check. Ruled out Executive Summary, differentiation, and a multi-year Vision section
  from the template — a solo dashboard feature isn't an investor pitch.

## What shipped

- `_bmad-output/planning-artifacts/briefs/brief-stockbrokerV2-2026-10-22/brief.md` —
  Problem, What This Adds, Who This Serves, Success Criteria, Scope (in/out), a named
  Constraint (no stored NAV history today), Open Questions. `status: final`.
- `addendum.md` — the rejected point-in-time-weights alternative, and why the brief
  skips investor-grade sections.
- `.memlog.md` — every decision (working mode, scope settlement, draft, polish,
  approval) logged as it happened, per the skill's audit-trail requirement.
- Polished via `bmad-review` (structure + prose lenses) on both files before finalizing:
  trimmed a redundant clause in `brief.md`'s "Who This Serves" (already covered more
  precisely in Scope/Out), deduped "today's current" → "today's", and split a run-on
  opening sentence in `addendum.md`.

## Done-when, checked

- The brief is under `_bmad-output/planning-artifacts/` and committed.
- It states the problem, constraints and success criteria — and names no
  implementation (the Constraint section flags the missing data, doesn't prescribe
  how to store it; that's explicitly left for PRD/architecture).
- Every assumption Mary flagged was confirmed or corrected by Hananya, not accepted
  silently: the backtest's exact scope (today's weights vs. point-in-time recompute)
  and the motivation behind it were both decided in conversation, not assumed.
