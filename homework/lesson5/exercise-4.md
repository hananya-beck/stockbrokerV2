# Exercise 4: A guard on your files

**Goal:** The harness protects itself — the agent can't edit away its own limits.

## The hook: `.claude/hooks/guard-writes.mjs`
A second `PreToolUse` hook, matcher `"Edit|Write"` (exact tool names, not `"*"` — it must not fire on every tool call, only the ones that write). Unlike exercise 3's exit-code guard, this one answers in **JSON**, per the contract: a deny prints
```json
{ "hookSpecificOutput": { "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "…" } }
```
and exits 0 (exit code isn't the signal here — the JSON is).

Denies writes to:
1. **`.env*`** — AGENTS.md: no secrets in the repo; the refresh button's token is typed in at runtime, never stored.
2. **`.claude/settings.json`** — this is the "self-protection" rule: the harness's own wiring can't be edited away by the agent that's governed by it.
3. **`data/funds.json` / `data/nav-history.json`** — this repo's stand-in for "build output": not compiled output (no build step exists — AGENTS.md forbids one), but the other kind of generated artifact: AGENTS.md already says "Never hand-edit `data/funds.json`" since the daily bot owns it.

## Fixtures — tested by hand before wiring in
`.claude/hooks/samples/`: `pre_write_env.json`, `pre_write_settings.json`, `pre_write_funds.json` — each piped through `node guard-writes.mjs` printed the JSON deny with its reason, exit 0. `pre_write_safe.json` (an edit to `src/lib/formatting.js`) printed nothing, exit 0.

## Wiring — `.claude/settings.json`
Added a second `PreToolUse` entry alongside exercise 3's `Bash` guard:
```json
{ "matcher": "Edit|Write", "hooks": [{ "type": "command",
  "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard-writes.mjs" }] }
```

## Proof in a live session
Two disposable headless sessions rooted in this repo:
- Asked it to write `GITHUB_TOKEN=abc123` to `.env`. Refused, hook's reason reported verbatim; it didn't try a shell redirect to work around it, and pointed out the project doesn't even use a `.env` file.
- Asked it to edit `.claude/settings.json` (flip the model). Refused, reason reported; it didn't try `sed`, and correctly suggested `/model opus` as a way to achieve the same thing without touching the protected file — the self-lockout the exercise warns about, live.

## The self-lockout, for real
This is also the moment section B's note becomes true: **a live Claude Code session rooted in this repo can no longer edit `.claude/settings.json` through the agent.** I'm doing this homework from outside that project's working directory (editing files directly, not through a `claude` session whose cwd is this repo), so this particular hook doesn't block *my* edits here — but it would block a real interactive session the way the two tests above show. From exercise 5 on, any new hook wiring into this repo's `settings.json` has to be a direct file edit, not something asked of a live agent working inside it.

## Done when ✅
- [x] A protected-path fixture prints a JSON `deny` with a reason and exits 0; a normal source file passes silently.
- [x] In a session, the agent is refused on `.env` and on the settings file, with the reason.
- [x] Its matcher (`Edit|Write`) fires only on the tools that write — not on every tool call.
