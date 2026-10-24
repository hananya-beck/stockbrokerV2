---
title: 'Merge each run into the stored history'
type: 'feature'
created: '2026-10-25'
status: 'done'
baseline_revision: '7700c5d8a2bb7e8e6ecb0ce9701e8d15e1bc34e1'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred:
  - summary: >-
      The workflow stages only data/funds.json, so data/nav-history.json never reaches the repo and the merge has no stored file to read in CI.
    evidence: |-
      Blind and verification-gap reviews. Story 1.4 owns staging; already recorded in deferred-work.md from Story 1.1. Until 1.4 lands the history does not accumulate across scheduled runs.
    location: >-
      .github/workflows/update-data.yml:29
    severity: medium
  - summary: >-
      nav-history.json is written with plain write_text, so a crash mid-write leaves a truncated file that the strict read now rejects on every later run.
    evidence: |-
      Edge-case review. Atomic writes are Story 1.4; already recorded in deferred-work.md. The strict read (exit 1 on an unparseable file) makes the non-atomic write more consequential than before.
    location: >-
      scripts/fetch_data.py:345
    severity: medium
---

<intent-contract>

## Intent

**Problem:** Each run overwrites `data/nav-history.json` with only the window the source returns today. Any date the source stops returning is lost, so the history Epic 2 needs cannot grow past the source window.

**Approach:** Before fetching, `fetch_data.py` reads the previous `nav-history.json`. For each fetched fund it merges the fetched points into the stored points by date: no stored date is removed, and on a shared date this run's close wins. The first run, with no previous file, starts from the fetched series alone.

## Boundaries & Constraints

**Always:** `scripts/fetch_data.py` is the only code that writes under `data/`. Standard library only. Merged points are sorted ascending by ISO date with one point per date, and closes stay finite and above zero. Merging runs only for funds fetched this run. A stored file that exists but cannot be read or has the wrong shape ends the run with exit 1 before any write, never an empty fallback. Tests run offline, with the fetch stubbed.

**Never:** Stale marking, the all-fail abort, and atomic writes (Stories 1.3 and 1.4). Workflow or add-fund staging (1.4). Changing `index.html` or hand-editing `data/funds.json`. Adding a dependency. Editing `AGENTS.md` or `.claude/rules/` (deferred documentation item). Deciding what duplicate ids in `funds_config.json` should do (deferred, no decision in the epic context).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Older dates kept | Stored points for dates 1-5, fetched window covers dates 4-6 | File holds dates 1-6 ascending | N/A |
| Revised close | A date in both with different closes | This run's close is stored | N/A |
| Two runs | Run 2 on a later day than run 1 | Every date from run 1 is in run 2's file | N/A |
| First run | No `nav-history.json` | File holds the fetched series alone | N/A |
| Unreadable previous file | File exists but is invalid JSON or lacks `funds` | Nothing written; exit 1 | `sys.exit` with a message naming the file |
| Fund fails this run | Fund is in the config and in the stored file, fetch raises | Its stored entry is carried over unchanged, so no stored date is dropped | Stale flag stays as stored; marking it is Story 1.3 |
| Fund left the config | Stored fund id is not in `funds_config.json` | Not carried into the new file | N/A |

</intent-contract>

## Code Map

- `scripts/fetch_data.py` -- `nav_points` (about line 101) filters closes to valid `[date, close]` points; reuse for the fetched side. `nav_history_payload` (about line 109) builds the file and hard-codes `stale: False`; it gains the merge. `main` (about line 242) reads the previous `funds.json` at the top and writes history at the end behind `if series_by_id:`; the previous-history read goes right after the config load, before the fetch loop.
- `tests/test_fetch_data.py` -- follow its plain-function style and its `main` tests that monkeypatch `FUNDS_CONFIG`, `OUTPUT`, `NAV_HISTORY`, `build_opener` and `fetch_fund_series` to `tmp_path`. Existing payload and size tests call `nav_history_payload(series_by_id, generated_at)`; keep that call valid.
- `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md` -- done predecessor; its Never list assigned merging here and stale handling to 1.3.

## Tasks & Acceptance

