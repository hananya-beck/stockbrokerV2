# Exercise 10: context7, for the whole team

## The server
`.mcp.json` is committed with context7 at project scope, so anyone who clones the repo gets it:

```
claude mcp add --transport http --scope project context7 https://mcp.context7.com/mcp
```

```json
{ "mcpServers": { "context7": { "type": "http", "url": "https://mcp.context7.com/mcp" } } }
```

It holds no secrets. context7 works without an API key, and I didn't use my user-level context7, which goes through an internal company gateway, because that would leak an internal hostname into a public repo. On first launch Claude Code asks to approve the project server (`claude mcp reset-project-choices` undoes that choice). After that, `/mcp` lists `context7` as connected.

## The feature: poll the exact refresh run
**Prompt:** "Improve the refresh button's polling. Use the GitHub REST API's list-workflow-runs filters (event, created) so we stop scanning the run list by hand. Check current GitHub docs through context7 first."

**What context7 returned** (`resolve-library-id` → `/websites/github_en_rest`, then `query-docs`):
- `GET …/actions/runs` accepts `created` (search date-range syntax), `event`, `branch` and `per_page`.
- **REST API version `2026-03-10`** changed `POST …/workflows/{id}/dispatches` from `204` (no body) to `200` with `{ workflow_run_id, run_url, html_url }`. Requests without `X-GitHub-Api-Version` still get `2022-11-28`.

The second result is too new for training memory, and it changed the plan. The old code had a comment saying "the dispatch endpoint returns no run id, so we match by creation time". That's no longer true, so the page can now poll the exact run.

**The change**
- `src/lib/refresh.js`: new pure `dispatchedRunId(body)` reads `workflow_run_id`. It returns `null` for a 204 body or an invalid id. `pickDispatchedRun` stays as the fallback.
- `index.html`: dispatch sends `X-GitHub-Api-Version: 2026-03-10`, then polls `GET /actions/runs/{id}`. If no id comes back, it falls back to the run list, now narrowed server-side with `created>=` (click time minus 30s).
- `tests/js/refresh.test.js`: 3 new tests (200 body, empty/204 body, invalid ids). `npm run check` passes with 29 tests.

## Proof the server was used
The session transcript shows `mcp__context7__resolve-library-id` ("GitHub REST API") and two `mcp__context7__query-docs` calls on `/websites/github_en_rest` (workflow-runs parameters, then the `X-GitHub-Api-Version` header). Note: this session started before `.mcp.json` existed, so these calls went to the context7 that was already connected (same tool names). The project-scoped server takes over from the next session.
