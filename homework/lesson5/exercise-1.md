# Exercise 1: Harness-ready gates

**Goal:** A green check you believe — the thing every later exercise leans on.

## What was already there
`npm run check` already chained `typecheck && lint && test`, and `jsconfig.json` already had `strict: true`. Two gaps kept it from being trustworthy:
- `eslint` on its own exits `0` on a pure warning — only errors fail it.
- No rule in `eslint.config.js` was set to `warn`, so that gap was never actually exercised.

## The tightening
- `eslint.config.js` — added `'no-console': 'warn'`. The repo has zero `console.*` calls today, so this costs nothing now and catches one later.
- `package.json` — `"lint": "eslint src tests"` → `"lint": "eslint --max-warnings=0 src tests"`, so a bare warning now fails the gate, not just an error.

## Proof each gate goes red
1. **Types:** appended `const _plantedTypeError = formatScore("not-a-number");` to `src/lib/formatting.js`. `npm run typecheck` → `TS2345: Argument of type 'string' is not assignable to parameter of type 'number'`, exit `2`. Reverted with `git checkout`.
2. **Lint:** appended `console.log("planted warning");` to the same file. Plain `npx eslint src tests` exits `0` (1 warning, 0 errors — the old, untrustworthy behavior). `npm run lint` (with `--max-warnings=0`) exits `1` on the exact same warning. Reverted with `git checkout`.
3. **Tests:** already covered by the existing 47 `node --test` cases (i18n parity, MCP tool/resource/prompt contracts, dispatch-run selection, API error messages) — these run the real code, not a mock.

## Proof green stays green
`npm run check` run three times in a row on the clean tree: exit `0` each time, 47/47 tests passing, no flakiness.

## Done when ✅
- [x] Types, lint and tests all run behind `npm run check`, and it exits non-zero when any of them fails.
- [x] A planted type error and a planted lint warning each turn it red — then reverted.
- [x] Three runs in a row on a clean tree give the same green.
