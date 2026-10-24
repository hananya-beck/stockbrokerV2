---
status: final
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-stockbrokerV2-2026-10-24/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-stockbrokerV2-2026-10-25/ARCHITECTURE-SPINE.md
---

# Backtest simulator - Epic Breakdown

## Overview

This document provides the epic and story breakdown for the backtest simulator in stockbrokerV2. It decomposes the requirements from the PRD and the architecture spine (AD-1 to AD-8) into two epics and nine stories. The project has no UX design contract and no starter template, so there are no UX requirements and no set-up story.

## Requirements Inventory

### Functional Requirements

FR1: The user can choose a start month no earlier than the history floor and a positive monthly deposit in ₪.
FR2: The system invests each month's deposit across the funds in proportion to their suggested weights, at each fund's NAV, and values the holdings at each month's last available NAV.
FR3: The system runs the same deposits split evenly across every fund in `data/funds.json` as the equal-weight baseline, with the same gap rule as FR4.
FR4: When a fund has no NAV for a month in the range, the system excludes its weight for that month, redistributes it across funds that have NAV, carries its units at the last known NAV, and marks the month. It never treats missing NAV as zero and never stops the run.
FR5: The system draws both cumulative-value lines on one chart, the suggested allocation solid and the baseline dashed, and shows each line's final value and total deposited.
FR6: The daily pipeline keeps each fund's daily NAV series in `data/`, adding new days and keeping earlier ones.
FR7: The first pipeline run after FR6 stores the full history the source returns. The page never calls bizportal, and a failed fetch shows stale data next to the refresh control.

### NonFunctional Requirements

NFR1: A backtest run makes no network request. It reads only `data/funds.json` and `data/nav-history.json`.
NFR2: Every new UI string is added in both Hebrew and English in `src/lib/i18n.js`.
NFR3: Stored NAV history totals under 5 MB, and a full backtest run finishes in under 2 seconds on the maintainer's machine. These are working targets.
NFR4: No browser storage (`localStorage`, `sessionStorage`, IndexedDB, cookies).
NFR5: No build step and no new runtime dependencies. Paths are relative. `data/funds.json` is never hand-edited.

### Additional Requirements

- AD-1: `index.html` may import `src/lib/`. `src/lib/` imports nothing outside itself, never fetches, touches the DOM, or reads the clock. `index.html` never imports `scripts/`.
- AD-2: `data/nav-history.json` has one shape: keys equal the `funds.json` ids, points `[YYYY-MM-DD, close]` ascending, gaps as absent points, `close` finite and above 0, every date under `data/` ISO, `stale` owned only by the producer, successful runs merge by date with the source value winning.
- AD-3: `scripts/fetch_data.py` is the only writer of generated files under `data/`. Any commit that changes `funds.json` also changes `nav-history.json`. The workflow runs `git pull --rebase` before push, and a failed push fails the run.
- AD-4: Zero successful fetches write nothing and exit 1. A failed fund keeps its previous points with `stale: true`, or is written with `points: []` if it has none. An unparseable previous history exits 1. Writes go through temp files and `os.replace`, `nav-history.json` first.
- AD-5: `src/lib/backtest.js` exports `simulateBacktest` and is the only place portfolio values are computed. It prices deposits at the month's first NAV and values holdings at the last. Gap rules are in this function. Cash from a month with no NAV for any fund is never invested.
- AD-6: Cumulative values are ₪ numbers and weights are fractions. Only `src/lib/formatting.js` formats text, and unknown values render as `'—'`. A page that cannot parse the history disables the run and never renders partial data.
- AD-7: The page makes two same-origin reads, `funds.json` and `nav-history.json`, with `cache: 'no-store'`, and stores nothing in browser storage.
- AD-8: `backtestBounds(navHistory, fundIds, nowMonth)` in `src/lib/backtest.js` returns the floor and range end. `index.html` passes `nowMonth` from the browser clock and computes neither bound.

### UX Design Requirements

None. No UX design contract exists for this feature.

### FR Coverage Map

FR1: Epic 2 - Stories 2.3 and 2.4 (inputs, bounds, the 6-month minimum)
FR2: Epic 2 - Story 2.1 (suggested allocation)
FR3: Epic 2 - Story 2.1 (equal-weight baseline)
FR4: Epic 2 - Story 2.2 (missing NAV months)
FR5: Epic 2 - Story 2.5 (comparison chart)
FR6: Epic 1 - Stories 1.1 and 1.2 (store and merge the history)
FR7: Epic 1 - Stories 1.3 and 1.4 (first run, failure safety, commit path)

## Epic List

### Epic 1: Keep a full NAV history

