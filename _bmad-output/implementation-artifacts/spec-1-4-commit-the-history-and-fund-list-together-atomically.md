---
title: 'Commit the history and fund list together, atomically'
type: 'feature'
created: '2026-10-25'
status: 'done'
baseline_revision: '549cf063b96ae8929502c5c05654c3b9a5d0c2f9'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** `main` writes `funds.json` with a plain `write_text`, then serialises and writes `nav-history.json`. A crash or a serialisation error between the two leaves the pair out of step, and an interrupted write can leave a half-written file. The daily workflow and the add-fund skill stage only `data/funds.json`, so `data/nav-history.json` never reaches the repo.

**Approach:** `main` serialises both payloads before any write, writes each to a temp file beside its target, then moves them into place with `os.replace`, history first and fund list last. The workflow and the skill stage both files together; the workflow rebases before pushing and fails when the push fails. A test reads both files and asserts the staging.

## Boundaries & Constraints

**Always:** Standard library only. Temp files live in `data/` (the target's own directory) so the move is a same-filesystem rename, and none survives a failed write. `nav-history.json` moves first and `funds.json` last. The all-fail run still writes nothing. Tests run offline.

**Never:** Changing the file shapes or what is written. Changing `index.html`. Hand-editing `data/funds.json`. Committing run output under `data/`. Editing `AGENTS.md` or `.claude/rules/` (deferred documentation item). Duplicate-id and non-numeric `C_p` items from `deferred-work.md`. Epic 2.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Normal run | At least one fund fetched | Both files replaced; history moved before fund list; no `.tmp` left in `data/` | N/A |
| Serialisation fails | History payload holds a non-finite value | Neither file written or changed; no temp file left | Raises (loud) |
| Temp write fails | Writing a temp file raises | No target replaced; temps removed | Raises |
| Crash after history move | `os.replace` of the fund list raises | History is new, fund list is the old file, no temp left | Raises |
| All funds fail | Every fetch raises | Nothing written | Exit 1 (unchanged) |
| Workflow push fails | `git push` returns non-zero | The job step fails | Step exits non-zero |

</intent-contract>

## Code Map

- `scripts/fetch_data.py` -- `main` (line 340): lines 395-406 write `OUTPUT` then `NAV_HISTORY` with `write_text`; the history payload is built only after `funds.json` is written. `NAV_HISTORY` and `OUTPUT` (lines 20-21) are the targets; tests monkeypatch both to `tmp_path`, so the temp path must derive from the target (`path.with_name`), not from a fixed `data/`.
- `.github/workflows/update-data.yml` -- "Commit updated data" step stages only `data/funds.json`, then pushes with no pull.
- `.claude/skills/add-fund/SKILL.md` -- step 7 commits `data/funds.json` with the config and README; step 6 runs `scripts/fetch_data.py`.
- `tests/test_fetch_data.py` -- existing `main` tests (line 196, 269) show the monkeypatch pattern (`FUNDS_CONFIG`, `OUTPUT`, `NAV_HISTORY`, `build_opener`, `fetch_fund_series`).
- `_bmad-output/implementation-artifacts/deferred-work.md` -- the staging, write-order and serialise-before-write items are this story's.

## Tasks & Acceptance

**Execution:**
- `scripts/fetch_data.py` -- add `write_files_atomically(files)` taking ordered `(path, text)` pairs: write every temp file first, then `os.replace` in order, and remove any leftover temp in a `finally` -- AD-4
- `scripts/fetch_data.py` -- `main`: build both JSON strings (history keeps `allow_nan=False`) before any write, then call `write_files_atomically` with history first and fund list last; print the two "Wrote" lines after -- AD-4, deferred write-order and serialise-first items
- `.github/workflows/update-data.yml` -- stage `data/funds.json data/nav-history.json`, run `git pull --rebase` before `git push`, nothing swallows a push failure -- AD-3, FR7
- `.claude/skills/add-fund/SKILL.md` -- step 7 stages and commits `data/nav-history.json` alongside `data/funds.json` -- AD-3
- `tests/test_fetch_data.py` -- tests for the matrix rows (order via a recorded `os.replace`, serialisation failure leaves both files untouched, mid-move failure leaves no temp, no temp after a normal run) and one offline test that reads the workflow and the skill and asserts staging, `git pull --rebase` before `git push`, and no `|| true` on the push -- AD-3

**Acceptance Criteria:**
- Given a normal run, when `main` finishes, then `os.replace` moved `nav-history.json` before `funds.json` and no temp file remains beside them.
- Given the history payload cannot be serialised, when `main` runs, then neither file is written or changed.
- Given the workflow and the skill, when the test reads them, then every line naming `data/funds.json` also names `data/nav-history.json`, and the workflow pulls with rebase before pushing.
- Given the test suite, when it runs, then no test opens a network connection.

## Spec Change Log

## Review Triage Log

## Design Notes

Two temp files, then two renames, is not a single transaction: a crash between the renames leaves the new history beside the old fund list. That order is chosen on purpose (AD-4): the history is a superset that the page does not read yet, so a new history with an old fund list is the harmless half-state, while the reverse would show a fund list that the history cannot back. The workflow commits both files in one commit, so the repo never holds the half-state.

## Verification

**Commands:**
- `python -m pytest tests -q` -- expected: all pass
- `npm run check` -- expected: typecheck, lint and JS tests pass; these paths are unchanged

## Auto Run Result

Status: done
Blocking condition: none. The first unattended session was blocked on the write to `.claude/skills/add-fund/SKILL.md`. The human approved the edit, and the staging line was changed in this session.

Done: `scripts/fetch_data.py` (`write_files_atomically`, serialise-before-write, history first), `.github/workflows/update-data.yml` (stage both, `git pull --rebase` before push), `.claude/skills/add-fund/SKILL.md` step 7 (stages `data/nav-history.json` too), seven new tests in `tests/test_fetch_data.py`. `python -m pytest tests -q`: 72 pass. `npm run check`: 42 pass.
