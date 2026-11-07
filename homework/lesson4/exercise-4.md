# Exercise 4: A command with arguments

**Goal:** A one-line trigger for a prompt I'd otherwise retype every day.

## The command: `/fund-compare`
`.claude/commands/fund-compare.md` compares two funds from `data/funds.json` by their TASE security id.

```
/fund-compare 1168723 5109889
```

- **Two arguments, comma or space.** The body reads `$ARGUMENTS` and takes the two ids from it, so `1168723 5109889` and `1168723, 5109889` both work. My first version named them `$a` and `$b`. Named arguments split on spaces only, so the comma stayed attached to `$a` (`1168723,`), and the first session run exposed it.
- **Live context before Claude reads it.** The line ``!`git log -1 --format=%cI -- data/funds.json` `` runs first and tells me when the data was last committed. Here it prints `2026-11-05T12:58:40+00:00`.
- **Pre-allowed and read-only.** `allowed-tools: Bash(git log *), Read` lets the `!` line run without a prompt. Expansion has nobody to approve a permission, so a command that asked would fail closed. The `git log` allowlist keeps it read-only.
- **File inlined with `@`.** `@data/funds.json` puts the whole fund file into the prompt, so the comparison is grounded in the committed data and not in a memory of it.
- **Missing id stops.** If either id isn't in the file, the command says so instead of guessing.
- **Output shape.** A table of `risk_adjusted_score`, `return_1y`, `return_3y`, `volatility_blended`, `stale` and `suggested_weight`, then one line on the higher score and a reminder that the score is a heuristic, not financial advice (per `AGENTS.md`).

## Why this one
Comparing two funds after the daily refresh is a question that repeats. Typing both ids and the metric list each time is the part worth saving. The capability is already in the repo (the data and the score), so the command only names the question.

## Session runs
- `/fund-compare 1168723, 5109889` produced the table and the verdict. Renewable Energy won on score (1.102 against 1.079). That run is where the comma bug showed up.
- Still open: a space-only run (`/fund-compare 1168723 5109889`). The body handles it by reading, not by a second run.
- No real use this week yet. The "used at least three times" check is still open.

## Done when
- [x] Typing it with two values does the job, each value landing in the right place. Comma form run in a session; space form to confirm.
- [x] Its `!`…`` command is read-only and pre-allowed. `Bash(git log *)` is the only shell rule.
- [ ] Used at least three times on real work this week. *(Open.)*