After this epic, the daily pipeline keeps every fund's daily NAV series in one file, merged across runs. A failed run never empties or silently drops a fund. The page is unchanged, so the epic is complete on its own.

**FRs covered:** FR6, FR7

### Epic 2: Backtest the suggested allocation

After this epic, Hananya chooses a start month and a monthly deposit, runs the backtest, and reads one chart comparing the suggested allocation with an equal-weight baseline, with gap months marked. The epic reads the history from Epic 1 at runtime but does not need Epic 1's stories to be changed to work.

**FRs covered:** FR1, FR2, FR3, FR4, FR5

## Epic 1: Keep a full NAV history

After this epic, the daily pipeline keeps every fund's full daily NAV series in `data/nav-history.json`, merged across runs, and a failed fetch never empties the history.

### Story 1.1: Store each fund's daily NAV series

As Hananya,
I want every successful run to save each fund's full NAV series to one history file,
So that the backtest has history to read.

**Acceptance Criteria:**

**Given** a successful run with at least one fund fetched
**When** the producer finishes
**Then** `data/nav-history.json` exists, its keys equal the ids in `data/funds.json`, and each fund's points are sorted ascending by ISO date (AD-2, FR6)
**And** a source point whose close is `0`, negative, `NaN` or `null` is dropped, and the run continues (AD-2)
**And** the file is written with `json.dumps(..., allow_nan=False)` and parses with a strict JSON parser (AD-2)
**And** `metrics.last_date` in `funds.json` is ISO `YYYY-MM-DD`, and no date under `data/` is `dd/mm/yyyy` (AD-2)
**And** the file for the seven current funds is under 5 MB (NFR3)
**And** `tests/test_fetch_data.py` covers each of these with fixture series and no network (NFR5)

### Story 1.2: Merge each run into the stored history

As Hananya,
I want each run to add to the stored history rather than replace it,
So that days the source stops returning are never lost.

**Acceptance Criteria:**

**Given** stored points for a fund and a run whose source window omits older dates
**When** the producer merges
**Then** every older date is kept (FR6, AD-2)
**And** when a date is in both with different closes, this run's source value wins (AD-2)
**And** after two runs on different days, the second file contains every date from the first (FR6)
**And** on the first run, when there is no previous `nav-history.json`, the merge starts from the fetched series alone, which is the only run allowed to have no previous history (FR7, AD-4)

### Story 1.3: Keep the last good data when a fetch fails

As Hananya,
I want a failed fetch to keep the fund's last good data and say so,
So that one outage never empties the history or hides a missing fund.

**Acceptance Criteria:**

**Given** a fund whose fetch fails and that has previous points
**When** the run writes both files
**Then** its points are kept and `"stale": true` is set in both files (AD-4, FR7)
**And** a fund whose fetch fails and has no previous data is written with `points: []` and `stale: true`, stays in the fund list, and prints a warning (AD-4)
**And** when every fund fails, nothing is written to either file and the run exits 1, including when previous data exists (AD-4)
**And** when `nav-history.json` exists but does not parse, the run exits 1 before any write (AD-4)

### Story 1.4: Commit the history and fund list together, atomically

As Hananya,
I want the history and the fund list written and committed as a pair,
So that the page never reads one file from a new run and the other from an old run.

**Acceptance Criteria:**

**Given** the producer writes its outputs
**When** it finishes
**Then** each file goes to a temp file in `data/` and is moved into place with `os.replace`, `nav-history.json` first and `funds.json` last (AD-4)
**And** `.github/workflows/update-data.yml` stages both `data/funds.json` and `data/nav-history.json`, runs `git pull --rebase` before `git push`, and fails the run when the push fails (AD-3, FR7)
**And** `.claude/skills/add-fund/SKILL.md` runs `scripts/fetch_data.py` and stages both files, never `funds.json` alone (AD-3)
**And** a commit that changes `funds.json` also changes `nav-history.json`, checked by reading the workflow and the skill (AD-3)

## Epic 2: Backtest the suggested allocation

After this epic, Hananya runs a backtest from the dashboard and reads one chart with gap months marked. The calculation lives in a pure, tested module, and the page only reads files and draws.

### Story 2.1: Simulate the suggested allocation and the equal-weight baseline

As Hananya,
I want one tested function that values the suggested allocation and the equal-weight baseline for each month,
So that both lines come from the same calculation.

**Acceptance Criteria:**

