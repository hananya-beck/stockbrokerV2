# Exercise 7 — Something Claude remembers

## The fact
The daily GitHub Action ("Update fund data") commits `data/funds.json` to `main`, so a push that touches it usually gets rejected. The fix is to rebase onto `origin/main` and, if `funds.json` conflicts, keep my regenerated copy with `git checkout --theirs`. During a rebase `--theirs` is my commit, which is the opposite of what you'd expect. Never force-push over the bot.

A fresh session gets this wrong. On 2026-10-16 the first push of the fetch-script fix was rejected, and the bot's copy had been computed with the old scoring, so keeping the wrong side would have shipped stale weights.

## What was written
`~/.claude/projects/C--Users-Hananya-projects-stockbroker/memory/`
- `MEMORY.md`: one index line pointing to the topic file.
- `data-bot-push-conflicts.md`: the fact, with frontmatter (`type: project`) and **Why** / **How to apply** lines.

## What loads at session start
Only `MEMORY.md` loads, up to its first 200 lines / 25 KB. Topic files like `data-bot-push-conflicts.md` are read only when the index line looks relevant, so the index stays one line per memory.

## How to verify
In a fresh session, make a change to `data/funds.json` and say "commit and push". Claude should pull with rebase first and resolve a `funds.json` conflict with `--theirs`, without being told.

## Why `/context` shows 4 memory files

"Memory files" in `/context` counts every instruction file loaded into context, not only the auto-memory notes:

| # | File | Type | What it is |
|---|------|------|------------|
| 1 | `~\.claude\CLAUDE.md` | User | Global instructions. It only contains `@RTK.md` (15 tokens). |
| 2 | `~\.claude\RTK.md` | User | Pulled in by the `@RTK.md` import, so it counts as its own file. |
| 3 | `stockbroker\.claude\rules\static-deploy.md` | Project | The always-on rule added in Exercise 6. |
| 4 | `...\memory\MEMORY.md` | AutoMem | The auto-memory index from Exercise 7. |

The category covers CLAUDE.md files, anything they import, `.claude/rules/*.md`, and the auto-memory `MEMORY.md`.

The individual memory notes aren't counted. `data-bot-push-conflicts.md` is listed in `MEMORY.md` but isn't loaded at startup, which is why the auto-memory only costs 64 tokens. It gets read only when it's relevant.

A path-scoped rule (one with `paths:` frontmatter) also stays out of the count until you work on a file that matches its paths, so the count can change during a session.
