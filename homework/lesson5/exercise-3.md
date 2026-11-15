# Exercise 3: A guard on the shell

**Goal:** A rule the agent cannot argue with.

## The hook: `.claude/hooks/guard-bash.sh`
A `PreToolUse` hook on the `Bash` matcher. Reads the stdin JSON (`.tool_input.command` — not an env var), and refuses three commands this project must never run, each with its own reason on stderr and `exit 2`:

1. **Recursive force-delete** — `rm -rf` / `-fr` / `--recursive --force` in any flag order.
2. **`npm publish`** — `package.json` has `"private": true`; this package was never meant to ship to a registry.
3. **Force-push** — `--force`, `--force-with-lease`, or `-f` — would wipe the daily data-bot's commits on `main` (`AGENTS.md` policy already forbids this by hand; the hook makes it unarguable).

Anything else prints nothing and exits 0 — permissions still apply on top.

## Fixtures — tested by hand before wiring in
`.claude/hooks/samples/`:
- `pre_bash_dangerous.json` — `rm -rf dist src/lib` → blocked, reason on stderr, exit 2.
- `pre_bash_dangerous_publish.json` — `npm publish --access public` → blocked, exit 2.
- `pre_bash_dangerous_forcepush.json` — `git push --force origin main` → blocked, exit 2.
- `pre_bash_safe.json` — `npm run check` → silent, exit 0.

Also hand-checked near-misses that must **not** false-positive: `rm file.txt`, `git push origin feat/level-6`, `git push --follow-tags origin main`, `npm run build` — all exit 0. `git push --force-with-lease` — correctly still blocked.

## Wiring — `.claude/settings.json`
```json
"hooks": { "PreToolUse": [
  { "matcher": "Bash", "hooks": [{ "type": "command",
    "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard-bash.sh" }] }
] }
```

## Proof in a live session
Ran a disposable headless session (`claude -p --permission-mode acceptEdits` — not `--dangerously-skip-permissions`; my own session's auto-mode classifier correctly refused that flag as "undermining oversight" when I first tried it, so I ran the live test without it instead) rooted in this repo:
- Asked it to run `npm publish --access public`. It was refused by `guard-bash.sh` and reported back: *"The project's `guard-bash.sh` hook blocked `npm publish --access public`, with this message: 'npm publish is never allowed — package.json has "private": true.'"* It didn't try to work around the hook.
- Asked it to run `npm run check`. It ran normally and reported exit 0, 47/47 tests passing — the hook doesn't interfere with legitimate commands.

`npm publish` was chosen for the live-fire test specifically because it's doubly safe: even if the hook had failed, `npm` itself refuses to publish a `"private": true` package.

## Done when ✅
- [x] Piped the dangerous fixtures, the script prints its reason to stderr and exits 2; piped the safe one, it stays silent and exits 0.
- [x] In a session, asking for one of those commands is refused and Claude reports the reason.
- [x] A normal command like the check command still runs.
