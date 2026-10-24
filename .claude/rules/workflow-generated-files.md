---
paths:
  - ".github/workflows/**"
  - "tests/test_fetch_data.py"
---

# Workflows that commit generated files

- A workflow that commits `data/` must declare a top-level `concurrency` group with `cancel-in-progress: false`. Without it, an overlapping run rebases onto the same generated files and fails.
- The commit step never swallows a failure: no `continue-on-error`, no `set +e`, and no `||` on `git push`.
- The fetch step runs before the step that stages `data/` files.
- Workflow tests parse the YAML and assert these properties. They do not match text.
