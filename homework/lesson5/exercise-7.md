# Exercise 7: Something Claude remembers — MEMORY.md

**Goal:** Teach Claude a project fact once — and have the next session know it.

## The fact
This repo's checked-out files are CRLF (Windows). Two gotchas already hit while building
this harness:
1. A committed `.sh` file loses its shebang on the next checkout if `core.autocrlf=true`
   and nothing forces it back to LF (exercise 3 — fixed with `.gitattributes`:
   `*.sh text eol=lf`).
2. A `$`-anchored line-comment regex (`/\/\/.*$/`) silently never matches on CRLF files,
   because `.` doesn't match `\r` (exercise 5 — fixed by dropping the anchor).

Neither is guessable from the code alone; both only show up against this repo's actual
checkout. That's exactly the kind of fact auto-memory is for.

## Where it went
`~/.claude/projects/C--Users-Hananya-projects-stockbrokerV2/memory/`:
- `crlf-line-endings.md` — the fact, with frontmatter (`type: project`), both failure
  modes, the fix for each, and a "how to apply" line.
- `MEMORY.md` — one-line index entry pointing at it.

I checked the project's memory folder before writing to confirm it existed (created by
an earlier session) but was empty — this is the first entry in it.

## Proof: a fresh session acted on it without being told
Gave a disposable session (`claude -p`, rooted in the repo) a task that would organically
re-create exercise 5's exact bug class — **without mentioning CRLF, memory, or the hook
script at all**: write a one-off Node script that scans `src/lib/*.js` for lines over 100
characters, ignoring `//` comments.

First two attempts got blocked by my own exercise-3/4 guard hooks (writing under
`.claude/` and writing to `/tmp` outside the project) — a side effect I hadn't planned
for, but it at least confirms those hooks are still live. Third attempt, writing the
script to the repo root, succeeded. Before running it, the session's own description of
what it had written was:

> It splits lines on `\r?\n`, so the repo's CRLF checkouts don't add a stray character.
> It strips everything from the first `//` to the end of each line...

That's the memory's fact, applied, unprompted — and applied via a different (also
correct) fix than the memory's literal suggestion: it normalized the line split
(`.split(/\r?\n/)`) up front instead of dropping the `$` anchor, which sidesteps the same
bug just as well. That's a sign it understood *why* the gotcha exists, not that it
pattern-matched the memory text.

Ran the script, got real results (`src/lib/i18n.js` and `src/lib/refresh.js` both have
genuine >100-char lines — pre-existing, left as-is since that's out of scope here), then
deleted the scratch script as asked. `git status` afterward: only the usual CRLF-warning
non-diff on `refresh.js` (confirmed with `git diff --ignore-space-at-eol`: no real
content change), nothing else untracked.

## How much of MEMORY.md loads at session start
Per the syllabus: the first 200 lines / 25 KB of a project's `MEMORY.md` auto-load every
session (same budget as the `CLAUDE.md` constitution). Right now the index is one line,
nowhere near the cap — worth keeping it that way: entries should stay index-only, with
detail living in the linked file per entry, not inlined into `MEMORY.md` itself.

## Done when ✅
- [x] The entry is in the project's `MEMORY.md`, under
      `~/.claude/projects/<project>/memory/`.
- [x] A fresh session acted on it without being told (the CRLF-safe scan script above).
- [x] Know the load budget: first 200 lines / 25 KB of `MEMORY.md` at session start.
