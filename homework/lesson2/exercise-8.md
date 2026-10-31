# Exercise 8 — Phase 4: sprint planning and the readiness gate

> Slide 42. Took the final PRD, architecture spine and epics (`exercise-6.md` and
> `exercise-7.md`) through the readiness gate, then generated the sprint status file with
> `bmad-sprint-planning`.

## Card

- **Goal:** have a skeptic check the plan before any code, and get a heartbeat file you can diff.
- **Challenge:** run sprint planning, read the readiness verdict, deal with what it raises
  in the planning docs rather than waving it through, and get the stories tracked.
- **Done when:** the verdict is recorded with what was done about each concern;
  `sprint-status.yaml` is committed with the epic and every story; the statuses a story
  moves through can be named in order.

## Readiness verdict

- **First gate run: CONCERNS.** Two gaps would have made a developer invent answers:
  - PRD FR-7 requires the page to show a failed fund's history as stale next to the
    refresh control, and no story covered it. Fixed: Story 2.4 now has that criterion, and
    the page reads the stale flag from the file rather than deriving it from dates.
  - Story 1.4's AD-3 criterion was "checked by reading the workflow", which is not
    testable. Fixed: it is now a test in `tests/test_fetch_data.py`.
- **Non-blocking concerns, also fixed in the planning docs:**
  - No layout spec for the new controls and chart. Fixed: Story 2.4 now requires the
    controls above the chart, the page's right-to-left layout in Hebrew, and no horizontal
    scrolling at a 360px width.
  - The 5 MB and 2-second targets are unmeasured. Covered by criteria already in the plan:
    Story 1.1 tests the size, and Story 2.5 measures the run time once.
- **Re-gated after the fixes: PASS.** The gate's judgment was made by me, not by an
  independent reviewer, so the PASS is my reading of the fixed docs.
- The card's hint says a FAIL would send the gap back to its owner (John for a requirement,
  Winston for a decision). Nothing reached FAIL, so no phase was re-run.

## Sprint status

- `_bmad-output/implementation-artifacts/sprint-status.yaml` is committed. It lists 2
  epics, 9 stories and 2 optional retrospectives, all `backlog`, and it validates with no
  problems.
- The script shortens two story keys (`…-basel`, `…-nav-series`). The keys are
  deterministic, so I kept them as generated.

## Story statuses, in order

The file's status definitions give the order a story moves through:

1. `backlog`: the story exists only in the epic file.
2. `ready-for-dev`: the story file is created and ready for development.
3. `in-progress`: a developer is implementing it.
4. `review`: implementation is complete and ready for review.
5. `done`: the story is complete.

An epic moves `backlog` → `in-progress` → `done`. The first story that starts moves its
epic to `in-progress` automatically.

## Done-when, checked

- The verdict is recorded (CONCERNS, then PASS), with what was done about each concern.
- `sprint-status.yaml` is committed with both epics and all nine stories.
- The story statuses are named in order above.

## Still open

- The gate was my own judgment. An independent reviewer would be the next check if this
  plan were going to a real team.
- Nothing is in progress yet. Story 1.1 is next.
