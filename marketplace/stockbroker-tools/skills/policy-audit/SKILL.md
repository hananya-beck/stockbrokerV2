---
name: policy-audit
description: Audits stockbrokerV2 against its AGENTS.md policy before a commit, push or release, with a PASS/FAIL per rule and file:line for each failure. It covers browser storage, leading-slash paths, browser APIs in src/lib, hard-coded colors, committed tokens, he/en i18n parity and silent failures. Use when the user asks whether the repo is ready to ship, for example "audit the repo", "policy check", "pre-release check", "is it safe to push", "can I commit this", "check the rules", "sanity-check before I push" or "בדוק שהכל תקין לפני push". Not for reviewing a diff for bugs or code quality (use bmad-code-review or bmad-review), not for fund data or scores (add-fund, fetch_data.py), and not for fixing scraper failures.
argument-hint: "[check ID like P3, or omit for all]"
allowed-tools: Read, Grep, Glob, Bash(node ${CLAUDE_PLUGIN_ROOT}/skills/policy-audit/scripts/audit.mjs), Bash(npm run check), Bash(git log *), Bash(git diff *)
---

# Policy audit

The outcome is a PASS/FAIL report per rule, with `file:line` for every failure, and the repo left unchanged unless the user asks for fixes.

What each check means and how to fix it is in [references/policy-checks.md](references/policy-checks.md).

1. Run the mechanical checks exactly as written. They are scripted so every run behaves the same. Run them from the repo root:
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/skills/policy-audit/scripts/audit.mjs"
   ```
   It needs only Node 18+, the same as `npm run check`. There's nothing to install.
2. Read every FAIL line in context before reporting it. Watch for the false positives listed in the reference.
3. Do the judgement checks M1–M3 from the reference on what changed (`git diff main...`, or the last few commits if you're on `main`).
4. Run `npm run check`. A typecheck, lint or test failure is a FAIL too. On a fresh clone, run `npm ci` first, otherwise `tsc` is not found.
5. Report in a table (ID, rule, PASS/FAIL, `file:line`). If the user asked for fixes, apply them and **go back to step 1**. You're done only when the script exits 0 and `npm run check` passes.

## Gotchas
- A P5 hit means a leaked token. Rotate it, because deleting it from the file doesn't remove it from git history.
- Don't touch `data/funds.json`. It's bot-generated.
