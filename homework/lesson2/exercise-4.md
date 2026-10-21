# Exercise 4 — Brownfield: project context first

> Slides 37 · 39. Ran BMAD's **project-context** workflow (`bmad-project-context`,
> intent `adopt`, since `CLAUDE.md` already had real content and no managed block)
> on this repo, which already had code, a `CLAUDE.md`, two `.claude/rules/*.md`
> files and a `src/lib/CLAUDE.md` from Levels 1–3.

## What the adoption found

- `.claude/rules/static-deploy.md` had no path frontmatter, so Claude Code loaded
  it unconditionally — and it duplicated five of `CLAUDE.md`'s six "Forbidden"
  rules almost verbatim, plus its own copy of the `npm run check` line. Same
  policy, paid twice every session.
- Verified-stale claim, caught mid-adoption: both `README.md` and
  `static-deploy.md` said the live site was
  `https://hananya-beck.github.io/stockbroker/`. The Pages endpoint actually
  enabled for this repo (confirmed via `gh api .../pages` earlier this session)
  is `https://hananya-beck.github.io/stockbrokerV2/`.
- Verified-stale convention: `CLAUDE.md` said homework write-ups go in
  `homework/exercise-N.md`. Actual layout: exercises 5–12 are flat, but
  starting lesson 2 they moved under `homework/lessonN/exercise-M.md` — this
  file included.
- `CLAUDE.md`'s "Stack" section (front-end/data/hosting narrative) was a
  directory-tree-style overview — excluded by the skill's own rules ("derived
  fresh, more accurately; stored copies rot"), except for one non-obvious fact
  (the data-refresh cron schedule + `workflow_dispatch` trigger), which moved
  into "Where things are" instead of being dropped with the rest.
- `src/lib/CLAUDE.md` and `.claude/rules/fetch-script.md` were both already
  substantial, subtree-scoped, and verified — kept as-is, untouched.

## What changed

- New `AGENTS.md` holds the verified `<!-- bmad:context -->` block: Orientation,
  Policy, Where things are, Running and verifying, Conventions, Known pitfalls.
- `CLAUDE.md` shrank to a single `@AGENTS.md` import — the same mechanism this
  session's own global `CLAUDE.md` already uses for `@RTK.md`, so it's verified
  working in this harness. No instruction loads twice.
- `.claude/rules/static-deploy.md` deleted — fully absorbed as duplicates into
  the `AGENTS.md` Policy section.
- `README.md`'s live-site URL corrected to `stockbrokerV2`.
- One instruction has **no prior source**: a `Known pitfalls` line about a
  `<td>` child sized only by `min-width` collapsing to that min-width under
  `table-layout: auto`. That's a real bug from this same session — the
  weight-bar fill looked identical across rows at every allocation percentage
  until `width: 100%` was added alongside the existing `min-width`.

## Done-when, checked

- `AGENTS.md` holds the verified project-context block — committed.
- Every rule from `CLAUDE.md` and `.claude/rules/static-deploy.md` is accounted
  for in the ledger: retained (often merged), relocated to `src/lib/CLAUDE.md`'s
  existing coverage, or deleted only because it survived elsewhere or because it
  was outside what the skill admits (stack overview, an obviously-guessable
  command) — and those two deletions were asked for explicitly, not assumed.
- No instruction loads twice: `CLAUDE.md` is now an import, not a second copy.
