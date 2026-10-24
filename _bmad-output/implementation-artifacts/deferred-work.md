# Deferred work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: The daily workflow stages only data/funds.json, so data/nav-history.json is never committed.
  evidence: Review finding B4/V3. Story 1.4 owns workflow staging. Until it lands, the history file never reaches the repo.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: funds.json is written before nav-history.json with plain write_text, so a crash between them leaves the pair out of step.
  evidence: Review finding B7b/E5/O2. Atomic writes and write ordering are Story 1.4.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: Duplicate fund ids in data/funds_config.json overwrite each other in the history file.
  evidence: Review finding E7. The duplicate already appears in funds.json, so this predates Story 1.1.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: A failing fund keeps its day-first last_date in funds.json until the next successful run.
  evidence: Review finding V2. The stale path is rewritten in Story 1.3.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: The metrics path does not filter non-numeric closes, so NaN could reach funds.json.
  evidence: Review finding O1, maybe-false. Predates this change; settle by checking a bizportal response with a non-numeric C_p.

## Deferred from: code review of story-1-1 (2026-10-25)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: When every fetch fails and a previous funds.json exists, main still rewrites funds.json with all-stale entries, which breaks the fetch-script.md abort rule.
  evidence: Review finding (medium, pre-existing). The stale fallback at scripts/fetch_data.py:270-271 keeps funds non-empty, so the abort at line 274 never runs. The spec's Never list defers the all-fail abort to Story 1.3.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: A fund whose points are malformed (non-numeric C_p such as an empty string, or a missing or unparseable D_p) fails the whole fund instead of one point.
  evidence: Review finding, maybe-false. scripts/fetch_data.py:90-91 raises on these values. Settle by checking a bizportal response containing such a point; the same check settles O1.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: AGENTS.md and .claude/rules/fetch-script.md do not mention data/nav-history.json, a new output that Epic 2 depends on.
  evidence: Review finding, low. Documentation edits to agent-context files are deferred by the review routing rule.
