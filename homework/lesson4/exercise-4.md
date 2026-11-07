# Exercise 4: A command with arguments

**Goal:** A one-line trigger for a prompt I'd otherwise retype every day.

## The command: `/fund-compare`
`.claude/commands/fund-compare.md` compares two funds from `data/funds.json` by their TASE security id.

```
/fund-compare 1168723 5109889
```

- **Two arguments.** `arguments: [a, b]` names them, so the body reads `$a` and `$b`. Named reads better than `$0` and `$1`, which are 0-based and easy to get off by one.
- **Live context before Claude reads it.** The line ``!`git log -1 --format=%cI -- data/funds.json` `` runs first and tells me when the data was last committed. Here it prints `2026-11-05T12:58:40+00:00`.
- **Pre-allowed and read-only.** `allowed-tools: Bash(git log *), Read` lets the `!` line run without a prompt. Expansion has nobody to approve a permission, so a command that asked would fail closed. The `git log` allowlist keeps it read-only.
- **File inlined with `@`.** `@data/funds.json` puts the whole fund file into the prompt, so the comparison is grounded in the committed data and not in a memory of it.
- **Missing id stops.** If either id isn't in the file, the command says so instead of guessing.
- **Output shape.** A table of `risk_adjusted_score`, `return_1y`, `return_3y`, `volatility_blended`, `stale` and `suggested_weight`, then one line on the higher score and a reminder that the score is a heuristic, not financial advice (per `AGENTS.md`).

## Why this one
Comparing two funds after the daily refresh is a question that repeats. Typing both ids and the metric list each time is the part worth saving. The capability is already in the repo (the data and the score), so the command only names the question.

## What I did not do
- **Not invoked in a session yet.** I checked the `!` line and the two ids by hand (`1168723` and `5109889` both appear in `data/funds.json`). The slash command itself runs only inside Claude Code, so I still need to type `/fund-compare 1168723 5109889` once and look at the table.
- **No real use this week yet.** The "used at least three times" check is still open.

## Done when
- [ ] Typing it with two values does the job, each value landing in the right place. *(To check in a session.)*
- [x] Its `!`…`` command is read-only and pre-allowed. `Bash(git log *)` is the only shell rule.
- [ ] Used at least three times on real work this week. *(Open.)*
