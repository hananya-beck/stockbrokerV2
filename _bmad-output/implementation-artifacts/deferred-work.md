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
  summary: The metrics path does not filter non-numeric closes, so NaN could reach funds.json.
  evidence: Review finding O1, maybe-false. Predates this change; settle by checking a bizportal response with a non-numeric C_p.

## Deferred from: code review of story-1-1 (2026-10-25)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: A fund whose points are malformed (non-numeric C_p such as an empty string, or a missing or unparseable D_p) fails the whole fund instead of one point.
  evidence: Review finding, maybe-false. scripts/fetch_data.py:90-91 raises on these values. Settle by checking a bizportal response containing such a point; the same check settles O1.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-store-each-fund-s-daily-nav-series.md`
  summary: AGENTS.md and .claude/rules/fetch-script.md do not mention data/nav-history.json, a new output that Epic 2 depends on.
  evidence: Review finding, low. Documentation edits to agent-context files are deferred by the review routing rule.

## Deferred from: code review of story-1-3 (2026-10-25)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-keep-the-last-good-data-when-a-fetch-fails.md`
  summary: .claude/rules/fetch-script.md still describes only the previous-metrics fallback, not the all-null entry for a fund with no previous data or the stale flag in nav-history.json.
  evidence: Review findings, low. The fix edits an agent-context file; batch it with the nav-history.json documentation item above.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-keep-the-last-good-data-when-a-fetch-fails.md`
  summary: A malformed entry or an unparseable previous funds.json is swallowed by a bare except in main, so every failed fund falls back to all-null metrics without a message.
  evidence: Review findings, low, pre-existing read at scripts/fetch_data.py:357. The history file is unaffected and keeps its points. Settle by printing a warning when the read fails.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-keep-the-last-good-data-when-a-fetch-fails.md`
  summary: funds.json is written before nav-history.json is serialised, so a serialisation failure leaves the pair out of step.
  evidence: Review finding, medium. Story 1.4 should serialise both payloads before any write, with the atomic-write work.
