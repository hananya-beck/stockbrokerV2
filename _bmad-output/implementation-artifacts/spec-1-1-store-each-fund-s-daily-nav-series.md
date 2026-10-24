---
title: 'Store each fund''s daily NAV series'
type: 'feature'
created: '2026-10-25'
status: 'done'
baseline_commit: '59fb8486f7dba6e37689e0c98365cb968031deb8'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The daily pipeline fetches each fund's full daily NAV series, computes the metrics, and then discards the series. The Epic 2 backtest needs that series, so nothing can be checked against history yet.

**Approach:** Have `fetch_data.py` write each fund's series to `data/nav-history.json`, keyed by fund id, as ISO-dated `[date, close]` points sorted ascending. Drop any close that is not a finite number above zero. Convert the source's day-first dates to ISO, including `metrics.last_date` in `funds.json`. Nothing else changes: the page is untouched and the metrics stay the same.

## Boundaries & Constraints

**Always:** `scripts/fetch_data.py` is the only code that writes under `data/`. Standard library only. Closes are finite numbers above zero. Every date written is ISO `YYYY-MM-DD`. The history file is serialized with `allow_nan=False`. Tests run offline, with the fetch stubbed.

**Never:** Merging with a previous history file (Story 1.2). Keeping stale data for a failed fetch, the all-fail abort, or atomic writes (Stories 1.3 and 1.4). Until Story 1.3, a fund whose fetch fails is simply absent from the history file. Changing `index.html`. Hand-editing `data/funds.json`. Adding a dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Happy path | One fund's series with day-first dates, in any order | `nav-history.json` holds that fund's points as ISO dates, ascending | N/A |
| Bad close | A point whose close is `0`, negative, `NaN` or `null` | That point is dropped; the other points are kept | Dropped without failing the run |
| Non-finite value | A value that would serialize as `NaN` or `Infinity` | Never written, because it is dropped before serialization | `allow_nan=False` makes any miss fail loudly |
| Fund fetch fails | An exception for one fund | That fund is absent from `nav-history.json` this run; the run continues | Existing per-fund catch; stale marking arrives in Story 1.3 |
| Size | Seven funds at their current history length | File under 5 MB | Test fails when over |

## Decisions

- **Verifying "works in the running app":** option A. Run `python scripts/fetch_data.py` locally, confirm `data/nav-history.json` parses as strict JSON, then serve the site with `python -m http.server` and confirm the page still loads and shows the same funds and figures. The page gets no new UI in this story.

</frozen-after-approval>

## Code Map

- `scripts/fetch_data.py` -- `fetch_fund_series` (about lines 64–94) builds the series from bizportal points, with day-first dates and `close` as a float. The series is sorted with `datetime.strptime` on `%d/%m/%Y`.
- `scripts/fetch_data.py` -- `compute_metrics` sets `metrics["last_date"]` from the last point (about line 182), still in day-first form.
- `scripts/fetch_data.py` -- `main` (about line 219) builds `funds` and writes `OUTPUT` (`funds.json`). The history file is written here, next to `OUTPUT`. The path constants are at the top of the file.
- `tests/test_fetch_data.py` -- the `make_series` helper uses placeholder dates such as `day0`. Do not reuse it for the date tests. Follow the file's plain-function style.

## Tasks & Acceptance

**Execution:**
- [x] `scripts/fetch_data.py` -- add a function that turns a fund's series into ISO points, dropping invalid closes and sorting ascending -- keeps the rules in one tested place
- [x] `scripts/fetch_data.py` -- make `last_date` ISO -- AD-2: every date under `data/` is ISO
- [x] `scripts/fetch_data.py` -- write `data/nav-history.json` from `main` with `allow_nan=False` -- the history file (AD-2)
- [x] `tests/test_fetch_data.py` -- tests for date conversion, bad-close drop, ordering, `last_date`, strict serialization, and the 5 MB bound -- the I/O matrix

**Acceptance Criteria:**
- Given a successful run, when the producer finishes, then `data/nav-history.json` exists, its keys are the fund ids fetched, and each fund's points are sorted ascending by ISO date.
- Given a close of `0`, a negative value, `NaN` or `null`, when points are built, then that point is absent and no other point changes.
- Given a run, when `funds.json` is written, then `metrics.last_date` is `YYYY-MM-DD`.
- Given seven funds at their current history length, when the history is serialized, then the file is under 5 MB.
- Given the test suite, when it runs, then no test opens a network connection.

