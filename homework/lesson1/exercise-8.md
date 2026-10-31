# Exercise 8: a CLAUDE.md that gets followed

`CLAUDE.md` at the repo root has five sections in slide 17's order: **Forbidden → Conventions → Stack → Commands → Open questions**. Every Forbidden line gives its reason.

## Where the content came from
- **Project rules (section B / `.claude/rules/static-deploy.md`):** no build step, relative paths, no browser storage, no secrets, don't hand-edit `funds.json`.
- **Exercise 4 (refresh button):** `src/lib/` stays pure (no `fetch` or DOM), and the token is typed in at runtime and kept in memory.
- **Exercise 4 follow-up (commit `de90798`):** a 401 error was only shown inline, so the convention is "show every failure, alert on auth errors".
- **Exercise 7:** the bot commits to `main`, so never force-push.
- **Exercises 2–3:** Hebrew RTL wording and `tokens.css` colors.

## Proof: a fresh session follows a rule without being told
Run headless with `claude -p` in plan mode. The prompt never mentions purity, paths or error handling:

> **Prompt:** I want a helper that downloads data/funds.json and returns the parsed funds array. Where should this code go and why? Answer in 3 sentences, don't edit any files.
>
> **Claude:** The fetch itself belongs in `index.html`, because the project rules forbid `fetch` and browser APIs in `src/lib/`, which is kept as the pure, unit-tested core. Any parsing or checking of the downloaded JSON can go in `src/lib/` as a pure function that takes the already-parsed object and returns the funds array, with JSDoc types and a test in `tests/js/`. Request the file with the relative path `data/funds.json` (no leading `/`, since the site is served under `/stockbroker/`), and show any failure as status text next to the control rather than failing silently.

It applied three CLAUDE.md lines unprompted: the Forbidden `src/lib/` rule, the testing convention, and the "never fail silently" convention.
