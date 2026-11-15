# Exercise 8: Rules, then a feature in Auto

**Goal:** Spend the autonomy you've just earned — on real work.

## Permissions — `.claude/settings.json`
```json
"permissions": {
  "allow": [ "Bash(npm run check)", "Bash(npm run typecheck)", "Bash(npm run lint)",
             "Bash(npm test)", "Bash(python -m pytest *)", "Bash(python -m ruff check *)",
             "Bash(python -m mypy *)" ],
  "ask":   [ "Bash(git push *)", "Bash(npm install *)", "Bash(npm ci *)" ],
  "deny":  [ "Read(./.env)", "Read(./.env.*)", "Bash(rm -rf *)", "Bash(npm publish *)" ]
}
```
The routine-check `allow` entries are exact matches (`npm run check`, not `npm run *`), so
they keep working in Auto — a wildcard allow would get dropped the moment Auto's own
classifier takes over (per slide 74). `deny` closes a gap the exercise-3/4 hooks didn't
cover: those hooks guard *writes* and dangerous shell patterns, but nothing previously
stopped a plain `Read` of `.env*` — the permission-level deny does, independent of any
hook. `rm -rf`/`npm publish` are denied here too, on top of `guard-bash.sh` — redundant
by design: one is a hook (can be edited by a future, less-careful me), the other is
permission config (checked earlier, before any hook even runs).

## Spent in Auto: CSV export
Ran a disposable session rooted in the repo with `--permission-mode auto`, gave it one
prompt — add a CSV-export button for the ranked funds table, pure data-shaping in
`src/lib` with tests, browser download wiring in `index.html` — and did not touch
anything while it worked.

**Result, unsupervised:**
- `src/lib/csv.js` (`escapeCsvField`, `toCsvRow`, `buildFundsCsv`) + `tests/js/csv.test.js`
  — RFC 4180 quoting, no DOM/fetch, matches `src/lib/CLAUDE.md`.
- `src/lib/i18n.js` — three new strings in both `he` and `en`.
- `index.html` — a disabled-until-loaded export button, styled from `tokens.css` only,
  a UTF-8-BOM-prefixed `Blob` download (so Hebrew names don't mojibake in Excel), errors
  surfaced through the existing status line rather than swallowed.
- `npm run check`: typecheck + lint + **58/58 tests** (11 new), green.
- `stockbroker-tools:policy-audit`: all six checks PASS (storage, leading-slash, browser
  APIs in `src/lib`, hard-coded colors, committed tokens, he/en parity).
- It correctly declined to commit on its own — it didn't know the exercise number for
  the subject line, and noticed my own uncommitted `.claude/settings.json` /
  `src/lib/refresh.js` changes sitting in the tree and left them alone.

No edits by me — I reviewed the diff after the fact, didn't change anything in it.

## Boundaries, re-checked in Auto
Two more disposable Auto-mode sessions, each a single targeted ask:
- `git push origin feat/level-6` → **did not push.** Reported that Bash needs a
  permission that hasn't been granted in this (non-interactive) session, and asked me to
  grant it or run it myself — the `ask` rule held even in Auto.
- `Read .env` → **refused outright**, citing the `deny` rule, and explicitly didn't try
  routing around it through `Bash cat .env` — the `deny` rule held, and it recognized a
  restriction rather than finding a side door.

## The audit log, read after the run
`logs/agent-audit.jsonl` across all three sessions: 26 lines — 3 `SessionStart`, and
`PreToolUse` broken down as 11 `Edit`, 6 `Bash`, 4 `Read`, 2 `Write`. From the log alone:
every file written (`Write`/`Edit` targets: `src/lib/csv.js`, `src/lib/i18n.js`,
`tests/js/csv.test.js`, `index.html`) and every command that ran (`Bash` targets,
including the attempted `git push origin feat/level-6`) are both directly readable.

**One thing I'd tighten:** the log can't currently tell a command that *ran* from one
that was *attempted and blocked* — the `git push` line looks identical to a successful
push. Exercise 7's hook only records that `PreToolUse` fired, not the resulting
`permissionDecision`. Worth adding that field next.

**One thing I'd loosen:** the catch-all `PreToolUse` matcher (`"*"`) logs plain `Read`
calls too — 4 of this run's 26 lines are reads that never touched anything and add
nothing an auditor would ask about. Narrowing the matcher to skip pure `Read` (e.g.
`"Bash|Edit|Write"`) would cut a chunk of the log's volume for no loss of the "which
files were written, which commands ran" signal.

## Done when ✅
- [x] The feature works and `npm run check` is green, with no edits by me.
- [x] In Auto, `git push` still stops and asks; reading `.env` is still refused.
- [x] Read the audit log of the run; wrote down one thing to tighten, one to loosen.