**Given** one ₪100 deposit, weights 50/50, fund A's NAV rising from 100 to 110, and fund B's flat at 100
**When** `simulateBacktest` runs
**Then** the final cumulative value of the suggested allocation is ₪105 (FR2, SM-2)
**And** with every fund's NAV flat, both lines' final values equal the total deposited (FR2, FR3)
**And** the suggested weights are read once and used unchanged for every month (FR2, AD-5)
**And** each fund gets `1/n` of every baseline deposit, where `n` is the number of funds passed in (FR3)
**And** the function reads no clock and is deterministic for the same input (AD-1, AD-5)
**And** `tests/js/backtest.test.js` covers each export, empty input, and a zero or negative NAV that is excluded (AD-2)

### Story 2.2: Handle months with missing NAV

As Hananya,
I want a month with missing NAV handled by one stated rule,
So that a data gap never shows as a loss and never stops a run.

**Acceptance Criteria:**

**Given** fund B has no NAV in month 1 only, with weights 50/50
**When** `simulateBacktest` runs
**Then** all of month 1's ₪100 goes to fund A, and month 1 is listed as a gap month (FR4, AD-5)
**And** fund B's units carry their last known NAV forward in later months (FR4, AD-5)
**And** when no fund has NAV for a month, that deposit is held as cash at zero growth through the range end, never invested, and the month is listed as a gap month (FR4, AD-5)
**And** the baseline's missing share is redistributed by the same rule, so both lines are comparable (FR3)
**And** no output value is `NaN` and no input causes a throw (AD-6)

### Story 2.3: Set the range bounds and validate the inputs

As Hananya,
I want the earliest and latest selectable months computed from the data, with the inputs checked,
So that I can only run a backtest the data can support.

**Acceptance Criteria:**

**Given** NAV points for every fund
**When** `backtestBounds(navHistory, fundIds, nowMonth)` runs
**Then** the floor is the latest of each fund's first month (FR1, AD-8)
**And** the range ends at the last complete calendar month before `nowMonth` in which every fund has at least one point (AD-8)
**And** when a stale fund ends early, the result names that fund as the limit (AD-8, FR7)
**And** when the floor is less than 6 months before the last complete month, the result reports the run as not runnable, with the reason (FR1)
**And** a deposit that is zero, negative or not a number returns an error and no run (FR1)
**And** the tests pass `nowMonth` explicitly, since the library never reads the clock (AD-1, AD-8)

### Story 2.4: Pick inputs and see the bounds on the dashboard

As Hananya,
I want to choose a start month and a deposit on the dashboard, with the bounds and any limit shown next to the control,
So that I only run backtests the data supports, and I see why when I can't.

**Acceptance Criteria:**

**Given** the page loads
**When** it reads data for the backtest
**Then** it reads only `data/funds.json` and `data/nav-history.json`, both relative and with `cache: 'no-store'`, and makes no other request (AD-7, NFR1)
**And** the start-month picker's earliest choice is the floor from `backtestBounds`, and `index.html` computes neither bound itself (AD-8)
**And** when the run is not runnable, the run control is disabled and the reason shows next to it in the selected language (FR1, NFR2)
**And** when `nav-history.json` fails to load or parse, the error shows next to the run control, the run is disabled, and no partial data is rendered (AD-6)
**And** the page writes nothing to `localStorage`, `sessionStorage`, IndexedDB or cookies (AD-7, NFR4)
**And** every new string exists in both `STRINGS.he` and `STRINGS.en` (NFR2)

### Story 2.5: Show the comparison chart

As Hananya,
I want one chart with both cumulative lines and the gap months marked,
So that I can read the answer in one look.

**Acceptance Criteria:**

**Given** a finished run
**When** the chart renders
**Then** both lines share one month axis, the suggested allocation is solid, and the baseline is dashed (FR5)
**And** each gap month is a shaded band whose tooltip names the missing funds (FR4, FR5)
**And** each line's final value and total deposited are labeled, and the chart states that results are gross of fees and taxes (FR5)
**And** every value is formatted through `src/lib/formatting.js`, and an unknown value shows `'—'` (AD-6)
**And** the chart is inline SVG in `index.html` with no charting library (AD-1, NFR5)
**And** a full run on the stored history finishes in under 2 seconds on the maintainer's machine, measured once and noted in the story (NFR3)

## Step 4 Validation

- FR coverage: FR1 to FR7 each appear in at least one story (see the coverage map).
- Starter template: none, so no set-up story is needed.
- Forward dependencies: none. Stories 1.1 to 1.4 build on earlier stories only, and so do 2.1 to 2.5.
- Epic independence: Epic 1 stands alone. Epic 2 uses Epic 1's file at runtime and needs no Epic 1 story to change.
- File churn: Epic 1 changes the producer and the workflow. Epic 2 changes `src/lib/`, `index.html` and tests. Only `formatting.js` and `i18n.js` are shared, and each epic adds to them without changing the other's work.
- Architecture: AD-1 to AD-8 are each cited in at least one story.
