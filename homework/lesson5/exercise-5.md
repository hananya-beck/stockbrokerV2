# Exercise 5: Feedback after every edit

**Goal:** The agent hears about a broken rule the moment it breaks it.

## The rule the linter can't express
`src/lib/CLAUDE.md` bans `fetch`, DOM, timers, `Date.now()` and randomness in `src/lib/` so every function there stays deterministic and testable under `node --test`. Nothing in `eslint.config.js` or `jsconfig.json` encodes this — it's a project-specific API ban on a specific directory, not a general code-quality rule a generic linter config would reach for.

## The hook: `.claude/hooks/post-edit-check.mjs`
A `PostToolUse` hook, matcher `Edit|Write`, `timeout: 30`. Checks the **path first** — only `src/lib/**/*.js` is read at all, so an edit anywhere else (README, index.html, tests/) returns before even opening the file. For files that match, it scans line by line (stripping `//` comments first, so prose *about* the rule doesn't trip the rule) for `fetch(`, `document.`/`window.`, `localStorage`/`sessionStorage`, `setTimeout(`/`setInterval(`, `Date.now()`, `Math.random()`. A hit prints `file:line: reason` to stderr and exits 2 — feedback, since the file is already written; a clean file exits 0 silently.

## Two bugs caught while building this
1. **Comment false positive on my own fixture:** the violation fixture's header comment literally contained the text `Date.now()`, so the first run flagged line 1 — a comment, not code. Reworded the comment; separately added comment-stripping to the checker itself so this class of false positive (already documented in `homework/lesson4/exercise-2.md` for the policy-audit skill) doesn't recur on real files.
2. **CRLF swallowed the comment-strip fix:** `line.replace(/\/\/.*$/, '')` silently did nothing on this repo's CRLF-terminated files, because JS's `.` never matches `\r`, so `.*` can't reach the `$` anchor through a trailing `\r` — the regex simply never matched. Caught it live: a real-session test flagged `src/lib/formatting.js`'s own header comment ("no network calls, no localStorage/IndexedDB...") as a violation. Fixed by dropping the `$` anchor (`/\/\/.*/ `) — it doesn't need to reach end-of-string, just strip from `//` onward.

## Fixtures — tested by hand before wiring in
`.claude/hooks/samples/src/lib/violation.js` (uses `Date.now()` and `fetch(`) and `safe.js` (pure), plus `post_edit_lib_violation.json` / `post_edit_lib_safe.json` / `post_edit_unrelated.json` (a `README.md` edit, to prove the path check short-circuits). Violation → exit 2 with two correct findings (lines 3–4, not the comment on line 1). Safe and unrelated → exit 0, silent.

## Wiring — `.claude/settings.json`
```json
"PostToolUse": [{ "matcher": "Edit|Write", "hooks": [{ "type": "command",
  "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-edit-check.mjs",
  "timeout": 30 }] }]
```

## Proof in a live session
Asked a disposable session, explicitly *without* reading any rule files first, to add `nowStamp()` returning `Date.now()` to `src/lib/formatting.js`, and told it to self-correct in the same turn without asking. It wrote the violating version, the hook flagged it, and in the same turn it:
- Recognized it hadn't yet seen `src/lib/CLAUDE.md`'s rules when it wrote the first version.
- Rewrote `nowStamp` to take the clock from the caller (`nowStamp(now) { return now.getTime(); }`), matching the existing pattern in `formatRelativeTime(isoDate, now)`.
- Added a test, per the module's other rule ("every export needs a test").
- Confirmed `npm run check` green, 48/48 tests, and reported exactly what it changed and why — without being told what was wrong.

(The test edit was reverted afterward — this write-up is the record, not a kept feature.)

## Why this hook didn't prevent the edit — and why that's fine here
`PostToolUse` fires after the tool already ran; the file was already on disk with `Date.now()` in it for a moment. That's fine because nothing *irreversible* happened — a local file write, not a shipped artifact or a side effect outside the repo. The things that actually need to be irreversible-proof (`rm -rf`, `.env`, the settings file) already have `PreToolUse` guards from exercises 3–4, which really do block. This one is deliberately a feedback loop, not a gate: it catches a class of mistake (an architectural/API rule, not a syntax error) that's cheap to say out loud after the fact and cheap for the agent to fix immediately, without needing to pre-validate every edit before it's written.

## Done when ✅
- [x] A fixture that breaks the rule exits 2 with a finding on stderr; one that respects it stays silent.
- [x] In a session, the agent makes the violating edit, gets the finding, and fixes it in the same turn.
- [x] Can say why this hook didn't prevent the edit, and why that's fine here.
