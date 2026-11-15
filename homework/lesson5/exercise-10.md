# Exercise 10: Both reviews, before a human

**Goal:** By the time a person reads the diff, only judgment calls are left.

## Running both, on the same diff — and where that broke down
`/code-review medium 588a473` scoped cleanly to exactly exercise 8's commit. `/security-review`
has no commit-target argument (confirmed: passing `588a473` as an argument to it didn't
change anything) — by its own design it always reviews "the pending changes on the current
branch," i.e. the whole `feat/level-6` diff against `main` (45 files, exercises 1–9). I
couldn't force identical scope, so rather than paper over it: the two reviews below are
compared on the part that's actually comparable — `src/lib/csv.js` and the export wiring in
`index.html`, which both reviews covered — and security-review's extra findings about
exercises 3/4's hooks are called out separately as out-of-scope-but-real.

## What each one found, on the CSV-export feature itself
- **`/code-review` caught something `/security-review` didn't:** `index.html`'s
  `applyStaticText()` looks up the export button by `document.getElementById('exportButton')`
  to set its label, but the button's actual `id` was `exportBtn` — a plain typo-class bug
  that security review's threat model ("what if hostile input arrives?") has no reason to
  catch, since it's not a vulnerability, just silent breakage. The button was clickable and
  the download worked; it just never got a visible label, in either language, and none of
  `csv.test.js`'s pure-function tests render the DOM so it slipped through `npm run check`.
- **`/security-review` flagged something, at low confidence, that `/code-review` didn't look
  for:** `escapeCsvField` doesn't neutralize a leading `=`, `+`, `-` or `@`, the classic
  spreadsheet-formula-injection vector. Confidence 2/10 — not code-review's job to weigh risk
  this way, since it's about correctness, not "what if the input were hostile."
- **They agreed, implicitly, on everything else in that feature:** neither flagged the `Blob`
  download, the object-URL handling, or the UTF-8 BOM — because none of it introduces a new
  sink for untrusted data (the only free-text cells come from the maintainer-committed
  `data/funds_config.json`, not the bizportal scrape) and none of it is a correctness bug.

## Top three findings, and what I decided
1. **`exportBtn`/`exportButton` id mismatch (`code-review`) — real bug.** Fixed: renamed the
   HTML element's id to `exportButton` to match the existing simple-loop convention every
   other UI string uses, instead of adding a `refreshBtn`-style special case. `npm run check`
   stayed green (58/58) after the fix.
2. **CSV formula-injection hardening gap (`security-review`, confidence 2/10) — won't fix now.**
   Blanket-escaping a leading `-` would corrupt every negative return/volatility cell the
   export writes (e.g. `-1.0%`), which are legitimate, common values, not edge cases — the
   fix would trade a real, constant breakage for a theoretical one that needs the fund config
   itself to become untrusted input first. Documented as an accepted risk in `src/lib/csv.js`'s
   own reasoning (and matches what the exercise-8 feature's own build session already flagged
   unprompted); revisit only if fund names/ids ever stop being maintainer-committed.
3. **Guard-bash bypasses (`security-review`, out of scope for exercise 8, but real) — fixed
   anyway.** `rm -r -f` (flags as separate tokens) and `git push origin +main` (force via a
   `+` refspec, no `--force` flag at all) both slipped past `guard-bash.sh`'s existing
   patterns — these are exercise-3 hooks, not part of this feature's diff, but a review
   surfacing a real hole in a `CONTRACT.md` "never" row is worth closing regardless of which
   exercise it was found under. Tightened both regexes (see below), re-tested the full
   existing fixture/edge-case suite plus the two new bypasses, re-verified live in a disposable
   session — both now blocked, with no regressions on the legitimate commands that must still
   pass (`rm -r src`, `rm -f single-file.js`, `git push origin main`, etc.).

## The guard-bash fix
Two new alternatives added to each check (plus the existing combined-flag and `--long-flag`
patterns, unchanged):
```bash
|| [[ "$cmd" =~ rm.*[[:space:]]-[rR].*[[:space:]]-f([[:space:]]|$) ]] \
|| [[ "$cmd" =~ rm.*[[:space:]]-f.*[[:space:]]-[rR]([[:space:]]|$) ]]
```
```bash
[[:space:]]\+[^[:space:]]     # added to the force-push alternation
```
Hit a real regex gotcha building the `rm` fix: an earlier attempt required a space
boundary on *both* sides of the `-r`/`-f` tokens, which silently never matched
`rm -r -f x` — the single space between the two flags can't serve as both the first
token's trailing boundary and the second token's leading boundary in one pass. Dropping
the boundary requirement on the middle token (only the outermost one needs to be
anchored) fixed it; verified by tracing the regex against the literal string before
believing the test output.

## Done when ✅
- [x] Both ran against the same feature (with the scope mismatch above stated plainly,
      not hidden); named one thing each caught that the other didn't, and where they agreed.
- [x] Top three findings and decisions are here and in the commit message.
- [x] `npm run check` green (58/58) and `stockbroker-tools:policy-audit` all PASS after
      every fix.
