# Exercise 2: A skill from work you did once

**Goal:** Package a procedure I'd already proven, not one I imagined.

## The task I did by hand first
I picked a **pre-push policy audit** of stockbrokerV2: check the code against the Policy section of `AGENTS.md` and the rules in `src/lib/CLAUDE.md`. I do this before every push, because the site is public and served as-is from GitHub Pages.

With Claude, I ran the checks as ad-hoc greps:
- browser storage (`localStorage`, `sessionStorage`, IndexedDB, cookies) in `index.html` and `src/`
- leading-`/` paths in `src=`, `href=`, `import` and `fetch()`
- `fetch`, DOM, `window` and timers inside `src/lib/`
- hard-coded colors outside `src/styles/tokens.css`
- GitHub tokens committed anywhere
- `STRINGS.he` and `STRINGS.en` key parity in `src/lib/i18n.js`

**Result:** every check passed. The run surfaced the gotchas that shaped the skill:
- **False positives from comments.** `formatting.js` and `i18n.js` say "No fetch… no localStorage" in their header comments, so a naive grep flags them.
- **Output filtering.** The shell's output filter hid some grep results, and they only showed up with `rtk bypass`. Running the checks through a script removes that variance.
- **Platform.** grep/regex flags differ between Git Bash and other shells. A Node script behaves the same everywhere.

## The skill: `.claude/skills/policy-audit/`
```
policy-audit/
├── SKILL.md                    26 lines: outcome, steps, gotchas, done-when
├── references/policy-checks.md  P1–P6 (scripted) + M1–M3 (judgement): rule, why, fix, false positives
└── scripts/audit.mjs            the fragile step: deterministic PASS/FAIL, exit code 0/1
```
- **Description routes:** it says what the skill does, when to use it, the phrases people actually type ("is it safe to push", "sanity-check the repo"), and what it's *not* for (fund data → `add-fund`, scraper failures).
- **Freedom matches fragility:** the mechanical checks are a script run exactly as written. The judgement checks (no hard-coded UI text, no silent failures, `funds.json` untouched) are left to the model, and the reference file explains them.
- **Checklist and loop:** step 5 says "fix, then **go back to step 1**". Done means the script exits 0 and `npm run check` passes.
- **Portable:** the script needs only Node 18+ and no npm install, which is stated next to the command in `SKILL.md` and in the script header.

## Verification
1. **Clean repo:** all six checks PASS, exit 0.
2. **Planted violations:** I appended a line with `localStorage`, `fetch("/data/x.json")` and `"#ff0000"` to `src/lib/refresh.js`. The script flagged P1–P4 with `file:line` and exited 1. I reverted with `git checkout`.
3. **Fresh session, skill not named:** `claude -p "Is the repo safe to push? Sanity-check it against our project rules."` loaded `policy-audit` from its description, ran the script, did M1–M3, ran `npm run check` and pytest, and returned a PASS table. Each check came with its evidence.
4. **What the fresh run taught me:** on a fresh clone, `npm run check` fails until `npm ci` has been run. I added that to step 4 of `SKILL.md`, which is exactly the kind of edge case a skill written before doing the task would miss.

## Done when ✅
- [x] The skill lives in `.claude/skills/policy-audit/`, and `SKILL.md` is under 500 lines (26).
- [x] Every helper is linked straight from `SKILL.md`, one level deep.
- [x] A fresh session did the task again and checked its own result before saying it was done.
- [x] The fragile step is a script (`audit.mjs`), with what it needs (Node 18+) written beside it.
