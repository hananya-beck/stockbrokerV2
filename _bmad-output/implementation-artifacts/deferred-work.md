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
