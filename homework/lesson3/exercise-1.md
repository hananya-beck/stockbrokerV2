# Exercise 1 — your own MCP server, three primitives

> Built on the stockbrokerV2 project (the funds dashboard), not on a file browser. The server reads `data/funds.json` and nothing else.

## What I built

- **`mcp/stockbroker.js`:** a stdio MCP server on `@modelcontextprotocol/sdk` 1.32.2, with zod 4 schemas.
  - **Tool `fund_metrics`:** reads one fund by id. `fund_id` is `z.enum` over the seven ids in `data/funds.json` (read at startup), so anything else is rejected by the schema. The description says what it returns and when to use it.
  - **Resource `stockbroker://funds`:** a markdown table of every fund's id, name, suggested weight, score and stale flag, with the data timestamp. You attach it with `@`.
  - **Prompt `monthly_split`:** takes an optional `amount` and asks for the split by suggested weight. It shows up as `/mcp__stockbroker__monthly_split`.
  - Read-only throughout. It never writes files and never refreshes data.
  - The data path comes from `STOCKBROKER_DATA_PATH`. The server throws at startup if the variable is unset, so a successful connection proves the `.mcp.json` default was applied.
- **`.mcp.json`:** a `stockbroker` entry (`node mcp/stockbroker.js`) with `"STOCKBROKER_DATA_PATH": "${STOCKBROKER_DATA_PATH:-data/funds.json}"`. No secrets.
- **`tests/js/mcp.test.js`:** five tests that run the server through the SDK's stdio client: the three primitives are listed, `fund_metrics` returns a known fund, a bad id is rejected, the resource lists every fund, and `monthly_split` puts the amount in its message. They run inside `npm run check`.

## Done when — status

| Done when | Status | How it was checked |
| --- | --- | --- |
| `/mcp` shows it Connected | **Pass** | `claude mcp list` → `stockbroker: node mcp/stockbroker.js - ✔ Connected`. Checked with the CLI, not the interactive `/mcp` panel. |
| `claude mcp get` says the scope is project | **Pass** | `Scope: Project config (shared via .mcp.json)` |
| Claude calls the tool on its own | **Pass** | `claude -p "What is fund 5109889's 1-year volatility?"`: the transcript has a `mcp__stockbroker__fund_metrics` tool call, and Claude answered `18.0%`, which matches the tool's `Volatility 1y: 18.0%`. |
| `@` attaches the resource | **Pass** | `claude -p "@stockbroker:stockbroker://funds …"`: the transcript includes the `Funds summary` markdown table, and Claude answered from it. |
| `/mcp__stockbroker__monthly_split` runs the prompt | **Pass** | `claude -p "/mcp__stockbroker__monthly_split 10000"` returned a split of ₪10,000 by suggested weight, for example `TASE 125 · 20.2% · ₪2,020`. |
| Bad input is rejected by the schema | **Pass** | Test: `fund_metrics` with id `0000000` returns `isError` with `Invalid arguments for tool fund_metrics`. The handler never runs. |
| Nothing secret in `.mcp.json` | **Pass** | The file holds only the variable reference and the default path. |

`npm run check` passes: typecheck, lint, and 47 tests, including the five new MCP tests.

The headless runs used `claude -p` with the server approved in `.claude/settings.local.json`, which is gitignored. The interactive `/mcp` panel itself wasn't opened, so the Connected check is the CLI equivalent.
