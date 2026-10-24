---
title: Backtest simulator
status: final
created: 2026-10-24
updated: 2026-10-25
---

# PRD: Backtest simulator

## 0. Document Purpose

This PRD defines what the backtest simulator must do and where its scope stops. It builds on `brief-stockbrokerV2-2026-10-22/brief.md` and its `addendum.md`, which are not repeated here. The reader is Hananya, the sole user and maintainer, and whoever builds it in this repo. Requirements describe capabilities; implementation choices belong to the architecture notes.

## 1. Vision

The dashboard suggests a monthly ₪ allocation across the TASE funds in `data/funds.json`, using a risk-adjusted score that nobody has validated. The backtest simulator tests that suggestion against history. It applies today's suggested weights to a past period and compares the result with an equal-weight baseline on the same deposits. One chart answers the question that matters: did today's suggested allocation beat an equal split over that period, and so is the score worth trusting?

## 2. Target User

### 2.1 Jobs To Be Done

- Decide whether the suggested allocation is worth trusting with real money, rather than trusting it on faith or ignoring it.
- Get that answer in one sitting, once or occasionally. No ongoing reporting.

### 2.2 Non-Users (v1)

Anyone other than the maintainer. There are no accounts, saved runs or sharing.

### 2.3 Key User Journeys

- **UJ-1. Hananya checks the score before trusting it.** Hananya opens the dashboard, picks a start month two years back and a ₪1,000 monthly deposit, clicks "Run backtest," and reads the chart. The suggested-allocation line finishes above or below the equal-weight baseline line, and any months with incomplete fund data are marked.

## 3. Glossary

- **Backtest range** — the months from the chosen start month through the last complete calendar month that has NAV data for every fund.
- **History floor** — the earliest month from which every fund has NAV data. The earliest selectable start month. Individual funds can still have gaps after the floor (see FR-4).
- **Monthly deposit** — the ₪ amount invested at the start of each month in the backtest range.
- **Suggested weight** — a fund's share in the dashboard's current suggestion, read from `data/funds.json` and held fixed for the whole run.
- **Suggested allocation** — the portfolio built by applying the suggested weights to every monthly deposit.
- **Equal-weight baseline** — the same monthly deposits split evenly across every fund in `data/funds.json`.
- **NAV history** — the stored daily NAV series for each fund, written by the daily pipeline.
- **Cumulative value** — total deposited so far, grown by each fund's NAV change and valued at the month's last available NAV.

## 4. Features

### 4.1 Backtest run

**Description:** The user chooses a start month and a monthly deposit, then runs the backtest. For each month in the range, the simulator invests that month's deposit through the suggested allocation, and invests the same deposit through the equal-weight baseline. Both cumulative values are drawn on one line chart. Realizes UJ-1.

**Functional Requirements:**

#### FR-1: Choose backtest inputs

The user can choose a start month no earlier than the history floor and a positive monthly deposit in ₪. Realizes UJ-1.

**Consequences (testable):**
- A start month before the history floor is rejected, and the message shows next to the control with the floor date.
- Months after the last complete calendar month cannot be selected.
- A deposit that is zero, negative or not a number does not start the run, and the error shows next to the control.
- When the history floor is less than 12 months before the last complete month, the run is disabled and the page says so next to the control. [ASSUMPTION: 12 months is the shortest backtest worth reading.]

#### FR-2: Simulate the suggested allocation

The system shall invest each month's deposit across the funds in proportion to their suggested weights, at each fund's NAV, and value the holdings at each month's last available NAV. Realizes UJ-1. [ASSUMPTION: deposits are invested at the first available NAV of the month.]

**Consequences (testable):**
- With every fund's NAV flat, the final cumulative value equals the total deposited.
- Fixture: one ₪100 deposit, weights 50/50, fund A's NAV rises from 100 to 110 and fund B's stays at 100. The final cumulative value is ₪105.
- Suggested weights are read once when the run starts and do not change across the range.

#### FR-3: Simulate the equal-weight baseline

The system shall run the same deposits split evenly across every fund in `data/funds.json`, using the same NAV data and the same gap rule as FR-4. Realizes UJ-1.

**Consequences (testable):**
- The baseline is always computed and shown with the suggested-allocation line. The user cannot turn it off.
- A fund with no NAV for a month has its 1/7 share redistributed across the funds that do have NAV, as FR-4 does for suggested weights.

#### FR-4: Handle missing NAV data

