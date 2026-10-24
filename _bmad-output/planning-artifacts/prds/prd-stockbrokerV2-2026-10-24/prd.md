---
title: Backtest simulator
status: final
created: 2026-10-24
updated: 2026-10-24
---

# PRD: Backtest simulator

## 0. Document Purpose

This PRD defines what the backtest simulator must do and where its scope stops. It builds on `brief-stockbrokerV2-2026-10-22/brief.md` and its `addendum.md`, which are not repeated here. The reader is Hananya, the sole user and maintainer, and whoever builds it in this repo. Requirements describe capabilities; implementation choices belong to the architecture notes.

## 1. Vision

The dashboard suggests a monthly ₪ split across 7 TASE funds from a risk-adjusted score that nobody has validated. The backtest simulator tests that suggestion against history. It applies today's suggested weights to a past period and compares the result with an equal split of the same deposits. One chart answers the question that matters: is the score worth trusting, or is it no better than splitting evenly?

## 2. Target User

### 2.1 Jobs To Be Done

- Decide whether the suggested split is worth trusting with real money, rather than trusting it on faith or ignoring it.
- Get that answer in one sitting, once or occasionally. No ongoing reporting.

### 2.2 Non-Users (v1)

Anyone other than the maintainer. There are no accounts, saved runs or sharing.

### 2.3 Key User Journeys

- **UJ-1. Hananya checks the score before trusting it.** Hananya opens the dashboard, picks a start month two years back and a ₪1,000 monthly deposit, clicks "Run backtest," and reads the chart. The suggested-allocation line finishes above or below the equal-weight line, and any months with incomplete fund data are marked.

## 3. Glossary

- **Backtest range** — the months from the chosen start month through the latest month that has NAV data for every fund.
- **History floor** — the earliest month from which every fund has NAV data. The earliest selectable start month. Individual funds can still have gaps after the floor (see FR-4).
- **Monthly deposit** — the ₪ amount invested at the start of each month in the backtest range.
- **Suggested weight** — a fund's share in the dashboard's current suggestion, read from `data/funds.json` and held fixed for the whole run.
- **Equal-weight baseline** — the same monthly deposits split evenly across all 7 funds.
- **NAV history** — the stored daily NAV series for each fund, written by the daily pipeline.
- **Cumulative value** — total deposits so far, grown by each fund's NAV change and valued at the month's last NAV.

## 4. Features

### 4.1 Backtest run

**Description:** The user chooses a start month and a monthly deposit, then runs the backtest. For each month in the range, the simulator invests that month's deposit by each fund's suggested weight, and invests the same deposit at 1/7 per fund for the baseline. Both portfolios' cumulative values are drawn on one line chart. Realizes UJ-1.

**Functional Requirements:**

#### FR-1: Choose backtest inputs

The user can choose a start month no earlier than the history floor and a positive monthly deposit in ₪. Realizes UJ-1.

**Consequences (testable):**
- A start month before the history floor is rejected, and the message shows next to the control with the floor date.
- Months after the latest month with complete NAV data cannot be selected.
- A deposit that is zero, negative or not a number does not start the run, and the error shows next to the control.

#### FR-2: Simulate the suggested allocation

The system shall invest each month's deposit across the funds in proportion to their suggested weights, at each fund's NAV, and value the holdings at each month's last NAV. Realizes UJ-1. [ASSUMPTION: deposits are invested at the first available NAV of the month and holdings are valued at the last available NAV of the month.]

**Consequences (testable):**
- With every fund's NAV flat, the final cumulative value equals the total deposits.
- Suggested weights are read once when the run starts and do not change across the range.

#### FR-3: Simulate the equal-weight baseline

The system shall run the same deposits split evenly across all 7 funds, using the same NAV data. Realizes UJ-1.

**Consequences (testable):**
- The baseline is always computed and shown with the suggested-allocation line. The user cannot turn it off.

#### FR-4: Handle missing NAV data

If a fund has no NAV for a month in the range (for example, a gap in its series), the system shall exclude that fund's weight for that month, redistribute it proportionally across funds that do have NAV, and mark that month on the chart. It shall not treat missing NAV as zero, and it shall not stop the run. Realizes UJ-1. [ASSUMPTION: if no fund has NAV for a month, that month's deposit is held as cash at zero growth and the month is marked.]

**Consequences (testable):**
- A marked month is visible on the chart and identifies the funds that were missing.
- A fund with NAV gaps does not lower the value of the funds that have data.

#### FR-5: Show the comparison

The system shall draw both cumulative-value lines on one chart with distinct styles, and show each line's final value and total deposited. Realizes UJ-1.

**Consequences (testable):**
- Both lines share the same x-axis months and the same deposit schedule.
- The final value of each line is labeled.

**Feature-specific NFRs:**
- The run reads only stored NAV history and the current `data/funds.json`. It makes no network request.
- Every new UI string is added in both Hebrew and English, per `src/lib/i18n.js`.

### 4.2 NAV history

**Description:** The backtest needs a stored daily NAV series per fund. Today, the pipeline discards the series after computing trailing metrics. This feature makes the pipeline keep it, so the page can read it. Without it, nothing in 4.1 can run.

#### FR-6: Persist NAV history

The daily pipeline shall keep each fund's daily NAV series in `data/` alongside the trailing metrics in `data/funds.json`. Each run adds new days and keeps earlier days.

**Consequences (testable):**
- After one run, each fund's stored series contains every day returned by the source for that fund.
- A later run does not drop days from an earlier run.

#### FR-7: Backfill existing history through the pipeline

The existing history is loaded by a pipeline run (scheduled or manually dispatched), not by the browser. `index.html` makes no bizportal request.

**Consequences (testable):**
- The backfill runs in `.github/workflows/update-data.yml` or the Python script, never in `src/` or `index.html`.
- `data/funds.json` is regenerated by the pipeline and is not hand-edited.

## 5. Non-Goals (Explicit)

- Testing whether the scoring algorithm would have recommended a different split at each past month.
- Backtesting any allocation other than "suggested weights" against "equal weight."
- Accounts, saved runs, or sharing.
- Forecasting returns, or giving investment advice.
- Modelling fees, taxes or fund management charges. [ASSUMPTION: the simulation is gross of fees and taxes, so it overstates the returns of both lines.]

## 6. MVP Scope

### 6.1 In Scope

- FR-1 to FR-5: the backtest run and its comparison chart.
- FR-6 and FR-7: stored NAV history and its one-time backfill.

### 6.2 Out of Scope for MVP

- Point-in-time recomputed weights. Deferred to a v3 candidate, once the stored history exists (see the addendum).
- Fee and tax modelling. Deferred; the result is labeled gross of both. [NOTE FOR PM] Add fees first if the comparison looks close, since a small fee gap could decide it.

## 7. Success Metrics

**Primary**
- **SM-1**: Hananya can read the chart and say whether the suggested split beat the equal split over the chosen range, with no extra steps. Validates FR-2, FR-3, FR-5.

**Counter-metrics (do not optimize)**
- **SM-C1**: The weights are not tuned to make the backtest look better. Fixing them is what keeps the test honest. Counterbalances SM-1.

## 8. Open Questions

1. How far back can the history floor go? It depends on how far back the source returns NAV data for each fund, or only the recent window its chart endpoint returns.
2. How large is the stored history, and is that acceptable for a static site on GitHub Pages?

## 9. Assumptions Index

- §4.1 FR-2: deposits are invested at the month's first available NAV and valued at its last available NAV.
- §4.1 FR-4: a month with no NAV for any fund holds the deposit as cash at zero growth and is marked.
- §5: the simulation is gross of fees and taxes.
