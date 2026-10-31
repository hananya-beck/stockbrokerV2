# Exercise 11: Hand the big read to a subagent

## The job
The course's example reviews a file-explorer folder against its project rules. Here I adapted that: **audit the whole repo against the rules in `CLAUDE.md`** (pure `src/lib/`, no build step, relative paths, no browser storage, no secrets, colors only from `tokens.css`, Hebrew UI with visible errors, stdlib-only Python). That means about 32 tracked files and 119 KB of source (about 30k tokens), all of which would otherwise be read into the main window.

**Prompt (sent to the built-in `Explore` subagent):** "Read-only audit of the repo (skip `data/funds.json` and `node_modules`). Check every tracked source file against these 8 rules. Report ONLY a compact summary (about 25 lines max): PASS or VIOLATION per rule, with file:line and a one-line note. Don't paste file contents."

## What came back (the summary only)
- Rules 1–6 and 8: **PASS**. `src/lib/` is pure, there are only devDependencies, paths are relative, the token lives only in a variable, there are no secrets, all 16 color literals are in `tokens.css`, and Python imports only the standard library.
- Rule 7 (Hebrew UI and visible errors): **2 minor issues**
  - `index.html:139`: the token dialog label is mostly English.
  - `index.html:213`: `load()` doesn't check `res.ok`, so a 404 shows up as a JSON parse error instead of a clear message. It's still shown to the user, though.
- The subagent was honest about coverage. It read `index.html`, `refresh.js` and `fetch_data.py` in full and only grepped the rest (tokens, tests, workflow, configs) for each rule's patterns.

## Cost to the main window
The transcript shows one `Agent` (general-purpose) call. What came back was the findings table and a list of the rules that passed, with no file contents. Measured with `/context` before and after the call:

| | Messages tokens |
|---|---|
| Before the subagent | 10 |
| After the subagent | 47.2k |

According to the harness, the subagent used **57,694 tokens** over 4 tool calls in 47 s, all in its own window. Most of the 47.2k in the main window isn't the audit. It's the first `/context` output pasted into the conversation (a table of about 475 MCP tools, which re-enters the context on every turn). The report itself was about 1k tokens, much smaller than the source the subagent read.

## The fixes that followed
- `load()` now checks `res.ok`. A failed load shows its message in the status line next to the refresh button, and in the table row as text (`textContent`, not `innerHTML`).
- Cancelling the token dialog now shows "הרענון בוטל: לא הוזן טוקן" instead of doing nothing.
- The fallback poll's query and timeout check moved into pure helpers in `src/lib/refresh.js` (`dispatchedRunsQuery`, `isPastDeadline`), with 2 new tests (31 total).
- Fund names and ids are HTML-escaped before they go into the table.

## When a subagent would be a waste
For a single-fact lookup in a file I already know, like "what's `MIN_WEIGHT` in `fetch_data.py`?", one `grep` costs a few tokens. A subagent costs a cold start, re-explains the task and returns a summary that's longer than the answer.
