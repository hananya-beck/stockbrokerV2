---
paths:
  - ".github/workflows/**"
  - "tests/test_fetch_data.py"
---

# Workflows that commit generated files

Added 2026-10-25. Reason: `_bmad-output/implementation-artifacts/epic-1-retro-2026-10-25.md` findings F4 (no concurrency group, so an overlapping run's rebase conflicts) and F13 (the Story 1.4 workflow test matched text, so a swallowed push failure would have passed).

- A workflow that commits `data/` declares a top-level `concurrency` group with `cancel-in-progress: false`.
- The commit step never swallows a failure: no `continue-on-error`, no `set +e`, and no `||` on `git push`.
- The fetch step runs before the step that stages `data/` files.
- Workflow tests check these properties on the workflow's structure, not on the presence of a phrase somewhere in the file.

**Bad**

```yaml
on:
  schedule: [...]
jobs:
  update:
    steps:
      - run: git add data/funds.json
      - run: git push || true
```

**Good**

```yaml
on:
  schedule: [...]
concurrency:
  group: update-data
  cancel-in-progress: false
jobs:
  update:
    steps:
      - run: python scripts/fetch_data.py
      - run: git add data/funds.json data/nav-history.json && git push
```

Enforced by `tests/test_fetch_data.py::test_workflow_serialises_runs_and_fetches_before_it_commits` and `test_commit_step_never_swallows_a_failure`.