## Implementation Notes

- `scripts/fetch_data.py`: `fetch_fund_series` now returns ISO dates, so `last_date` is ISO without a separate change. `nav_points` drops closes that are not finite and above zero. `nav_history_payload` builds the file, and `main` writes it next to `funds.json` with `allow_nan=False`. Failed funds are omitted, as the spec's Never list says.
- `tests/test_fetch_data.py`: 18 tests pass offline. The five I/O matrix rows each have a covering test that ran and passed: happy path, bad close, non-finite serialization, fund fetch failure (via `main` with a stubbed fetch), and size.
- Manual check (option A): `python scripts/fetch_data.py` ran against bizportal. It wrote 7 funds, and `nav-history.json` parsed with 200 to 1,230 points per fund and was 437 KB. Served with `python -m http.server`, `index.html`, `funds.json` and `nav-history.json` returned 200. A browser render was not checked. The generated `funds.json` and `nav-history.json` were restored or removed, not committed.

## Spec Change Log

## Review Triage Log

Reviewers: blind hunter (B), edge-case hunter (E), verification-gap (V). Each finding has one row. Routes: **patch** (fixed here), **defer** (recorded in `deferred-work.md`), **reject** (verdict false, low, or excluded by the frozen intent).

| ID | Finding | Verdict | Route | Evidence |
|----|---------|---------|-------|----------|
| B1 / E1 | All fetches failing keeps stale fallbacks, so `series_by_id` is empty and the history is overwritten with `funds: {}` | high | patch | Guard added: history is written only when a fund succeeded. Test `test_all_fetches_failing_keeps_last_good_history` fails without the guard and passes with it. |
| B2 / E2 | A failed fund with prior data is absent from history and not marked stale | medium | reject | Excluded by the frozen Never list; carry-over and stale marking are Story 1.3. |
| B3 / E3 | `stale` is hard-coded `False`, so no fund can report stale | medium | reject | Same as B2; the stale flag is written by Story 1.3. |
| B4 / V3 | The workflow stages only `funds.json`, so `nav-history.json` is never committed | high | defer | Staging is Story 1.4. Until then the history file never reaches the repo; recorded in `deferred-work.md`. |
| B5 | The 5 MB test uses synthetic data and `indent=2` inflates the size | low | reject | The test is the spec's acceptance criterion. The real file is 437 KB, measured in Implementation Notes. Changing the format is out of scope. |
| B6 | No duplicate-date check and no ordering assertion | low | reject | The source returns unique dates; Story 1.2 merges by date. |
| B7 | The payload has no schema version | low | reject | AD-2 defines the shape; versioning is not part of the contract. |
| B8 | Test not hermetic: `main` might make a risk-free-rate fetch | false | reject | `main` calls the network only through `fetch_fund_series`, which the test replaces; config and outputs go to `tmp_path`. |
| B9 | ISO sort depends on an invariant that is not stated | low | patch | One comment added above the sort in `fetch_fund_series`. |
| B7b / E5 / O2 | `funds.json` is written before the history file, with plain `write_text`, so a crash between them leaves the pair out of step | medium | defer | Atomic writes and ordering are Story 1.4. `allow_nan=False` cannot raise on the history payload, since `nav_points` drops non-finite values. |
| E4 | A fund whose closes are all dropped gets `points: []` and looks fresh | low | reject | Unlikely in practice; the fix would break AD-2's rule that keys equal the `funds.json` ids. |
| E6 | One malformed row fails the whole fund | low | reject | The existing behavior fails the fund safely; the fix adds branches for an unlikely input. |
| E7 | Duplicate fund ids in `funds_config.json` overwrite each other in history | medium | defer | Predates this change: the duplicate already appears in `funds.json`. Recorded in `deferred-work.md`. |
| V1 | The `main` test checks only the fund keys, so dropping every point still passes | high | patch | Points assertion added to `test_failed_fund_is_absent_from_history_and_run_continues`. |
| V2 | `funds.json` keeps the day-first `last_date` for a failing fund until the next run | medium | defer | The stale path is rewritten in Story 1.3. Recorded in `deferred-work.md`. |
| O1 | The metrics path does not filter non-numeric closes, so `NaN` could reach `funds.json` | maybe-false | defer | Predates this change. Not verified against live bizportal data. What would settle it: a bizportal response containing a non-numeric `C_p`. Recorded in `deferred-work.md`. |

