# Exercise 2: The red path

**Goal:** Catch the bug that compiles — and watch the agent correct itself from the message alone.

## The behavior, and why types/lint can't see it
`pickDispatchedRun` in `src/lib/refresh.js` picks the **earliest** `workflow_dispatch` run after the user clicked refresh (ties broken by creation time, not insertion order). That ordering rule is pure business logic — `tsc` only checks that `best`/`run` are the right shape, and `eslint`'s rules (`no-unused-vars`, `eqeqeq`, …) don't know what a comparison *means*. Only a behavior test can catch a flipped `<` → `>`.

It was already guarded: `tests/js/refresh.test.js` has `'pickDispatchedRun picks the earliest run after the click'`, asserting the id of the earliest of two out-of-order runs.

## The plant
```diff
- if (!best || created < new Date(best.created_at).getTime()) best = run;
+ if (!best || created > new Date(best.created_at).getTime()) best = run;
```
Still type-checks (same types both sides), still lints clean (no banned pattern) — picks the *latest* run instead of the earliest.

**Confirmed:** `npm run typecheck` → exit 0. `eslint --max-warnings=0` → exit 0. `npm run test` → exit 1, exactly one failure: `pickDispatchedRun picks the earliest run after the click`.

## The blind fix
With the plant in place, I gave a **fresh agent with no knowledge of the plant** an unrelated one-line task (add a JSDoc `@example` to `describeApiError`, a different function in the same file) with `npm run check` as its only bar — never told it anything was wrong.

It found and fixed it from the failure message alone:
- Ran `npm run check`, got `actual: 2, expected: 1` on the earliest-run test.
- Recognized its own JSDoc edit couldn't have caused a numeric-ordering failure, so it isolated the cause: `git stash` (clean HEAD passes 47/47) vs. the dirty tree (fails) — confirming the bug predated its change.
- Reverted the comparison in `pickDispatchedRun` back to `created <`, matching the test's documented contract and `dispatchedRunsQuery`'s doc comment ("earliest ... after the click").
- Reported back before committing, as instructed.

## Final state
`git diff` on `src/lib/refresh.js` shows only the intended `@example` JSDoc line — the plant is gone. `npm run check` exits 0, 47/47 tests pass.

## Done when ✅
- [x] With the plant in, types and lint pass and only the behavior test is red.
- [x] The agent found and fixed it from the failure message alone — never told what was wrong.
- [x] The check is green and the plant is gone from the final diff.
