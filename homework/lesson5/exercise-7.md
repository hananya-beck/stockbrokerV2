# Exercise 7: The audit trail

**Goal:** When someone asks "what did the agent do?", you can show them.

> Correction: an earlier version of this file covered the wrong exercise (a MEMORY.md
> task that belongs to a different homework track). This is the real Level 6 exercise 7,
> from the homework panel at slide 81 (`data-hw="l6"`).

## The hook: `.claude/hooks/audit-log.mjs`
One script, reused for two events — the input's `hook_event_name` says which one fired:
- **`PreToolUse`**, matcher `"*"` — every tool call, whatever it is. Runs alongside the
  existing `Bash` and `Edit|Write` guard hooks; multiple `PreToolUse` entries all fire
  independently, so this doesn't change what those guards block.
- **`SessionStart`** — the "at least one other event."

Each call appends one JSON line to `logs/agent-audit.jsonl`:
`{ ts, session_id, event, tool, target }`. `target` is the Bash command for a `Bash`
call, or the file path for `Edit`/`Write` — never the file's content, so a write never
leaks what was written, only that it happened and to where.

**Never blocks:** the whole body is one `try { ... } catch {}` and the script always
`process.exit(0)`, success or failure. A parse error on stdin, a `logs/` that can't be
created or written (e.g. something else occupies that path) — none of it reaches the
agent as a block. The script can't throw past its own catch, and there's no code path
that exits non-zero.

## Hand-tested before wiring in
Fixtures: `audit_pretool_bash.json`, `audit_pretool_write.json`, `audit_session_start.json`.
- Bash, Edit, and SessionStart inputs each → exit 0, one well-formed JSON line appended.
- Garbage (non-JSON) stdin → exit 0, no line written, no crash.
- Empty stdin → exit 0, no line written.
- `logs` replaced with a plain file (so `mkdirSync`/`appendFileSync` both fail) → still
  exit 0, nothing thrown.
- Parsed every line in the resulting log with `JSON.parse` — all valid, all with the
  same field set for their event type.

## Wiring — `.claude/settings.json`
Added a third `PreToolUse` entry (matcher `"*"`) alongside the existing two, plus a new
`SessionStart` block:
```json
{ "matcher": "*", "hooks": [{ "type": "command",
  "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/audit-log.mjs" }] }
```
```json
"SessionStart": [{ "hooks": [{ "type": "command",
  "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/audit-log.mjs" }] }]
```

## Proof in a live session
Cleared `logs/agent-audit.jsonl`, then ran real disposable sessions against the repo:
1. `npm run check` → log got a `SessionStart` line, then two `PreToolUse`/`Bash` lines
   (the outer `tail`-piped command and the plain `npm run check` retry), each with the
   full command as `target`. The check itself still ran and reported green — the audit
   hook added zero friction.
2. A session told to append a blank line to `README.md` did it via a `Bash` redirect
   (`printf '\r\n' >> README.md`) — the log's `target` for that line is the exact command,
   so **the written file is visible straight from the log** even though the agent chose
   a shell redirect over the `Write` tool. Reverted with `git checkout -- README.md`
   afterward (session made no commit itself).

From the log alone: every `Bash` line's `target` is the literal command that ran, and
every `Edit`/`Write` line's `target` is the file path touched — satisfies "which files
were written, and which commands ran" without needing anything else.

## Done when ✅
- [x] Every line of the log parses as JSON; lines for the same event type share the same
      fields (`ts`, `session_id`, `event`, plus `tool`/`target` when applicable).
- [x] From the log alone: which files were written, which commands ran — both answerable.
- [x] Broken input and an unwritable log path both still exit 0 (hand-tested above).
