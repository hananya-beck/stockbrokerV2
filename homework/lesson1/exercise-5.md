# Exercise 5 — What's in your context, and where it comes from

> Figures come from `/context` (Opus 5.5, 1M window). I ran it once right after `/clear`
> and again after sending one message.

## Fresh session (after `/clear`): 36.4k / 1M tokens (4%)

| Category | Tokens | Where it comes from |
|---|---|---|
| System prompt | 3k (0.3%) | Built into Claude Code: harness rules, tool guidance, environment info |
| System tools | 21.6k (2.2%) | Built-in tools whose schemas are sent every turn: Bash, Read, Edit, Write, Grep, Glob, Agent, Artifact, Workflow… |
| MCP tools | 1.8k (0.2%) | 467 tools from MCP servers: **datadog**, **atlassian**, **glean**, **slack**, **codesearch**, **context7**, **backstage**, and about 60 `claude_ai_*` connectors. They're loaded on demand, so only their names count here. |
| MCP tools (deferred) | 324.5k (32.4%) | The full schemas for those 467 tools. They don't count until a tool is actually loaded. Datadog accounts for most of it. |
| System tools (deferred) | 24.7k (2.5%) | Built-in tools that load on demand (WebFetch, WebSearch, Task*, Cron*…). Not counted until loaded. |
| MCP server instructions | 1.6k (0.2%) | Usage instructions supplied by the context7, datadog, and glean servers |
| Memory files | 1.9k (0.2%) | `~/.claude/CLAUDE.md`, the RTK command reference. There's no project `CLAUDE.md`. |
| Skills | 6.3k (0.6%) | Descriptions of 46 skills: plugins (`slack:*`, `sg:*`, `sg-experimental:*`), built-ins, and claude.ai-synced skills (docx, pptx, xlsx, pdf…) |
| Messages | 130 (0.0%) | Almost empty, since nothing has been sent yet |
| Free space | 930.6k (93.1%) | |
| Autocompact buffer | 33k (3.3%) | Space kept free so auto-compaction can run |

## After one message: 77k / 1M tokens (8%)

| Category | Before | After | Change |
|---|---|---|---|
| Messages | 130 | 40.1k | **+40k** |
| System tools | 21.6k | 22.3k | +0.7k (the deferred tool list and advisor tool were added) |
| Free space | 930.6k | 890k | −40.6k |
| Everything else | — | — | unchanged |

One short sentence roughly doubled the context. **Messages** grew from 130 to 40.1k tokens because it holds the full conversation: my prompt, the reply, and the pasted `/context` output, which is long because it lists every MCP tool. Tool calls and their results also land in Messages. The fixed categories (system prompt, memory, skills, MCP) were loaded at session start and stay the same size.

## Biggest category and what I'd cut

- **Biggest loaded cost: System tools at 22.3k.** It's built in and can't be cut. The biggest category overall is **deferred MCP tools at 324.5k**. It costs nothing until one of those tools is loaded, but each schema adds to the context when it is. Datadog alone has about 150 tools, several of them 1–4k tokens each.
- **Cut:** disable the Datadog MCP server and the unused `claude_ai_*` connectors for this project, using `/mcp` or `disabledMcpjsonServers` in `.claude/settings.json`. That removes about 300k of deferred schemas and most of the 1.8k of tool names, along with Datadog's server instructions.
- **Also:** avoid pasting large command output (like the full `/context` tool list) into prompts. It went straight into Messages and was the main reason context doubled after one message.
- **Why it's safe:** this project is a static GitHub Pages site plus a Python script. It has no Datadog monitoring, no Jira tickets, and no Salesforce. Nothing in exercises 1–4 used those tools, and they can be turned back on in any other project or session.
