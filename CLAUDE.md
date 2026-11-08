@AGENTS.md

## Extensions and their rungs

The ladder is rule → command → skill → plugin → MCP, lightest first. The mod sits outside it: it is the only extension that draws a pane.

- `AGENTS.md`, `CLAUDE.md`, `.claude/rules/git-workflow.md`: rules, loaded every session. The policy and the commit rules apply to all work.
- `src/lib/CLAUDE.md` and the five path-scoped rules in `.claude/rules/`: rules that load only for their own files.
- `.claude/skills/add-fund`, `.claude/skills/policy-review`: skills, because each is a procedure used now and then, not on every session. `policy-review` runs forked onto the agent.
- `.claude/skills/bmad-*` (29 skills): skills for the BMAD workflow. Each adds a description to every session, so they are the heaviest skills here. Moving them to a plugin is proposed, not done.
- `.claude/agents/policy-reviewer.md`: an agent, because a read-only reviewer needs its own window and tool list.
- `marketplace/stockbroker-tools`: a plugin, because teammates get the policy skill, the fund-compare command and the reminder hook from one install.
- `marketplace/stock-browser`: a mod, because it draws the StockBrowser pane, which only a mod can do.
- `.mcp.json` `stockbroker`: an MCP server, because `fund_metrics` answers fund questions in any chat without a file read. A command would need the person to type it. context7 was removed from the team file.
