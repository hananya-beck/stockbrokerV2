# Validation Report — Backtest simulator

- **PRD:** `_bmad-output/planning-artifacts/prds/prd-stockbrokerV2-2026-10-24/prd.md`
- **Rubric:** `.claude/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-10-25
- **Grade (as reviewed):** Fair — six high findings and one thin dimension (Done-ness clarity)
- **Grade (after fixes):** not re-scored; see the revision notes below

## Overall verdict
Tidy and proportionate for a solo tool: explicit Non-Goals, indexed assumptions, contiguous IDs and one named protagonist. The risk was how far the chart can be trusted. Today's weights come from trailing scores that overlap the backtested months, so the test is in-sample, and the PRD did not say so. Several requirements also left gap-month valuation, baseline handling and backfill mechanics undefined.

## Dimension verdicts
- Decision-readiness — adequate
- Substance over theater — strong
- Strategic coherence — adequate
- Done-ness clarity — thin
- Scope honesty — adequate
- Downstream usability — adequate
- Shape fit — strong

## Findings by severity

### High (6)
- **[Strategic coherence]** Hindsight bias undisclosed (§1, §5, §7) — The in-sample weights likely flatter the suggested allocation. *Fix applied:* §5 non-goal states the test is in-sample; §1 wording is now "did today's suggested allocation beat an equal split over that period."
- **[Decision-readiness]** Point-in-time trade-off not named (§5, §6.2) — The MVP cannot show whether the scoring method added value over time. *Fix applied:* §6.2 states this explicitly.
- **[Decision-readiness]** History floor may make UJ-1 infeasible (§3, FR-1, UJ-1, OQ-1) — No minimum or fallback. *Fix applied:* FR-1 disables the run below 12 months of history, indexed as an assumption.
- **[Done-ness clarity]** Holdings valuation undefined in gap months (FR-4, §3) — *Fix applied:* FR-4 carries the last known NAV forward; the rule is indexed.
- **[Done-ness clarity]** Baseline gap behaviour unspecified (FR-3 vs FR-4) — *Fix applied:* FR-3 uses the same redistribution rule as FR-4.
- **[Done-ness clarity]** Backfill mechanics unstated, no failure state (FR-7, §6.1) — *Fix applied:* FR-7 names a manual `workflow_dispatch` backfill, a floor-reached record, and a visible failure state.

### Medium (4)
- **[Substance over theater]** No performance or payload bound (§4.1 NFRs, OQ-2) — *Fix applied:* working targets of 5 MB and 2 seconds, indexed as assumptions; OQ-2 stays open until measured.
- **[Strategic coherence]** SM-1 is a self-report (§7) — *Fix applied:* SM-2 added as a fixture-based check.
- **[Done-ness clarity]** Core arithmetic tested only by a flat-NAV case (FR-2) — *Fix applied:* FR-2 has a 50/50 fixture with a final value of ₪105.
- **[Scope honesty]** "Gross of fees" label promised but not required (§6.2, FR-5) — *Fix applied:* FR-5 requires the label.

### Low (9)
- **[Substance over theater]** SM-C1 is a principle, not a measurable counter-metric — *Fix applied:* restated as a process rule.
- **[Decision-readiness]** OQ-1 conflates floor and source depth — *Fix applied:* OQ-1 asks how far back the source returns NAV.
- **[Done-ness clarity]** FR-4 consequence is not a checkable bound — *Fix applied:* replaced with a fixture.
- **[Done-ness clarity]** Presentational terms undefined (FR-4 marker, FR-5 line styles) — *Fix applied:* shaded band with tooltip; solid and dashed lines.
- **[Done-ness clarity]** Partial current month undefined (§3, FR-2) — *Fix applied:* range ends at the last complete calendar month, indexed as an assumption.
- **[Scope honesty]** Point-in-time framed twice (§5, §6.2) — *Fix applied:* §5 points to §6.2.
- **[Scope honesty]** Brief fidelity: start date narrowed to start month — *Fix applied:* recorded as a memlog decision.
- **[Downstream usability]** Glossary drift for lines and weights — *Fix applied:* "Suggested allocation" and "Equal-weight baseline" defined and used consistently.
- **[Downstream usability]** Hard-coded fund count "7" — *Fix applied:* "every fund in `data/funds.json`" everywhere except §1's description of today's set.

## Mechanical notes
- The memlog said fee modelling was "deferred to v2"; the PRD says only "Deferred." Corrected in the memlog.
- FR-6 and FR-7 carried no "Realizes UJ-1" line; §4.2 now states they enable UJ-1.
- Assumptions Index now lists every inline `[ASSUMPTION]`, including the new ones.

## Reviewer files
- `review-rubric.md` — the full rubric review this report summarizes

## Not generated
- The HTML report from the template was not produced. This markdown twin is the canonical record.