If a fund has no NAV for a month in the range (for example, a gap in its series), the system shall exclude that fund's weight for that month and redistribute it proportionally across funds that do have NAV. The fund's existing units are valued at its last known NAV, carried forward. The month is marked on the chart. The system shall not treat missing NAV as zero, and it shall not stop the run. Realizes UJ-1. [ASSUMPTION: if no fund has NAV for a month, that month's deposit is held as cash at zero growth and the month is marked.]

**Consequences (testable):**
- Fixture: weights 50/50, fund B has no NAV in month 1 only. The whole ₪100 deposit of month 1 goes to fund A.
- A marked month is a shaded band on the chart, with a tooltip that names the funds that were missing.

#### FR-5: Show the comparison

The system shall draw both cumulative-value lines on one chart. The suggested allocation is a solid line and the equal-weight baseline is a dashed line. The system shall show each line's final value and total deposited. Realizes UJ-1.

**Consequences (testable):**
- Both lines share the same x-axis months and the same deposit schedule.
- The final value of each line is labeled.
- The chart and the final values state that results are gross of fees and taxes.

**Feature-specific NFRs:**
- The run reads only stored NAV history and the current `data/funds.json`. It makes no network request.
- Every new UI string is added in both Hebrew and English, per `src/lib/i18n.js`.
- Working targets: stored NAV history totals under 5 MB, and a full backtest run finishes in under 2 seconds on the maintainer's machine. [ASSUMPTION: these bounds are working targets to measure after the first backfill.]

### 4.2 NAV history

**Description:** The backtest needs a stored daily NAV series per fund. Today, the pipeline discards the series after computing trailing metrics. This feature makes the pipeline keep it, so the page can read it. FR-6 and FR-7 carry no journey of their own; they enable UJ-1, and nothing in 4.1 can run without them.

#### FR-6: Persist NAV history

The daily pipeline shall keep each fund's daily NAV series in `data/` alongside the trailing metrics in `data/funds.json`. Each run adds new days and keeps earlier days.

**Consequences (testable):**
- After one run, each fund's stored series contains every day returned by the source for that fund.
- A later run does not drop days from an earlier run.

#### FR-7: Backfill existing history through the pipeline

A manual dispatch of the pipeline runs the one-time backfill of existing history. Scheduled daily runs then append new days. The backfill runs in the pipeline, not in the browser, and `index.html` makes no bizportal request.

**Consequences (testable):**
- The backfill is triggered by a `workflow_dispatch` input in `.github/workflows/update-data.yml`, and runs in the pipeline, never in `src/` or `index.html`.
- After the backfill, the stored history records the earliest date reached for each fund, and the page shows that floor.
- If the backfill fails or returns less history than the source has, the data status next to the refresh control shows the failure.
- `data/funds.json` is regenerated by the pipeline and is not hand-edited.

## 5. Non-Goals (Explicit)

- Testing whether the scoring algorithm would have recommended a different split at each past month (see §6.2).
- Backtesting any allocation other than the suggested allocation against the equal-weight baseline.
- Validating the score out of sample. The weights come from trailing scores ending today, which overlap the backtested months, so the result is in-sample and tends to flatter the suggested allocation.
- Accounts, saved runs, or sharing.
- Forecasting returns, or giving investment advice.
- Modelling fees, taxes or fund management charges. [ASSUMPTION: the simulation is gross of fees and taxes, so it overstates the returns of both lines.]

## 6. MVP Scope

### 6.1 In Scope

- FR-1 to FR-5: the backtest run and its comparison chart.
- FR-6 and FR-7: stored NAV history and its one-time backfill.

### 6.2 Out of Scope for MVP

- Point-in-time recomputed weights. Deferred to a v3 candidate, once the stored history exists (see the addendum). Until then the MVP can only test today's split against history; it cannot show whether the scoring method added value over time.
- Fee and tax modelling. Deferred; the result is labeled gross of both. [NOTE FOR PM] Add fees first if the comparison looks close, since a small fee gap could decide it.

## 7. Success Metrics

**Primary**
- **SM-1**: Hananya can read the chart and say whether the suggested allocation beat the equal-weight baseline over the chosen range, with no extra steps. Validates FR-5.
- **SM-2**: For a fixed NAV fixture, the final values of both lines match hand-computed values. Validates FR-2, FR-3, FR-4.

**Counter-metrics (do not optimize)**
- **SM-C1**: The allocation formula is not changed in the same change set as backtest results. Counterbalances SM-1.

## 8. Open Questions

1. How far back does the source return daily NAV for each fund? This sets the history floor and whether the two-year example in UJ-1 is possible.
2. Does the backfilled history fit the 5 MB working target? Measure after the first backfill.

## 9. Assumptions Index

- §4.1 FR-1: a backtest needs at least 12 months of history to be shown.
- §4.1 FR-2: deposits are invested at the month's first available NAV, and holdings are valued at its last available NAV.
- §4.1 FR-4: a fund's units are valued at its last known NAV, carried forward across its gaps.
- §4.1 FR-4: a month with no NAV for any fund holds the deposit as cash at zero growth and is marked.
- §4.1 NFRs: the 5 MB and 2-second bounds are working targets.
- §5: the simulation is gross of fees and taxes.
