# Exercise 8: One clone, full setup

**Goal:** The Level 5 setup works for someone who isn't me, not just on my laptop.

## What the exercise asks
From the syllabus (Level 5 homework, exercise 8; the Plugins section). The brief adds the file-viewer mod to the marketplace; here the mod is the StockBrowser mod.
- Add the mod to the marketplace from exercise 5. Clone the repo into a fresh folder, as a teammate would, start Claude Code there, and accept only what it offers. Fix each failure in the repo and commit it. Never patch the clone by hand.
- **Done when:** in the fresh clone, after trusting the folder, Claude Code offers the marketplace and its plugins, and nothing needs an install path typed. The MCP server connects, the skill and command run, and the pane opens. The repo holds no absolute path, no secret and nothing that exists only on this machine. Each fix is its own commit.

## Fixes, one commit each
| Commit | Failure in a fresh clone | Fix |
| --- | --- | --- |
| `b8667a3` | `mods/stock-browser/tsconfig.json` extends the engine's gitignored types folder | removed the tsconfig |
| `b3f00bf` | the mod wasn't in the marketplace; a plugin source can't use `../` | moved the mod to `marketplace/stock-browser` and listed it |
| `9ac5ff5` | `.mcp.json` named `codebase-memory-mcp`, a binary installed only on this machine | removed that entry from the team file |
| `5e3557e` | `_bmad-output/implementation-artifacts/sprint-status.yaml` had absolute paths to this laptop | made the refs repo-relative |
| `7877465` | `prompts/exercise-10-orchestrator.md` named this laptop's repo and scratch folders | made both repo-relative or scratchpad-relative |
| `25d2e9b` | `.claude/rules/git-workflow.md` named this laptop's profile path | refers to the user's global `CLAUDE.md` |
| `f07bed2` | the team file didn't enable the StockBrowser plugin | enabled `stock-browser@stockbroker-marketplace` |

Exercise 6 and 7 write-ups now point at `marketplace/stock-browser` for `--plugin-dir`.

## Checks
- [x] `claude plugin validate ./marketplace` passes, with both plugins.
- [x] A fresh clone of the repo (committed state only) has no absolute path to this laptop.
- [x] In the fresh clone, `claude -p "/stock-browser"` runs with no install step: it prints `stock-browser: StockBrowser pane opened.` The plugin isn't installed at user level, so it came from the team file. The run also printed that the workspace isn't trusted and its `permissions.allow` entries were ignored.
- [x] `claude mcp list` in the fresh clone shows the `stockbroker` server, pending approval. It's defined in the repo, and a teammate approves it in an interactive session.
- [ ] **Interactive, not checked here:** in the fresh clone, accept the trust dialog, then check that Claude Code offers the marketplace and its plugins without an install path.
- [x] Approving the `stockbroker` MCP server first failed with a missing package: a clone has no `node_modules`. `npm ci` fixes it, and the server then answers the MCP handshake. The README now says to run it (`0910ef0`).
- [ ] **Interactive:** approve the `stockbroker` MCP server in the clone and check that it connects.
- [ ] **Interactive:** in the fresh clone, `/stock-browser` opens the pane beside the chat.
- [ ] Not checked: `/fund-compare` and the policy-audit skill in the fresh clone. This machine also has `stockbroker-tools` installed at user level, so the run can't show whether the team file alone enables it.

## Open for the owner
- **`context7` is defined twice.** The project file uses the public endpoint, `https://mcp.context7.com/mcp`. This machine's user scope uses a SeatGeek gateway. Claude Code warns about the conflict. Keep one; removing the user-scope entry is a change to this machine's config, so I didn't make it.
- **`"model": "haiku"` and `"effortLevel": "high"` in the team file** apply to every teammate. I left them as they were.
- **Untrusted run.** The headless run in the untrusted clone still loaded and ran the enabled plugin. Only the permission rules were skipped. Whether a plugin should run before trust is a question for Claude Code, not for this repo.

## Status
The fresh-clone failures are fixed, each in its own commit. The interactive trust, MCP approval and pane checks are still open.
