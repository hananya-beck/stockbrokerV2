# Exercise 6: No "done" on red

**Goal:** "Done" stops being the agent's opinion.

## The hook: `.claude/hooks/stop-gate.mjs`
A `Stop` hook, no matcher needed (it fires once per turn end, not per tool). Runs `npm run check`; if it's red, prints the failure to stderr and exits 2 — the turn can't end, and the failure goes back to Claude. If `stop_hook_active` is true, the hook has already blocked this turn once, so it lets the turn end regardless of the check's state: a check that can never go green (or an agent that reasonably won't auto-fix something it can't confirm is a mistake) still terminates after one retry, instead of looping forever. `timeout: 60` — comfortably above the ~2.7s the real check takes.

## Hand-tested before wiring in
Using `.claude/hooks/samples/stop_fresh.json` (`stop_hook_active: false`) and `stop_retry.json` (`stop_hook_active: true`):
- **Clean tree, fresh:** exit 0, silent.
- **Replanted exercise 2's bug (`pickDispatchedRun`'s `<` flipped to `>`), fresh:** exit 2, full `npm run check` output on stderr, including the exact failing assertion (`actual: 2, expected: 1`).
- **Same plant, retry:** exit 0 — the safety valve lets it through even though the check is still red.
- Reverted the plant, confirmed exit 0 again.

## Wiring — `.claude/settings.json`
```json
"Stop": [{ "hooks": [{ "type": "command",
  "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/stop-gate.mjs",
  "timeout": 60 }] }]
```

## Proof in a live session — exercise 2's plant, twice
Per the exercise's own instruction, replanted exercise 2's bug and gave a disposable session an unrelated one-line task — this time **never mentioning any check at all**, to see whether the Stop hook forces the issue on its own.

**Pass 1 — no self-correct instruction:** It got blocked, correctly diagnosed the exact bug (file, line, the `<`→`>` flip, matching neither the doc nor the test), but noticed the diff looked like it could be *deliberate test material for this exact stop-hook homework* (inferred from recent commit history) and chose not to silently revert something it couldn't confirm was a mistake. The retry safety valve let the turn end anyway, red check and all, with that explanation. This is the "doesn't trap it in an endless loop" case working exactly as designed — including a cautious, context-aware judgment call I hadn't anticipated.

**Pass 2 — explicit "fix it, don't ask":** Same plant, told to treat any red check it finds as real and fix it before ending. It found the same bug, restored `created <`, and reported `npm run check` green, 47/47 — this is the "stops only once the check is green" case. Confirmed on disk: `git diff src/lib/refresh.js` is empty (matches HEAD) and `npm run check` exits 0.

## Done when ✅
- [x] With a red check, Claude is sent back to work with the failure; it stops only once the check is green (pass 2).
- [x] A check that can't be confirmed safe to auto-fix doesn't trap the session in an endless loop — the retry safety valve lets it end after one block (pass 1).
- [x] The hook has an explicit timeout (60s) comfortably longer than the check's real runtime (~2.7s).
