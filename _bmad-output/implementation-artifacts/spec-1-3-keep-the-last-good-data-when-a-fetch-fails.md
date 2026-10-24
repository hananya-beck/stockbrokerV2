---
title: 'Keep the last good data when a fetch fails'
type: 'feature'
created: '2026-10-25'
status: 'done'
baseline_revision: '8b91fa37b84975dce3f450a697be5bcb63d0d51b'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred:
  - summary: >-
      .claude/rules/fetch-script.md still describes only the previous-metrics fallback, not the all-null entry for a fund with no previous data or the stale flag in nav-history.json.
    evidence: |-
      Blind, verification-gap and intent reviews. The fix edits an agent-context file, which review routing defers. Joins the nav-history.json documentation item already in deferred-work.md.
    location: >-
      .claude/rules/fetch-script.md:11
    severity: low
  - summary: >-
      A malformed entry or an unparseable previous funds.json is swallowed by a bare except in main, so every failed fund falls back to all-null metrics without a message.
    evidence: |-
      Blind and intent reviews. Pre-existing read; it matters more now that a failed fund always gets an entry. The history file is unaffected and keeps its points. Reachable only by hand-editing or an old file shape.
    location: >-
      scripts/fetch_data.py:357
    severity: low
  - summary: >-
      funds.json is written before nav-history.json is serialised, so a serialisation failure leaves the pair out of step.
    evidence: |-
      Edge review. Atomic writes and serialising both payloads before any write are Story 1.4; the non-atomic write is already in deferred-work.md.
    location: >-
      scripts/fetch_data.py:391
    severity: medium
  - summary: >-
      The workflow stages only data/funds.json, so the stale entries written to nav-history.json are not committed.
    evidence: |-
      Verification-gap and intent reviews. Story 1.4 owns staging; already in deferred-work.md. The stale flag holds in both files on disk after the script, not in the repo after the scheduled run, until 1.4.
    location: >-
      .github/workflows/update-data.yml:29
    severity: medium
---

<intent-contract>

## Intent

**Problem:** A failed fetch is only half handled. `nav-history.json` carries a failed fund's stored entry with its old `stale` flag, and a failed fund with no stored data vanishes from both files. When every fund fails and a previous `funds.json` exists, the run still rewrites `funds.json` with all-stale entries and exits 0. A stale fund also keeps the day-first `last_date` of the old file.

**Approach:** `main` counts fresh fetches before any write and exits 1 with nothing written when there are none. Every configured fund that failed is written stale to both files: with its previous metrics and points when it has them, otherwise with empty metrics and `points: []`, plus a warning. A failed fund's carried `last_date` is converted to ISO.

## Boundaries & Constraints

**Always:** `scripts/fetch_data.py` is the only code that writes under `data/`. Standard library only. `stale` has one owner, the producer, and both files carry the same flag for the same id. Every configured fund appears in both files on every successful run. A fund with no previous data has `points: []`, `stale: true` and an entry in `funds.json` shaped like the others, with every metric `null`. Every date written under `data/` is ISO. Tests run offline, with the fetch stubbed.

**Never:** Atomic writes, write ordering, workflow or add-fund staging (Story 1.4). Changing `index.html` or hand-editing `data/funds.json`. Adding a dependency. Editing `AGENTS.md` or `.claude/rules/` (deferred documentation item). Deciding what duplicate ids in `funds_config.json` should do (deferred). Settling the non-numeric `C_p` items in `deferred-work.md` (needs a live bizportal response). Epic 2.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fails with previous data | Fund fetch raises; stored points and previous metrics exist | Stored points and previous metrics kept; `stale: true` in both files; `last_date` is ISO | Failure printed to stderr |
| Fails with no previous data | Fund fetch raises; no stored points, no previous metrics | In both files with `stale: true`; `points: []`; all metrics `null`; fund keeps the floor weight | Warning naming the fund on stderr |
| Fails, metrics only | Previous `funds.json` has the fund, history does not | Previous metrics kept stale; `points: []` | Warning names the missing points |
| Fails, points only | History has the fund, previous `funds.json` does not | Stored points kept stale; metrics all `null` | Warning names the missing metrics |
| Every fetch fails, previous files exist | All raise | Neither file touched, byte for byte | Exit 1 with a message |
| Every fetch fails, no previous files | All raise | Neither file created | Exit 1 with a message |
| Day-first previous date | Previous `funds.json` has `last_date` `22/10/2026` and the fund fails | `last_date` written as `2026-10-22` | N/A |
| Unparseable previous date | Previous `last_date` is neither ISO nor day-first | `last_date` written as `null` | N/A |
| Unparseable history | `nav-history.json` exists but does not parse | Exit 1 before any fetch or write | Already covered by Story 1.2; keep passing |
| Recovery | A stale fund succeeds on the next run | `stale: false` in both files, points merged | N/A |

</intent-contract>

## Code Map

