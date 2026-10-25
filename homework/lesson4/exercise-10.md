# Exercise 10: An orchestrator finishes the epic

## The brief
`prompts/exercise-10-orchestrator.md` (commit `7700c5d`). It tells an orchestrator session to build Stories 1.2, 1.3 and 1.4 of Epic 1 in fresh sessions, one at a time, with a gate after each story. It also runs the epic retro, turns the action items into rules, and checks the app before stopping. The orchestrator writes no code, never merges and never pushes.

## What ran
- **Orchestrator:** one headless `claude -p` session on Sonnet, launched in the background. Run log: `exercise-10-run-log.md` in the session scratchpad.
- **Story 1.2** (session `6f8d40d7-7ca2-45ca-bc3e-9e206bcec70b`, commit `8b91fa3`): all gates passed. `npm run check` 42 JS tests, pytest 45. Marked done. No resumes.
- **Story 1.3** (session `5ae421c8-bf14-4883-a7c5-ad86a8621d90`, commit `549cf06`): all gates passed. pytest 65. Marked done. No resumes.
- **Story 1.4** (session `f247599d-0588-4552-afba-b905159d3faf`): **blocked**. The story needs one line changed in `.claude/skills/add-fund/SKILL.md`, and the write was denied under `acceptEdits`. The session did not route around the denial, and the orchestrator stopped on its stop condition.

## Where it stopped, and what I finished by hand
The orchestrator stopped at Story 1.4 and did not run the retro, the rules or the app check. I then:
- Made the one-line skill edit (step 7 stages `data/nav-history.json` too). It was approved in the session.
- Finished Story 1.4 (commit `fb396f5`). `npm run check` and pytest passed (72 tests). Marked done.
- Ran the epic retro (`bmad-retrospective -H 1`) in the session, not through the orchestrator.

The orchestrator's stop was right: a story session hit a file it had no permission to write, and the brief did not list that file. The fix for next time is in the retro's process lesson P3.

## Retro verdict: rejected
The retro is `_bmad-output/implementation-artifacts/epic-1-retro-2026-10-25.md` (commit `0203432`). All four stories are done, and their acceptance criteria pass. The verdict is rejected on the declared criteria for one reason: the bad-close rule (Story 1.1's I/O matrix, and the epic's "finite and above zero" rule) breaks on the metrics path. I reproduced two failures:
- A negative latest close aborts the daily run with a `TypeError`.
- A NaN close writes `funds.json` with a bare `NaN` token that `index.html` cannot parse.

Seven action items were recorded in `sprint-status.yaml`. The three that describe standing behaviour became rules: `.claude/rules/fetch-script-series.md`, `workflow-generated-files.md` and `nav-history-recovery.md` (commit `da249a4`). Once the first two action items land, the verdict should flip to accepted-with-open-items.

## App check
- `scripts/fetch_data.py` ran live in a scratch copy of the repo. All seven funds fetched. The history is strict JSON, sorted, with ISO dates. A second run gives the same history.
- The repo served locally: `index.html`, `data/funds.json` and `data/funds_config.json` return 200.
- `data/nav-history.json` is not in the repo yet. It appears with the first daily run, which the workflow then commits.
- Not done: the page in a browser. The Story 1.1 spec lists that as a manual check, and it is still open.
