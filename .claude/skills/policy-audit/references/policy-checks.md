# Policy checks: what each one means and how to fix it

The rules come from `AGENTS.md` ("Policy" and "Conventions") and `src/lib/CLAUDE.md`. `scripts/audit.mjs` checks P1–P6 mechanically. M1–M3 need judgement, so read them yourself.

| ID | Rule | Why | Typical fix |
|----|------|-----|-------------|
| P1 | No `localStorage`, `sessionStorage`, IndexedDB or cookies in `index.html` / `src/` | A stored GitHub token would outlive the tab on a public page | Keep the value in a JS variable. Keep the language choice in `?lang=` |
| P2 | No leading `/` in `src=`, `href=`, `import` or `fetch()` paths | The site lives under `/stockbrokerV2/`, so `/x` 404s on Pages | `data/funds.json`, not `/data/funds.json` |
| P3 | `src/lib/*.js` has no `fetch`, DOM, `window`, timers, `Date.now()` or `Math.random` | The core must be deterministic under `node --test` | Move the call into `index.html` and pass the result in as a parameter |
| P4 | No hex, `rgb()` or `hsl()` color outside `src/styles/tokens.css` | Colors come from tokens | Add or reuse a `--token` and write `var(--token)` |
| P5 | No `ghp_…` or `github_pat_…` strings anywhere | The repo is public | Remove it, **rotate the token**, and tell the user |
| P6 | `STRINGS.he` and `STRINGS.en` have the same keys | English is a supported second language | Add the missing key to the other language |
| M1 | No new UI text hard-coded in `index.html` | i18n | Move it to `src/lib/i18n.js` in both languages |
| M2 | Every failure is shown (status text, plus `alert` for 401) | Never fail silently | Look at every new `catch`. It must update status text |
| M3 | `data/funds.json` not hand-edited in the change | The daily bot overwrites it | `git log -1 -- data/funds.json` should be the bot's "Update fund data" |

## Known false positives
- Comments that *name* a banned API ("No fetch, no DOM") are skipped by the script. A code line that only mentions one in a string still counts, so read the hit before "fixing" it.
- `//cdn…` protocol-relative URLs are not leading-slash paths, and P2 ignores them.
- `#` anchors such as `href="#top"` don't match P4, which needs 3–8 hex digits on a color-like token.