- `scripts/fetch_data.py` -- `main` (line 293): the fetch loop's `except` appends a stale `funds.json` entry only when the id is in `previous`; `if not funds:` (line 330) is never true once a previous file exists, which is the all-fail defect; the history write sits behind `if series_by_id:` (line 347). `nav_history_payload` (line 155) hard-codes `stale: False` and carries unfetched previous entries verbatim; it gains `failed_ids`. `compute_metrics` (line 208) defines the metric keys the empty entry must mirror. `_is_iso_date` (line 114) is reusable for the date conversion.
- `tests/test_fetch_data.py` -- its `_run_main`, `_entry`, `_pts` and `_series` helpers cover the `main` tests. Three existing tests encode the old behaviour and change: `test_failed_fund_is_absent_from_history_and_run_continues` (line 176), `test_all_fetches_failing_keeps_last_good_history` (line 207, calls `main` without expecting an exit) and `test_failed_fund_keeps_stored_entry_and_removed_fund_is_dropped` (line 408, expects the stored `stale` flag verbatim).
- `index.html`, `src/lib/formatting.js` -- read-only evidence: the page already renders a `null` metric and a `null` score (young funds), and does not read `last_date`, `last_price` or `history_days`, so an all-`null` entry needs no page change.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- the all-fail item and the stale-path `last_date` item are this story's; the rest are out of scope.
- `_bmad-output/implementation-artifacts/spec-1-2-merge-each-run-into-the-stored-history.md` -- done predecessor; it carried failed funds unchanged and left the flag to this story.

## Tasks & Acceptance

**Execution:**
- `scripts/fetch_data.py` -- `main`: abort with `sys.exit(message)` when `series_by_id` is empty, before the sort, the weights and every write; this replaces the `if not funds` check -- AD-4 all-fail rule
- `scripts/fetch_data.py` -- `main`: in the `except`, always append a stale `funds.json` entry whose metrics are the ISO-normalised previous metrics or an all-`null` set, and print a warning when previous metrics or stored points are missing -- every configured fund stays listed
- `scripts/fetch_data.py` -- add `empty_metrics()` mirroring the `compute_metrics` keys, and `iso_last_date(value)` returning an ISO date, a converted day-first date, or `None` -- one tested place for each rule
- `scripts/fetch_data.py` -- `nav_history_payload(series_by_id, generated_at, previous=None, failed_ids=())`: write each failed id as `{"stale": True, "points": <previous points or []>}`; entries in neither set are not written -- AD-4, AD-2
- `tests/test_fetch_data.py` -- one test per matrix row, plus updates to the three old-behaviour tests; the all-fail tests assert exit code 1 and byte-identical files

**Acceptance Criteria:**
- Given a fund that fails and has previous points, when the run writes both files, then its points are kept and `stale` is true in both.
- Given a fund that fails and has no previous data, when the run writes, then it is in both files with `points: []` and `stale: true`, and a warning names it.
- Given every fund fails and previous files exist, when the run ends, then it exits 1 and neither file changed.
- Given `nav-history.json` exists but does not parse, when the run starts, then it exits 1 before any write.
- Given the test suite, when it runs, then no test opens a network connection.

## Spec Change Log

## Review Triage Log

### 2026-10-25 — Review pass
- verdicts: 23 findings — high 0, medium 4, low 16, false 3, maybe-false 0
- findings:
  - `[low]` `[reject]` Blind 1: a stale fund still competes for weight and a no-data fund takes the floor — the Design Notes choose this on purpose; before this story a stale fund already kept its score and ranking, and the floor matches how young funds are treated.
  - `[low]` `[defer]` Blind 2: the rules doc and the page do not describe the new behaviour — the page already renders null metrics (young funds) and never reads `last_date`; the doc edit touches an agent-context file; recorded in `deferred`.
  - `[false]` `[reject]` Blind 3: `last_date` is only converted on the failure path — `compute_metrics` already writes ISO from the fetched series, so only carried old values can be day-first, which is the deferred item this story fixes.
  - `[low]` `[reject]` Blind 4: `iso_last_date` accepts non-padded day-first dates — it still returns a correct ISO date; no wrong output.
  - `[low]` `[defer]` Blind 5: a malformed previous `funds.json` silently empties every fallback — pre-existing swallow in `main`; hand-editing only; recorded in `deferred`.
  - `[low]` `[reject]` Blind 6: weak or redundant tests — the claimed gaps (non-dict previous entry) are reachable only by hand-editing; a duplicated `_read_funds` call is harmless.
  - `[low]` `[reject]` Blind 7: `empty_metrics` can drift from `compute_metrics` — `test_empty_metrics_has_the_keys_compute_metrics_produces` fails on drift.
  - `[low]` `[reject]` Edge 1: an empty config exits with the "all failed" message — same message as before this story, and the run still exits 1 with nothing written.
  - `[low]` `[reject]` Edge 2: a non-numeric previous score crashes the sort — hand-editing only, and the run fails loudly before any write.
  - `[low]` `[reject]` Edge 3: carried metrics are not validated per field — hand-editing only; validating would add branches for no reachable case.
  - `[false]` `[reject]` Edge 4: the missing-metrics warning fires only on the first failure — a repeated failure still has no stored points, so the points warning keeps firing; only the metrics half goes quiet, which is correct because all-null metrics are then the previous metrics.
  - `[low]` `[reject]` Edge 5: duplicate ids give a stale and a fresh entry — duplicate ids in `funds_config.json` are already deferred in `deferred-work.md` with no epic decision.
  - `[medium]` `[defer]` Edge 6: `funds.json` is written before the history is serialised — atomic writes and write ordering are Story 1.4; recorded in `deferred`.
  - `[low]` `[reject]` Edge 7: with no scored fund the "floor" is 1/n, not `MIN_WEIGHT` — `allocate_weights` is unchanged and equal weights are its documented fallback; the fix would be to reword the spec.
  - `[low]` `[reject]` Edge 8: the same-flag invariant breaks for duplicate ids — same as Edge 5.
  - `[medium]` `[patch]` Verification 1: no test pins a failed fund's previous score, rank and weight — added `test_failed_fund_keeps_previous_score_rank_and_weight`.
  - `[medium]` `[defer]` Verification 2: the workflow stages only `funds.json` — Story 1.4; recorded in `deferred`.
  - `[low]` `[defer]` Verification 3: the rules doc still describes only the previous-metrics fallback — same as Blind 2.
  - `[low]` `[reject]` Intent 1: the tests do not assert the number 1 as the exit status — the abort is `sys.exit(str)`, which CPython maps to status 1, and the tests assert the string code; a subprocess test would hit the network.
  - `[low]` `[defer]` Intent 2: an unparseable previous `funds.json` degrades silently — same as Blind 5.
  - `[false]` `[reject]` Intent 3: `last_date` normalisation covers the stale path only — same as Blind 3; the epic assigns exactly that path to this story.
  - `[medium]` `[defer]` Intent 4: after the script the stale flag is on disk in both files but the workflow commits only one — same as Verification 2.
  - `[low]` `[reject]` Intent 5: the dashboard does not show the stale flag — Epic 1 leaves the page unchanged; the label is Story 2.4.

