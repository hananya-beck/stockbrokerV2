# Exercise 11: The lightest rung, written down

**Goal:** Every extension in the repo earns its weight, and the next person knows why it's there.

## What the exercise asks
From the syllabus (Level 5 homework, exercise 11; slide 64, "Which one? Take the lightest rung").
- List every extension the repo carries: rules, commands, skills, plugin, mod, MCP servers, agents. For each, say why it sits on its rung and not the one below. Move or remove at least one that's heavier than it needs to be. Write the result into `CLAUDE.md`.
- **Done when:** `CLAUDE.md` has a short section with each extension, its rung and a one-line reason. At least one extension moved down a rung or was removed, and the commit says why. The MCP server count is one you can defend, and `/context` before and after is in the commit message.

## The inventory
The section in `CLAUDE.md` lists each extension with its rung and reason. In short:

| Rung | Extensions |
| --- | --- |
| rule, always loaded | `AGENTS.md`, `CLAUDE.md`, `git-workflow.md` |
| rule, path-scoped | `src/lib/CLAUDE.md` and five rules in `.claude/rules/` |
| command | `add-fund` (moved down from a skill) |
| skill | `policy-review` (forked), and 29 `bmad-*` skills |
| agent | `policy-reviewer` |
| plugin | `stockbroker-tools` (policy skill, fund-compare command, reminder hook) |
| mod | `stock-browser` (the pane, outside the ladder) |
| MCP | `stockbroker` (one team server) |

## The change
- **Removed: the `context7` MCP server from the team file** (`.mcp.json`, commit `49f8c0b`). The repo has no library code to look up, and its two tools load into every session of anyone who trusts the folder.
- **Measured with `/context`.** In a clean config (no user-level servers), with the team file as it was: deferred MCP tools 10.1k tokens. With the change: 8.3k. The `context7` rows are gone. On this machine, `context7` also comes from user scope, so `/context` doesn't change here.

## Moved down a rung
- **`add-fund`: skill → command** (`.claude/commands/add-fund.md`). It writes the fund config and README, runs the fetch and commits, so the person should start it on purpose. As a skill, it could also start from a loose phrase like "remove a fund" through its description. As a command, it starts only when the person types `/add-fund`, and its arguments are the ID and names.
- **Measured with `/context`.** The `add-fund` row dropped from about 110 tokens to about 60. The Skills total still reads 9.7k at this rounding.
- **Checked.** `/add-fund` with no argument asks for the ID and the two names and changes nothing; `git status` shows only the rename.

## Why the rest stays
- **`stockbroker` MCP.** Its `fund_metrics` tool answers "how did this fund do" in any chat without a file read. A command would need the person to type it, and the model couldn't call it on its own.
- **`stock-browser` mod.** It draws the pane. Nothing lower on the ladder can.
- **`stockbroker-tools` plugin.** Exercise 5 requires it, and teammates get it from one install. Its hook is the only part that runs on every edit; it stays because exercise 5 asks for it.
- **Path-scoped rules.** They load only for their own files, which is already the lightest form for file-specific guidance.

## Proposed, not done
- **Move the 29 `bmad-*` skills out of `.claude/skills/`.** Each one adds a description to every session, so they are the heaviest skills here. Moving them into a plugin would mean they load only for people who install it. The BMAD workflow is in use for epic 1, so this is for you to decide.

## Checks
- [x] `CLAUDE.md` has the section with each extension, its rung and a reason.
- [x] One extension was removed (`context7`), and the commit says why and carries the `/context` numbers.
- [x] One extension moved down a rung (`add-fund`: skill → command), and its commit says why.
- [x] The team MCP count is one (`stockbroker`), defended above.
- [ ] Not done: moving the BMAD skills into a plugin (proposed above).
