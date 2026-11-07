# Exercise 7: StockBrowser · click a fund, see its record

**Goal:** The StockBrowser pane beside the chat shows what each row holds, not only its score.

## What the exercise asks
From the syllabus (Level 5 homework, exercise 7; slide 60, "What a mod is"). The syllabus example is a file viewer; here the rows are funds from `data/funds.json`.
- Make every row pressable. Selecting one shows its preview in the pane: the source, the size, and the content highlighted for its language with line numbers.
- Handle three things that break a naive viewer: a binary one, a huge one and one that can't be read. Each shows one calm line saying why, never an error.
- **Done when:** a selected row shows its content highlighted with line numbers and is marked in the list; the three breaking cases each show one calm line; a selection outside the file is refused.

## How the syllabus maps to StockBrowser
| Syllabus (file viewer) | StockBrowser |
| --- | --- |
| a file in the tree | a fund in the ranking |
| its content, highlighted | its record in `data/funds.json`, JSON, with a line gutter |
| binary file | a record holding control characters |
| huge file, over the cap | a record over 4096 bytes: its first 30 lines, and how many are left |
| unreadable file | `data/funds.json` can't be read or parsed: one line saying why |
| path outside the project | an id that isn't a fund in the file: refused |

## What I built
```
mods/stock-browser/
├── .claude-plugin/plugin.json   ← manifest, names the types contract
├── hooks/hooks.json             ← modules: ./register.tsx
├── hooks/register.tsx           ← /stock-browser, the Pane render hook, the preview
├── hooks/stock-browser.test.tsx ← the four cases above
└── types/index.d.ts             ← the $.state contract: selectedFund
```
- **Press selects.** A row is a `Button` keyed by its id. A press stores that id in `selectedFund`, and the write redraws the pane. The selected row shows `●` instead of `▸`.
- **Preview.** The selected record is `JSON.stringify` of the fund as stored in the file, shown in a `Code` element with `language="json"` and `startLine={1}`, so the gutter numbers the lines. The header shows the fund's name, the file path and the record's size in bytes.
- **Binary.** `JSON.stringify` writes a control character as an escape such as `\u0001`. A record with one of those escapes gets a calm line and no `Code` element.
- **Huge.** A record over 4096 bytes shows its first 30 lines and says how many more are left.
- **Unreadable.** The file can't be read or parsed: one line says why, as in exercise 6.
- **Refused.** A selected id that isn't a fund in the file shows one line saying so, and nothing is drawn.
- **Names.** A control character in a fund's name breaks the pane's validation, which skips the whole pane. Names are shown with control characters replaced by `�`. The test caught this.
- **State.** The selected id is in `$.state` and declared in `types/index.d.ts`, so it survives a reload.
- **Changes from exercise 6.** A press selects a fund instead of toggling its figures, which now appear in the record preview. The list is no longer cut to the viewport, since the data has seven funds.

## Checks
- [x] `claude plugin validate ./mods/stock-browser` passes. The only remaining message is the plugin-directory submission check (license and icon), which applies only when publishing.
- [x] `tsc` on the module against the bundled API types passes, with no errors.
- [x] `claude plugin test ./mods/stock-browser` passes (4 tests): the selected row and its JSON preview, the binary line, the huge record, and the unreadable file.
- [ ] **Not checked by a test:** the refusal line. The test kit doesn't expose `$.state.set`, so the test can't select an unknown id. The branch is in the code, but it has no test.
- [x] **Live:** run `claude --plugin-dir ./mods/stock-browser`, then `/stock-browser`, and press a row. The gutter line numbers and the highlighting were checked in the terminal and look right.

## Status
Code, tests and the live gutter and highlighting check pass. The refusal branch has no test yet.