## Design Notes

"No previous data" is judged per file: previous metrics come from the old `funds.json`, stored points from the old history. A fund missing from only one of them keeps what it has and gets a warning for what it lacks. Deriving metrics from stored points was left out: it adds a second metrics source for a state a normal run cannot reach.

A failed fund gets the same score as before, so a stale fund keeps its place in the ranking; a fund with no data scores `null` and takes the `MIN_WEIGHT` floor, as young funds already do.

`main` still writes `funds.json` before `nav-history.json` with plain `write_text`. Atomic writes and ordering are Story 1.4.

## Verification

**Commands:**
- `python -m pytest tests -q` -- expected: all pass
- `npm run check` -- expected: typecheck, lint and JS tests pass; these paths are unchanged

**Manual checks (if no CLI):**
- Run `python scripts/fetch_data.py` once against bizportal and confirm both files are written with `stale: false`. Then `git restore data/` and delete any untracked generated file; nothing under `data/` is committed.

## Auto Run Result

Status: done

**Summary:** `scripts/fetch_data.py` now exits 1 with nothing written when no fund fetched fresh, including when a previous `funds.json` exists. Every configured fund that failed is written stale to both files. It keeps its previous metrics and points when it has them. Otherwise it gets all-null metrics, `points: []` and a stderr warning, and takes the floor weight. A failed fund's carried `last_date` is converted from day-first to ISO. An unparseable previous `nav-history.json` already exits 1 before any write (Story 1.2) and its tests still pass.

**Files changed:**
- `scripts/fetch_data.py` -- `iso_last_date`, `empty_metrics`, `stale_metrics`; `nav_history_payload` takes `failed_ids`; `main` aborts on zero fresh fetches and always lists failed funds.
- `tests/test_fetch_data.py` -- a test per matrix row, unit tests for the new helpers, and one test for a failed fund's score, rank and weight; three old-behaviour tests replaced.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- resolved items removed, new deferrals added.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- story marked done.
- `_bmad-output/implementation-artifacts/spec-1-3-keep-the-last-good-data-when-a-fetch-fails.md` -- this spec.

**Review findings:** 23 findings: 0 high, 4 medium, 16 low, 3 false. Patches applied: 1 (medium, the missing score, rank and weight test). Deferred: 4 items (the rules doc wording, the silent previous-`funds.json` read, serialising before writing, workflow staging). Rejected: 14 rows, each with its reason in the Review Triage Log.

**Follow-up review recommended:** false. One medium finding was patched and no high.

**Verification:**
- `python -m pytest tests -q` -- 65 passed, offline.
- `npm run check` -- typecheck, lint and 42 JS tests pass.
- Matrix audit: every row has a covering test that ran and passed; the unparseable-history row is covered by the parametrized Story 1.2 test.
- Manual live run against bizportal not performed; every test stubs the fetch.

**Residual risks:** The stale flag reaches the repo only after Story 1.4 stages `nav-history.json`. `funds.json` is still written before the history with plain `write_text`. The page does not show the stale flag until Story 2.4. A malformed previous `funds.json` silently falls back to null metrics.
