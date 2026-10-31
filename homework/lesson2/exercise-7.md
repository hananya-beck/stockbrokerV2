# Exercise 7 — Phase 3: spine, then epics

> Slide 41. Took the final backtest PRD (`homework/lesson2/exercise-6.md`) to
> `bmad-architecture` for the architecture spine, then to `bmad-create-epics-and-stories`
> for the epics and stories.

## How this run was done

- The course page could not be read past the middle, so the exercise card's exact wording
  was not available. I read the index line "Spine, then epics" as: write the architecture
  spine (the Solutioning phase), then break the PRD into epics and stories.
- Run by the assistant under the instruction to make the calls, not as a coached session.
  Every decision is in the memlog for review.

## Architecture spine

- `_bmad-output/planning-artifacts/architecture/architecture-stockbrokerV2-2026-10-25/ARCHITECTURE-SPINE.md`
  — `status: final`. Paradigm: pipes and filters. Eight invariants (AD-1 to AD-8) cover
  the dependency direction, the NAV-history contract, the single writer, failure safety,
  the one simulation core, values and formatting, the two browser reads, and range bounds.
- The reviewer gate ran in three parts:
  - **Lint:** clean, 0 findings.
  - **Version check:** corrected the Stack table to the versions in `package-lock.json`
    (TypeScript 5.9.3, ESLint 9.39.5), and noted the registry's newer versions sit outside
    the declared ranges. The check also showed that pytest is unpinned.
  - **Adversarial review:** 12 holes. All are accepted into AD-2 to AD-8. They include a
    merge rule that the first draft left undefined, an all-fail path that the existing code
    gets wrong, a date format that `funds.json` breaks, and the add-fund skill committing
    `funds.json` without the history file.
- The spine lists six code follow-ups where the existing code does not yet meet the rules.
  They are not implemented in this exercise.

## Epics and stories

- `_bmad-output/planning-artifacts/epics/epics.md` — `status: final`. Two epics, nine
  stories, every FR covered.
  - **Epic 1, keep a full NAV history** (FR6, FR7), four stories: store, merge, failure
    safety, and the atomic commit path.
  - **Epic 2, backtest the suggested allocation** (FR1 to FR5), five stories: the core
    calculation, missing-NAV months, bounds and validation, the dashboard controls, and the
    chart.
- Two epics rather than one because the data contract (AD-2) is the feedback boundary.
  Epic 1 is complete on its own, and Epic 2 uses its data at runtime.
- No UX contract and no starter template exist, so there are no UX requirements and no
  set-up story.

## Done-when, checked

- The spine's invariants are decided or deferred, and each AD names what it binds and what
  divergence it prevents.
- Every FR appears in at least one story, and the acceptance criteria cite the AD they follow.
- No story depends on a later one, and each epic stands on its own.
- The exercise card's own Done-when text was not available, so these checks come from the
  architecture and epics workflows.

## Still open

- The six code follow-ups in the spine need their own change before the feature can work
  as specified. Two of them change behaviour that already exists: the all-fail path in
  `main()` and the add-fund skill's commit.
- The 5 MB and 2-second targets are still unmeasured. The size is an estimate from the point
  count.
