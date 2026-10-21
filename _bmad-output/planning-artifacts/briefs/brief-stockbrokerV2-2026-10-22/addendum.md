---
title: Backtest simulator — addendum
created: 2026-10-22
updated: 2026-10-22
---

# Addendum: Backtest simulator

## Rejected alternative: point-in-time recomputed weights

The original EARS draft (`homework/lesson2/exercise-1.md`) reads naturally as "apply *that month's* suggested allocation weights." Taken literally, that means re-deriving `risk_adjusted_score` and `suggested_weight` as of every historical month, using only NAV data available up to that point.

That version answers a different, more interesting question: has the scoring algorithm itself been adding value over time, not just today's snapshot? But it requires a full backfilled daily NAV history per fund *and* replaying `compute_metrics`/`allocate_weights` at every historical point — effectively a second data pipeline, and its own epic.

Rejected for v1 on scope grounds, not because it's a bad idea — Hananya's own framing (trust/validation motivation) would arguably be better served by it eventually. Revisit as a v3 candidate once the historical NAV series itself exists from this epic's work.

## Why this is a passion-project-sized brief

Audience is Hananya alone, one-time use, no target metric beyond "do I trust this score or not." That ruled out sections like Executive Summary, differentiation, and a multi-year vision — right-sized rigor for a solo dashboard feature, not an investor-grade brief.
