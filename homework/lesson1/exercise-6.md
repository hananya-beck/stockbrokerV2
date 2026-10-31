# Exercise 6 — Two rules and a skill

| File | Kind | Loads |
|---|---|---|
| `.claude/rules/static-deploy.md` | Always-on rule (no frontmatter) | At session start. It covers the GitHub Pages static-site constraints: no build step, relative paths, no secrets or browser storage, the bot-owned `data/funds.json`. |
| `.claude/rules/fetch-script.md` | Path-scoped rule (`paths: ["scripts/**"]`) | Only after Claude reads a file under `scripts/`. It covers the fetch script's conventions: standard library only, bizportal quirks, trading-day horizons, per-fund failure handling, offline tests. |
| `.claude/skills/add-fund/SKILL.md` | Skill | When a request like "add a fund", "track security 1234567" or a pasted bizportal link matches its description, or via `/add-fund`. |

## How to verify
1. Fresh session → `/context`. `static-deploy.md` is listed under Memory files, and `fetch-script.md` isn't.
2. Ask "what does scripts/fetch_data.py do?". After the file is read, the terminal shows a one-line `Loaded .claude/rules/fetch-script.md` notice.
3. `/skills` lists `add-fund`. Asking "I want to also track fund 5130604" (without naming the skill) picks it up.

## Why these two rules
- The deploy rule applies to every change (HTML, JS, CSS, data, workflow), so it's worth paying for in every session.
- The fetch-script rules only matter when editing the Python scraper, so scoping them to `scripts/**` keeps them out of the context for front-end work.
