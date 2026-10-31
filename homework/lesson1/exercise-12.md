# Exercise 12: Ask a code graph instead of grepping

## The server
`.mcp.json` now lists `codebase-memory-mcp` alongside context7, at project scope. It's a local stdio server that indexes the repo into a call graph:

```json
"codebase-memory-mcp": { "type": "stdio", "command": "codebase-memory-mcp", "args": [] }
```

It runs on the machine, so nothing is sent off it and the repo gets no secrets. Anyone who clones the repo needs the `codebase-memory-mcp` binary on their `PATH`.

## The question
**Prompt:** "please ask the graph which functions call describeRunState"

Claude loaded the deferred `trace_path` tool and made one call:
`trace_path(function_name="describeRunState", project="stockbroker", direction="inbound", depth=1, include_tests=true)`

**What the graph returned:**

| Caller | Hop | Test |
|---|---|---|
| `refresh` (`index.html`) | 1 | no |
| `tests/js/refresh.test.js` | 1 | yes |

`callers_total: 2`, with `callers_total_relation: eq`, so the count is exact and not a lower bound.

## Checked against grep
- `index.html:319` and `:323` are both inside `async function refresh()` (line 292). One polls the exact dispatched run and the other is the fallback list match. Grep shows two call sites, and the graph merges them into one caller edge.
- `tests/js/refresh.test.js` has four `describeRunState` tests (lines 53–67).
- `src/lib/refresh.js:58` is the definition, so it isn't a caller.

The graph was right. It answered in terms of functions, not text lines. Grep also matched the two `import` lines, which the graph correctly skips.

## Where the graph helps and where it doesn't
- **It helps** with "who calls X", multi-hop paths ("what does a click on רענן נתונים reach?") and impact checks before a refactor, especially as the repo grows. Grep can't follow calls through aliases or across several hops.
- **It doesn't help** much on a repo this size. One grep found the same answer and cost about as much. Grep is also the only way to find literals, such as Hebrew strings or color values, since those aren't graph symbols.
- **Context cost:** the server's tools are deferred, so they cost almost nothing until one is loaded. `/context` after the question showed Messages at 24.1k and MCP tools at 2.6k, out of 60.8k used.
