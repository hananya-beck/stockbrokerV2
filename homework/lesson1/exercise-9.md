# Exercise 9: a nested CLAUDE.md

`src/lib/CLAUDE.md` holds conventions that only matter inside the pure core: deterministic functions (no `fetch`, DOM, timers or `Date.now()`), named exports, JSDoc on every export, `'—'` for unknown numbers, values as fractions, and one test file per module. The root `CLAUDE.md` now just points to it, so other work doesn't pay for those lines.

It's layer 4 of slide 18: loaded on demand when Claude reads a file in `src/lib/`, not at launch. After `/compact` it drops out until a file there is read again.

## Proof
Two fresh headless sessions (`claude -p`, plan mode), each asked to quote a rule that exists only in `src/lib/CLAUDE.md`.

**1. No file read: not loaded**

> **Prompt:** Without using any tools or reading any files, list every CLAUDE.md currently in your context by path, and quote the rule about how unknown numbers render in src/lib if you have one.
>
> **Claude:** It lists `~\.claude\CLAUDE.md` and `stockbroker\CLAUDE.md` only. "The rule about unknown numbers in `src/lib`: I don't have it. `src/lib/CLAUDE.md` exists… but its contents aren't loaded. Subdirectory CLAUDE.md files load only when I read files in that directory."

**2. After reading `src/lib/refresh.js`: loaded**

> **Prompt:** Read src/lib/refresh.js. Then, without reading any other file, list every CLAUDE.md that is currently in your context, and quote the rule about how unknown numbers render.
>
> **Claude:** "`…\stockbroker\src\lib\CLAUDE.md`: the subdirectory file. It wasn't there at the start and was loaded only because I read `refresh.js` inside `src/lib/`." It then quotes: "Unknown or missing numbers (`null`, `undefined`, `NaN`) render as `'—'` with `sign: null`. They never throw or render `NaN`."

## Checking it interactively
1. Start a fresh session and run `/context`. Memory files lists the two CLAUDE.md files, `RTK.md`, `static-deploy.md` and `MEMORY.md`, but not `src/lib/CLAUDE.md`.
2. Ask "what does src/lib/refresh.js do?". After the read, the terminal shows a one-line `Loaded src/lib/CLAUDE.md` notice.
3. Run `/context` again. `src/lib/CLAUDE.md` is now listed.
