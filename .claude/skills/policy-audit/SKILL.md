---
name: policy-audit
description: Audit the stockbrokerV2 codebase against its AGENTS.md policy before a commit or release, covering browser storage, leading-slash paths, browser APIs in src/lib, hard-coded colors, committed tokens, he/en i18n parity and silent failures. Use when asked to "audit", "policy check", "pre-release check", "is it safe to push", "check the rules" or "sanity-check the repo". Not for reviewing fund data or scores (that's add-fund and fetch_data.py), and not for fixing scraper failures.
argument-hint: "[check ID like P3, or omit for all]"
allowed-tools: Read, Grep, Glob, Bash(node .claude/skills/policy-audit/scripts/audit.mjs), Bash(npm run check), Bash(git log *), Bash(git diff *)
---

# Policy audit

The outcome is a PASS/FAIL report per rule, with `file:line` for every failure, and the repo left unchanged unless the user asks for fixes.

What each check means and how to fix it is in [references/policy-checks.md](references/policy-checks.md).

1. Run the mechanical checks exactly as written. They are scripted so every run behaves the same:
   ```bash
   node .claude/skills/policy-audit/scripts/audit.mjs
   ```
   It needs only Node 18+, the same as `npm run check`. There's nothing to install.
2. Read every FAIL line in context before reporting it. Watch for the false positives listed in the reference.
3. Do the judgement checks M1–M3 from the reference on what changed (`git diff main...`, or the last few commits if you're on `main`).
4. Run `npm run check`. A typecheck, lint or test failure is a FAIL too. On a fresh clone, run `npm ci` first, otherwise `tsc` is not found.
5. Report in a table (ID, rule, PASS/FAIL, `file:line`). If the user asked for fixes, apply them and **go back to step 1**. You're done only when the script exits 0 and `npm run check` passes.

## Gotchas
- A P5 hit means a leaked token. Rotate it, because deleting it from the file doesn't remove it from git history.
- Don't touch `data/funds.json`. It's bot-generated.
