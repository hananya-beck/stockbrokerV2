---
title: Backtest simulator — product brief
status: final
created: 2026-10-22
updated: 2026-10-22
---

# Product Brief: Backtest simulator

## The Problem

The dashboard ranks 7 TASE funds and suggests a monthly ₪ split by a heuristic — a risk-adjusted score blended across 1/3/5-year windows (25/35/40 weighting), explicitly flagged in the repo's own docs as "not validated." Right now there's no way to check whether following that suggested split would actually have beaten the obvious baseline (an equal split across all 7 funds) — the score is trusted on faith, or not trusted at all, with nothing in between.

## What This Adds

A backtest view: pick a start date and a monthly deposit amount, and see what *today's* suggested allocation would have returned if applied unchanged over that historical period, plotted against an equal-weight baseline on the same chart.

This deliberately does **not** test whether the scoring algorithm itself would have recommended something different at each point in the past — it tests today's one fixed split against history. See `addendum.md` for why that narrower scope was chosen over the alternative.

## Who This Serves

Just Hananya, the sole user and maintainer of this dashboard. One-time (or occasional) sanity check, not a recurring workflow to design around.

## Success Criteria

Hananya can look at the chart once and form an honest opinion on whether the risk-adjusted score is worth trusting with real money, or whether it's no better than an equal split. Nothing more is riding on this — there's no target return, no adoption metric, no second user to satisfy.

## Scope

**In:**
- Pick a start date and a monthly deposit amount; run the simulation.
- Apply the fund list's current `suggested_weight` for every fund, unchanged, across the whole backtest range.
- Render cumulative portfolio value as a line chart, with the equal-weight baseline always shown alongside it.
- Handle funds with incomplete history for the selected range without crashing or silently zeroing their weight (see `homework/lesson2/exercise-1.md` for the exact EARS requirement).

**Out:**
- Recomputing the score or suggested weight as of each historical month (see `addendum.md`).
- Any account, saved-run, or sharing feature — single-session use is enough.
- Backtesting any allocation other than "today's suggested weights" vs. "equal weight."

## Constraint

Even this narrower scope needs a historical NAV series per fund, and none is currently stored: `scripts/fetch_data.py` fetches the full daily series from bizportal on every run, but only ever persists the computed trailing metrics to `data/funds.json` — the raw series is discarded after use. Populating that history has to go through the existing daily GitHub Actions pipeline (the only process allowed to reach bizportal), not a client-side fetch from `index.html` — consistent with this repo's no-backend, static-site constraints (`AGENTS.md`). How exactly that gets backfilled and stored is a question for the PRD/architecture phase, not this brief.

## Open Questions

- How far back can the backtest range go, given funds have different amounts of trading history (the newest fund's start date is the practical floor)?
- Does backfilling history require a one-time bulk pull from bizportal, and is that pull even available for dates further back than bizportal's chart endpoint currently returns?