**Execution:**
- `scripts/fetch_data.py` -- add `merge_points(previous, fetched)` that unions by date with fetched winning and returns sorted `[date, close]` points -- the merge rule in one tested place (AD-2)
- `scripts/fetch_data.py` -- add `read_previous_history(path)` returning `{fund_id: points}`; absent file gives `{}`, unreadable or wrong shape raises `SystemExit` -- the previous-history read (AD-4)
- `scripts/fetch_data.py` -- give `nav_history_payload` an optional `previous` argument: merge fetched funds, carry over previous entries not fetched this run; `main` passes the previous points limited to configured ids -- no stored date dropped
- `tests/test_fetch_data.py` -- tests for each I/O matrix row, including a two-run `main` test -- the matrix

**Acceptance Criteria:**
- Given stored points and a run whose window omits older dates, when the producer writes, then every older date is in the file.
- Given a date in both with different closes, when merged, then the file holds this run's close.
- Given two runs on different days, when the second finishes, then its file contains every date from the first.
- Given no previous `nav-history.json`, when the producer runs, then the file holds the fetched series alone and the run succeeds.
- Given the test suite, when it runs, then no test opens a network connection.

## Spec Change Log

## Review Triage Log

### 2026-10-25 — Review pass
- verdicts: 26 findings — high 0, medium 3, low 20, false 3, maybe-false 0
- findings:
  - `[medium]` `[defer]` Blind 1: merge never runs in production because the workflow does not stage `nav-history.json` — Story 1.4 owns staging; recorded in `deferred` and already in `deferred-work.md`.
  - `[low]` `[reject]` Blind 2: a corrupt entry for a removed fund blocks the daily refresh — AD-4 requires an unparseable or mis-shaped file to exit 1; scoping validation to configured ids is extra branching for a hand-corruption case.
  - `[low]` `[reject]` Blind 3: removing a fund from the config deletes its stored history — AD-4 makes the fund list the only fund set; the removal is deliberate and the matrix row states it.
  - `[low]` `[patch]` Blind 4: `_is_point` accepts any string as a date — added `_is_iso_date` (strict `fromisoformat` round trip) and use it in `_is_point`.
  - `[low]` `[patch]` Blind 5: validation tests leave most rules unpinned — parametrized the unreadable-history test with one case per rule.
  - `[low]` `[reject]` Blind 6: spec and code disagree on the return shape of `read_previous_history` — the fix is to edit the spec, which triage does not do; the docstring and tests describe the shipped shape.
  - `[low]` `[reject]` Blind 7: history size unbounded, merged size untested — seven funds measured 437 KB in Story 1.1 against a 5 MB bound; growth is about 250 points a year per fund.
  - `[low]` `[reject]` Blind 8: no log of added or revised points — cosmetic, and adds code for no consumer.
  - `[low]` `[reject]` Blind 9: a fetched fund with no new dates is marked fresh — the stale flag is Story 1.3.
  - `[low]` `[reject]` Blind 10: assorted missing tests (idempotence, empty inputs, missing `generated_at`) — the behaviours are covered by the two-run and carry-over tests; the rest are unlikely to regress.
  - `[low]` `[reject]` Edge 1: `math.isfinite` raises `OverflowError` for a huge stored integer — fails loudly with exit 1 before any write; reachable only by hand-editing.
  - `[low]` `[reject]` Edge 2: `RecursionError` on deeply nested JSON escapes the handler — same: loud failure before any write, hand-editing only.
  - `[low]` `[patch]` Edge 3: non-ISO stored date sorts out of order — same root cause as Blind 4; fixed by `_is_iso_date`.
  - `[low]` `[reject]` Edge 4: carried entries are written verbatim, so unsorted or duplicate points persist — the producer always writes them sorted and unique; only hand-editing breaks that.
  - `[low]` `[reject]` Edge 5: a non-string config id would not match stored string keys — `funds_config.json` ids are strings and the fetch URL and `funds.json` already assume it.
  - `[low]` `[reject]` Edge 6: concurrent runs can overwrite each other's merge — speculative; the workflow rebase and push path is Story 1.4.
  - `[medium]` `[defer]` Edge 7: a truncated non-atomic write makes the strict read fail every later run — atomic writes are Story 1.4; recorded in `deferred` and already in `deferred-work.md`.
  - `[false]` `[reject]` Edge 8: an unreadable history halts the `funds.json` refresh — AD-4 requires exit 1 before any write; that is the specified behaviour.
  - `[low]` `[reject]` Edge 9: the return shape differs from the spec task — same as Blind 6.
  - `[false]` `[reject]` Edge 10: a removed fund survives when every fetch fails — nothing is written in that case, which leaves the stored file untouched as AD-4 requires.
  - `[low]` `[patch]` Verification 1: `_is_point` and `_is_history_entry` rules are not isolated by tests — parametrized cases added for a 3-element point, non-string and non-ISO dates, boolean, zero, negative and infinite closes, non-boolean `stale`, non-list `points` and a non-object entry.
  - `[low]` `[patch]` Verification 2: non-ISO stored dates pass validation — same root cause as Blind 4; fixed by `_is_iso_date`.
  - `[medium]` `[defer]` Verification 3: the workflow does not stage `nav-history.json` — same as Blind 1.
  - `[low]` `[reject]` Intent 1: the first-run criterion has no standalone `main`-level test — the first call of the two-run test runs `main` with no file, and a payload test covers the no-previous case.
  - `[low]` `[patch]` Intent 2: the spec does not state the deferred-work scan result or that the unreadable-file exit was pulled forward from Story 1.3 — both added to Design Notes.
  - `[false]` `[reject]` Intent 3: the history read at the top of `main` can exit before fetching — AD-4 says the producer reads the previous history before fetching.

