# Exercise 11: Three mistakes that happen only once

Every fix also saves the lesson where the agent reads it automatically. Three rules, each with a date, its source, and a Bad and Good example. One is enforced by tests, and a fresh session followed one of them without being told.

## The rules

| Rule | Date | Source | Enforced by |
|---|---|---|---|
| `.claude/rules/fetch-script-series.md` (paths `scripts/**`): one cleaned series per fund, strict JSON output | 2026-10-25 | `epic-1-retro-2026-10-25.md` findings F1, F2; fixed in `025b302` | `test_main_drops_bad_closes_before_metrics_and_writes_strict_funds_json` |
| `.claude/rules/workflow-generated-files.md` (paths `.github/workflows/**`, `tests/test_fetch_data.py`): concurrency group, no swallowed failures, structural workflow tests | 2026-10-25 | retro findings F4 and F13 | `test_workflow_serialises_runs_and_fetches_before_it_commits`, `test_commit_step_never_swallows_a_failure` |
| `.claude/rules/orchestrator-briefs.md` (paths `prompts/**`): a brief grants every file a story names | 2026-10-25 | exercise 10 run log, Story 1.4 (session `f247599d-0588-4552-afba-b905159d3faf`) | None. Checked at launch time. |

Each file has a Bad example and a Good example. For the workflow rule, the Good example shows a concurrency group, a fetch step before the commit, and no swallowed push.

The workflow rule also needed the fix it describes: the concurrency group was missing (retro action item 3), so it was added in the same commit. Without it, the new test fails (checked by stashing the workflow change: `1 failed`).

## Enforcement

- `python -m pytest tests -q` (76 tests) fails if either enforced rule is broken. The series test fails on the pre-fix code with the `TypeError` from the retro, and the workflow test fails without the concurrency group.
- The project's Python check is `python -m pytest tests -q`, since `npm run check` covers only the front end.

## Fresh-session check

A fresh headless session (`claude -p`, Sonnet, in a clean clone of `exercise-11-rules`) was given this task, which does not mention cleaning or the rule:

> In scripts/fetch_data.py, add a latest_close field to each fund's entry in funds.json: the close on the fund's most recent point. Add a test in tests/test_fetch_data.py that runs main with a fund whose series ends in a NaN close and checks latest_close. Run python -m pytest tests -q until it passes. Do not commit.

Evidence from the session transcript (`abe58e9c-285a-4851-ae11-1ed57ff20d82`):

- The series rule was loaded automatically. The transcript holds the rule's text under a system reminder that starts "Contents of … fetch-script-series.md". The session never read the rules file itself.
- The session used the cleaned series (`series[-1]["close"]` after `clean_series`). Its summary says: "A trailing NaN is dropped first … Using the raw last point would have made `json.dumps(..., allow_nan=False)` fail on the write."
- Its test, `test_main_latest_close_skips_a_trailing_nan_close`, passes. 76 tests pass in the clone.

Caveat: `main` already cleans each series, so this task would have passed a little less of the rule than it looks. The session still chose the cleaned series and gave the reason the rule gives. A harder check would ask for a new reader of the raw response.

## What I did not do

- The `sprint-status.yaml` hand edit from Story 1.4 is not a rule here. The script can't set story status, so no sanctioned path exists yet for it. It's a gap for a later exercise.
