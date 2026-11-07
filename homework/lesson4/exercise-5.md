# Exercise 5: Ship it as a plugin

**Goal:** One install gives a teammate everything I built in exercises 2–4.

## What the exercise asks
From the syllabus (Lesson 4, exercise 5; slide 58, "Marketplaces & the lifecycle"):
- Bundle the skill and the command, plus one hook that fits them, into a plugin with a manifest, inside a **marketplace folder** in the repo.
- Wire the repo so a teammate who clones it is offered the marketplace, then prove the lifecycle.
- **Done when:** `claude plugin validate` on the marketplace passes; installed, the command and skill work; disabled, the command is gone; enabled again and reloaded, it's back, with no uninstall; the marketplace path committed in settings is relative.

## What I built
```
marketplace/
├── .claude-plugin/marketplace.json      ← lists one plugin
└── stockbroker-tools/
    ├── .claude-plugin/plugin.json       ← manifest only
    ├── skills/policy-audit/             ← moved from .claude/skills/ (exercise 2)
    │   ├── SKILL.md
    │   ├── references/policy-checks.md
    │   └── scripts/audit.mjs
    ├── commands/fund-compare.md         ← moved from .claude/commands/ (exercise 4)
    └── hooks/
        ├── hooks.json                   ← PostToolUse, Edit|Write
        └── policy-reminder.mjs
```
- **Move, not copy.** A copy left in `.claude/skills/` would register `policy-audit` twice.
- **The hook.** After an edit to `index.html` or `src/**`, it reminds Claude of the policy (no browser storage, no leading slash, tokens for colors, both languages). After an edit to `data/funds.json`, it says the file is bot-generated. It uses a Node script, not a shell script, because the repo's git warns about CRLF line endings and Node runs the same as `audit.mjs`.
- **Settings.** `.claude/settings.json` declares `extraKnownMarketplaces` with `"path": "./marketplace"` and `enabledPlugins` for `stockbroker-tools@stockbroker-marketplace`. The path is relative, so it is not this laptop's absolute path.

## The gotcha
`SKILL.md` hard-coded `node .claude/skills/policy-audit/scripts/audit.mjs`. That path doesn't exist inside a plugin, so both the step and its `allowed-tools` rule now use `${CLAUDE_PLUGIN_ROOT}`. The script itself reads `process.cwd()`, so it still audits the repo it runs from.

## Lifecycle, run with the CLI (Claude Code 2.1.319)
| Step | Command | Result |
|---|---|---|
| Validate | `claude plugin validate ./marketplace` | ✔ passes, no warnings. I added a marketplace description and the plugin author to clear two warnings. |
| Install | `claude plugin install stockbroker-tools@stockbroker-marketplace` | ✔ installed, enabled |
| Use | `claude -p "/fund-compare 1168723 5109889"` | ✔ the command ran and printed the table |
| Disable | `claude plugin disable stockbroker-tools@stockbroker-marketplace` | ✘ disabled. A fresh run no longer knows `/fund-compare`; Claude had to compare the funds by hand. |
| Enable | `claude plugin enable stockbroker-tools@stockbroker-marketplace` | ✔ enabled. A fresh run prints the table again. |

- **Relative path.** The committed `.claude/settings.json` has `"path": "./marketplace"`. The CLI resolves it to the local folder, so no laptop path is committed.
- **Settings side effect.** `disable` and `enable` write the flag into the committed `.claude/settings.json`. Commit it only in its enabled state.
- **Fresh process, not `/reload-plugins`.** `claude -p` starts a new process, so it checks the state on disk. The interactive `/reload-plugins` step is still to be checked in a live session.

## Status
- [x] Plugin files written (manifest, marketplace, skill, command, hook).
- [x] Settings declare the marketplace with a relative path and enable the plugin.
- [x] Old copies removed from `.claude/skills/policy-audit/` and `.claude/commands/fund-compare.md` (`git rm`).
- [x] `claude plugin validate ./marketplace` passes.
- [x] Lifecycle: install, use, disable (command gone), enable (command back), checked with the CLI in fresh processes.
- [ ] `/reload-plugins` in a live session. *(Not checked.)*
- [x] `${CLAUDE_PLUGIN_ROOT}` expands inside the skill body. A headless run of the skill ran `node "…/marketplace/stockbroker-tools/skills/policy-audit/scripts/audit.mjs"` with the real path, and the audit passed. The `allowed-tools` rule was not separately tested, because the user's default mode is `auto`.
- [x] The hook's `additionalContext` reaches Claude. A headless run created `src/hook-probe.css`, and Claude quoted the policy reminder back. The probe file was then deleted.
