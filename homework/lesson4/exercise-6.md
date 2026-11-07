# Exercise 6: StockBrowser · the ranking in a pane

**Goal:** The first code that runs inside Claude Code and draws: a pane beside the chat that shows the fund ranking from StockBrowser.

## What the exercise asks
From the syllabus (Level 5 homework, exercise 6; slide 60, "What a mod is"). The syllabus example is a file tree; in this repo the mod shows StockBrowser's funds instead.
- Start a mod in `mods/`: a slash command that opens a pane, and the pane shows the data, with each row open and closed on a press.
- **Done when:** the command opens a pane beside the chat; the rows match the data; a row opens and closes on a press; saving a change to the module redraws the open session without a restart.

## What I built
```
mods/stock-browser/
├── .claude-plugin/plugin.json   ← manifest, names the types contract
├── hooks/hooks.json             ← modules: ./register.tsx
├── hooks/register.tsx           ← session.start, /stock-browser, the Pane render hook
├── hooks/stock-browser.test.tsx ← ranking, stale marker, press, and an unreadable file
└── types/index.d.ts             ← the $.state contract: openFunds
```
- **Command.** `/stock-browser` registers in `session.start` and opens a pane titled `StockBrowser`.
- **Ranking.** The pane reads `data/funds.json` with `$.fs.read` and sorts the funds by `risk_adjusted_score`, highest first, as the dashboard does.
- **Press.** Each fund is a `Button` keyed by its id, labelled with its score and English name. A press toggles that fund in `openFunds`, and the write redraws the pane. An open fund shows its returns (1m, 3m, 1y, 3y), volatility, suggested weight, last price date and Hebrew name.
- **Stale.** A fund the data marks `stale` gets a `(stale)` suffix on its label.
- **Errors.** If the file can't be read or parsed, the pane shows one line that says why, instead of an empty pane.
- **State.** The open funds are in `$.state`, declared in `types/index.d.ts`, so they survive a reload.
- **Read-only.** The mod only calls `$.fs.read`. It never writes, runs a program or touches the network.
- **Room.** The pane shows as many rows as the viewport fits and says how many are left. It doesn't scroll yet.

## Checks
- [x] `claude plugin validate ./mods/stock-browser` passes. The only remaining message is the plugin-directory submission check (license and icon), which applies only when publishing.
- [x] `tsc` on the module against the bundled API types passes, with no errors.
- [x] `claude plugin test ./mods/stock-browser` passes (2 tests). The tests stub `fs.read` with a two-fund fixture, so they check the ranking, the stale marker, the press and the error line, not the real file.
- [x] `data/funds.json` has every field the mod reads, for all 7 funds.
- [x] Live check in a terminal, `claude --plugin-dir ./mods/stock-browser`: `/stock-browser` opens the pane beside the chat, the ranking shows the real data, and a save redraws the open session.

## Notes
- **Where the mod lives.** The plugin-authoring skill writes new mods to a folder outside the repo and asks the person to turn on hot reload. This exercise keeps the mod in `mods/stock-browser/` and loads it with `--plugin-dir`, as the exercise's setup says, so the hot-reload question doesn't apply.
- **Data source.** The mod reads the committed `data/funds.json`, which the daily bot refreshes. It doesn't recompute scores, so the pane matches the dashboard's ranking.

## Status
Code, tests and the live check pass.
