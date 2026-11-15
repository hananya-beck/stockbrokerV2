# Exercise 11: A run with a price cap

**Goal:** Cost becomes one more signal you can see — and one more limit you can set.

## The script: `scripts/cost-capped-audit.mjs`
Runs a headless `claude -p` audit with four rails:
- **Read-only tool surface:** `--tools Read,Grep,Glob --disallowedTools Edit Write NotebookEdit Bash`
  (belt and braces — the allowlist alone is enough, the denylist is redundant on purpose).
- **Turn limit:** `--max-turns N`.
- **Dollar cap:** `--max-budget-usd D`.
- **Machine-readable output:** `--output-format json`, parsed for `total_cost_usd`, `num_turns`,
  `terminal_reason`, `is_error`, `result`.

It also proves the "couldn't have edited a file" claim instead of just asserting it: `git status
--porcelain` is snapshotted before and after the subprocess runs, and the script fails loudly
(exit 1) if they ever differ — flag misconfiguration, not just intent, is what's actually being
checked.

## What running it for real turned up
- **The hint about a half-dollar first turn is real, and it's worse than that.** A cold
  `claude -p "pong"` in this repo (big `.claude/` layer: hooks, skills, two plugins) cost
  **$0.52** the first time and **$1.52** the second — before producing any text — because
  `--max-budget-usd` is checked between API calls, not mid-call, so the run can overshoot the
  cap by the cost of whatever call was already in flight. A later identical call cost **$0.065**
  once the system prompt was warm in the 1-hour prompt cache. Same prompt, 23x cost spread,
  purely from cache state — this is the actual lesson behind slide 78, not a one-time footnote.
- **`claude` exits non-zero when a rail is hit** (`max-turns`, `max-budget-usd`) even though
  stdout is still a complete, valid result JSON. `execFileSync` throws on that exit code by
  default — the script's first real run crashed on exactly this, caught in `runAudit`'s
  try/catch now (`err.stdout` still has the JSON).
- **`--max-turns` is real but not linear.** `--help` doesn't even list it in this installed
  build (2.1.325) — found it only by trying it. Set to `1` on a 4-file-read task, it capped the
  run cleanly (`num_turns: 2`, `terminal_reason: "max_turns"`). Set to `2` on the same task, the
  run finished in 5 turns with `terminal_reason: "completed"` — no error at all. It isn't a hard
  linear ceiling on tool-call count; treat it as a coarse circuit breaker, and rely on
  `--max-budget-usd` as the rail that actually binds.
- **The real audit ran clean.** `--max-turns 15 --max-budget-usd 3.0`, prompt: *"Audit this repo
  against AGENTS.md…"* → `cost_usd: 0.27`, `turns: 16`, `terminal_reason: "completed"`,
  `tree_unchanged: true`. It found two real, previously-unflagged issues (a `localStorage` call
  inside a bundled BMAD skill asset, and `@modelcontextprotocol/sdk`/`zod` sitting under
  `dependencies` instead of `devDependencies` despite the dashboard never loading them at
  runtime) and correctly said it *couldn't* check force-push history or `data/funds.json` edits
  because Bash wasn't available to it — it didn't guess.

## The status line: `.claude/statusline.mjs` + `settings.json`
Reads the stdin JSON Claude Code pipes on each render and prints
`<dir> · <model> · $<cost> · ctx <pct>%`. Can't be driven through a headless `-p` session (the
status line is a TUI-only feature), so it was self-tested instead against a synthetic stdin
built from the documented field shape (`cost.total_cost_usd`, `model.display_name`,
`workspace.current_dir`, `context_window.used_percentage`) — renders correctly on the full
shape, degrades to `· model? · $?` on an empty object, and never crashes on `JSON.parse`
failure (`{}` → safe fallback, plain garbage → `"statusline: unreadable input"`, exit 0 either
way, matching exercise 7's "never block, correct even on broken input" standard).

## Two effort levels, same task
Same prompt (*"Audit `src/lib/csv.js` and `index.html`'s export wiring for correctness bugs"*),
same model, only `--effort` changed:

| | low | high |
|---|---|---|
| cost | $0.267 | $0.414 (1.55x) |
| turns | 9 | 14 |
| findings | 2 (Blob-revoke timing, a truncated variable name) | 5, ranked worst-first, plus named test gaps and a concrete next step |

**Which I'd keep: high, for this kind of task.** The 1.55x cost bought a genuinely deeper
review — it caught a missing-`NaN` handling gap inherited from `formatting.js` and a BOM
fragility issue the low-effort run didn't look for at all, not just more words about the same
two things.

**But it also wasn't free of error, which is the actual finding here.** High effort's top risk
claimed fund names "come from the bizportal scrape, which is untrusted" — directly contradicting
what exercise 10 established (and what I re-verified just now: `scripts/fetch_data.py` never
writes `name_he`/`name_en` at all; `data/funds.json`'s names are carried through unchanged from
the maintainer-committed `data/funds_config.json`). A deeper review is not a more trustworthy
one by default — the extra reasoning surfaced a real, correctly-prioritized new finding (test
gaps) in the same breath as a wrong provenance claim about an existing one. Effort level buys
you more to check, not less need to check it.

## Done when ✅
- [x] The script prints the run's cost, turn count and result; `tree_unchanged` is checked, not
      assumed, and the run that mattered (`max-turns 15 / max-budget-usd 3.0`) came back
      `true`.
- [x] `.claude/statusline.mjs` is wired into `settings.json`'s `statusLine` key and renders the
      live session cost (self-tested against the documented stdin shape; rendering in the real
      TUI is left for interactive use, since headless mode can't drive it).
- [x] Compared one task at two effort levels; wrote down which to keep and why, including the
      caught error in the "better" run.
