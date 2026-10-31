# Exercise 1 — settings.json across three scopes

> Written after the fact from the commit history. The user-scope and local-scope files are not in the repo, so their values come from the commit message of `01d4b3b`.

## Project scope — `.claude/settings.json`

Added in `01d4b3b` ("Add project-scope Claude Code settings"):

- `effortLevel: "high"` so every teammate gets the same default effort.
- An allowlist for the check-command tools (`npm run check`, `npm run typecheck`, `npm run lint`, `npm test`, `python -m pytest`, `python -m ruff check`, `python -m mypy`), so the team isn't prompted for them.

## User and local scope

- `effortLevel` is also set in user scope (`~/.claude/settings.json`) and local scope (`.claude/settings.local.json`) at values different from the project file. The commit says this is deliberate, to test precedence: local > project > user.
- `.claude/settings.local.json` is ignored by git through the global gitignore, so it never reaches the repo. The commit message is the only record of those values.

## One-line follow-up — `f207610`

Commit `f207610` (titled "Excerise 1") adds `"model": "haiku"` to the project `.claude/settings.json`. That is the only line this commit changes in the repo.

## What the commits don't record

- Which effort value Claude Code actually used in each scope.
- Whether the precedence check was run, and what it showed.