## Design Notes

Previous entries for configured funds that failed to fetch are carried over verbatim. Dropping them would delete stored days on a successful run, which AD-2 forbids. Only the stale flag is left for Story 1.3. The history file is not committed until Story 1.4, so the interim `stale: false` on a carried entry has no reader.

Deferred-work scan: the only item about keying the history is duplicate fund ids in `funds_config.json`. The epic context gives no rule for it, so it stays deferred. The other items belong to Stories 1.3 and 1.4 or are documentation edits. The exit-1 on an unreadable previous file is Story 1.3's last criterion, pulled forward because merging cannot start from an empty fallback without dropping stored days. Story 1.3 owns its contract and error text.

`read_previous_history` returns `{fund_id: {"stale", "points"}}`, not points alone, so a carried entry keeps its stored flag.

## Verification

**Commands:**
- `python -m pytest tests -q` -- expected: all pass
- `npm run check` -- expected: typecheck, lint and JS tests pass; these paths are unchanged

**Manual checks (if no CLI):**
- Run `python scripts/fetch_data.py` twice. `data/nav-history.json` keeps its point count or grows on the second run. Then `git restore data/` and delete any untracked generated file; nothing under `data/` is committed.

## Auto Run Result

Status: done

**Summary:** `scripts/fetch_data.py` now reads the previous `data/nav-history.json` before fetching and merges each fetched fund's points into the stored points by date. No stored date is removed, and this run's close wins on a shared date. With no previous file, the first run starts from the fetched series alone. Stored entries for configured funds that failed to fetch are carried over unchanged. Funds that left the config are dropped. A previous file that exists but cannot be read or has the wrong shape ends the run with exit 1 before any write.

**Files changed:**
- `scripts/fetch_data.py` -- `merge_points`, `read_previous_history`, `_is_iso_date`, `_is_point`, `_is_history_entry`; `nav_history_payload` takes `previous`; `main` reads the history before the fetch loop.
- `tests/test_fetch_data.py` -- tests for each matrix row, a two-run `main` test, parametrized unreadable-history cases; the all-fail test's sentinel file is now a valid history file.
- `_bmad-output/implementation-artifacts/spec-1-2-merge-each-run-into-the-stored-history.md` -- this spec.

**Review findings:** 26 findings: 0 high, 3 medium, 20 low, 3 false. Patches applied: 5 rows over 2 root causes (strict ISO dates in stored points, plus parametrized validation tests) and 1 spec note, all low. Deferred: 3 rows over 2 items (workflow staging and non-atomic write, both Story 1.4). Rejected: the remaining 17 rows, each with its reason in the Review Triage Log.

**Follow-up review recommended:** false. No high finding and no medium finding was patched.

**Verification:**
- `python -m pytest tests -q` -- 45 passed, offline.
- `npm run check` -- typecheck, lint and 42 JS tests pass.
- Manual: `python scripts/fetch_data.py` run twice against bizportal. The first run wrote 7 funds with 200 to 1,230 points each; the second run left the same counts and merged without error. Generated files were restored or deleted, and nothing under `data/` is committed. A browser render was not checked, as `index.html` is untouched.
- Matrix audit: every row has a covering test that ran and passed.

**Residual risks:** The history does not accumulate in CI until Story 1.4 stages `nav-history.json`. A carried-over failed fund keeps its stored `stale` flag, so `funds.json` and `nav-history.json` can disagree on it until Story 1.3. Duplicate ids in `funds_config.json` stay deferred.