## Verification

**Commands:**
- `python -m pytest tests -q` -- expected: all pass
- `npm run check` -- expected: typecheck, lint and JS tests pass; these paths are unchanged, so they must stay green

**Manual checks (decided: option A):**
- Run `python scripts/fetch_data.py` locally. `data/nav-history.json` exists and parses as strict JSON.
- Serve the site with `python -m http.server`. The page still loads and shows the same funds and figures.

### Review Findings

- [x] [Review][Patch] Main-level tests do not check the bytes `main` writes: the 5 MB bound and strict-JSON check run on a re-implementation, and no test checks that `funds.json` `last_date` is ISO [tests/test_fetch_data.py:328] — applied: `test_main_writes_strict_history_under_5_mb_and_iso_last_date`
- [x] [Review][Defer] When every fetch fails and a previous `funds.json` exists, the stale fallback keeps `funds` non-empty, so `funds.json` is rewritten with all-stale entries [scripts/fetch_data.py:270] — deferred: pre-existing; the all-fail abort is Story 1.3 by the Never list.
- [x] [Review][Defer] The stale path keeps a day-first `last_date` [scripts/fetch_data.py:270] — deferred: already recorded as V2; Story 1.3.
- [x] [Review][Defer] The workflow stages only `funds.json` [.github/workflows/update-data.yml:29] — deferred: already recorded as B4/V3; Story 1.4.
- [x] [Review][Defer] `funds.json` is written before `nav-history.json` [scripts/fetch_data.py:286] — deferred: already recorded as B7b; Story 1.4.
- [x] [Review][Defer] Duplicate fund ids overwrite each other in history [data/funds_config.json] — deferred: already recorded as E7; predates this change.
- [x] [Review][Defer] The metrics path does not filter non-numeric closes, so `NaN` could reach `funds.json` [scripts/fetch_data.py:91] — deferred: already recorded as O1, maybe-false; settle with a bizportal response containing a non-numeric `C_p`.
- [x] [Review][Defer] A malformed point (non-numeric `C_p` such as an empty string, or a missing or unparseable `D_p`) fails the whole fund [scripts/fetch_data.py:90] — deferred: maybe-false; settle with the same bizportal check as O1.
- [x] [Review][Defer] `AGENTS.md` and `.claude/rules/fetch-script.md` do not mention `data/nav-history.json` [AGENTS.md] — deferred: documentation edits to agent-context files.

**Rejected:**
- `false`: `nav_points` can receive a `None` close. Upstream, `fetch_fund_series` drops `None` at `scripts/fetch_data.py:94`.
- `false`: the all-fail history-guard comment is wrong. The guard runs only when no fund succeeded, which is the all-fail case.
- `false`: `nav_points` does not sort or convert dates, as the Execution task text says. The acceptance criterion holds end to end, so this is a cosmetic wording mismatch.
- `false`: `generated_at` is a full timestamp, not a date. It is an AD-2 field, and the `YYYY-MM-DD` rule covers date fields.
- `reject`: `"stale": false` is always false. The field is part of the AD-2 shape (`ARCHITECTURE-SPINE.md:42`) and is set only once Story 1.3 lands.
- `reject`: failed-fund history is lost on overwrite. The frozen Never list excludes it until Story 1.3, the same as B2.
- `reject`: duplicate source dates would double-count. Same as B6; the source returns unique dates.
- `reject`: a fund whose closes are all dropped gets `points: []`. Same as E4.
- `reject`: the manual browser render was not checked. This is a process gap, not a code defect: `index.html` is untouched and does not read `last_date`. It stays open for the author to run.
- `reject`: the Code Map describes day-first dates. Fixing it would edit the spec under review.
- `reject`: the committed `data/funds.json` has day-first `last_date` values. The next scheduled run regenerates it, and the only fix is a hand-edit that `AGENTS.md` forbids.
- `reject`: triage IDs `B7` and `B7b` are easy to conflate. Cosmetic.

**Status sync:** the spec frontmatter says `done` and `sprint-status.yaml` says `review`. Step 6 of the review sets both to the new status.
