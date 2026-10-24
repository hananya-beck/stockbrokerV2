# Adversarial review: Backtest simulator spine

Reviewed: `ARCHITECTURE-SPINE.md` (AD-1 to AD-7) against `prd.md` (FR-1 to FR-7), `scripts/fetch_data.py`, `.github/workflows/update-data.yml`, `index.html` (fetch and date use), `data/funds_config.json`, `data/funds.json`, `.claude/skills/add-fund/SKILL.md`, `.claude/rules/fetch-script.md`.

Verdict: the spine governs the happy path only. Several holes sit in existing code (the all-fail path, the silent drop of a fund, the date format), and several more sit in definitions the spine never owns (merge, floor and range end, cash fate, clock). AD-3 is already breached by the add-fund skill.

Each entry gives two unit behaviours that both obey the cited ADs, the incompatibility, and proposed AD text.

---

## H1. Successful-run merge is undefined (FR-6 vs AD-2 and AD-4)

- **Unit A (replace):** the producer writes the series the source returned this run, as is. This is what `fetch_fund_series` already does.
- **Unit B (merge):** the producer unions the previous stored series with the new one by date, so no date is ever removed.
- **ADs obeyed:** AD-2 (sorted, absent points, ISO) and AD-4 (writes replace the whole file). AD-4 covers failure only, so neither unit breaks it.
- **Incompatibility:** bizportal returns a rolling window (the spine's Deferred section says retention is "set by bizportal"). Under A, days that fall out of the window disappear, which breaks the PRD's testable consequence "a later run does not drop days from an earlier run" (FR-6). Under B, a revised close for the same date has no rule for which value wins. The Deferred line contradicts FR-6 as written.
- **Proposed AD-2 addition:** "A successful fetch merges into the stored series by date. A date is never removed by a successful run. When the source returns a different close for a date already stored, the source value wins. Only `scripts/fetch_data.py` merges." Also delete "Retention beyond the source window: set by bizportal" from Deferred, since FR-6 requires retention.

## H2. Existing code contradicts AD-4 on the all-fail path

- **Unit A (current `main()`):** if every fetch fails but `data/funds.json` already exists, `previous` is non-empty. Every fund is appended with `stale: True`, so `if not funds` is false. The run rewrites `funds.json` with a new `generated_at`, exits 0, and the bot commits it.
- **Unit B (AD-4 and `.claude/rules/fetch-script.md`):** "If every fund fails, both files are left untouched and the run exits non-zero."
- **ADs obeyed:** AD-4 binds Unit B. Unit A is the existing producer, which the spine says already "follows the same rule".
- **Incompatibility:** the spine's premise is false. Under the current code, a total outage produces a green run and a rewritten file, and nav-history would follow the same path.
- **Proposed AD-4 text:** "The producer counts successful fetches before any write. If zero funds fetched successfully, it writes nothing to either file and exits 1, whether or not previous data exists. Fix the existing check in `main()` (`if not funds` becomes `if not any fresh fetch`) in the same change."

## H3. A fund that fails with no previous data vanishes silently, and the fund set has three owners

- **Unit A (current code):** a configured fund whose fetch fails and that has no entry in the previous `funds.json` is simply not appended. It has no `stale` marker, the run exits 0, and only stderr shows it. Weights are then redistributed across the remaining funds.
- **Unit B (AD-4 as written):** "a fund whose fetch fails keeps its previous points and is marked stale."
- **ADs obeyed:** AD-4 for B. For A, AD-4 says nothing about a fund with no previous data, so A also obeys it.
- **Incompatibility:** the fund set is owned three ways. `funds_config.json` (edited by the add-fund skill), the keys of `funds.json`, and the keys of `nav-history.json`. A new fund that fails on day one is in none of the outputs, so the baseline ("every fund in `data/funds.json`") silently covers six funds. This also breaks AGENTS.md's "show every failure" rule, since the green run hides it.
- **Proposed AD-4 and AD-2 text:** "`funds_config.json` is the only fund set. Every configured fund appears in both `funds.json` and `nav-history.json` on every successful run. A fund with no previous data is written with `points: []` and `stale: true`, and the run prints a warning. Fund keys in `nav-history.json` equal the `id`s in `funds.json` exactly. The baseline covers every fund in `funds.json`, including a fund with no points, which is then carried at zero units."

## H4. The previous history is read silently, so AD-4's "keeps previous points" can empty a fund

- **Unit A (existing pattern):** the producer reads the previous file inside `try ... except (OSError, ValueError, KeyError): pass`. A corrupt or unreadable `nav-history.json` yields an empty previous map. Every stale fund is then written with empty points.
- **Unit B (AD-4):** "a fund keeps its previous points." It does not say what happens when the previous file cannot be read.
- **Also:** FR-7's first run after FR-6 has no `nav-history.json`. A fund that fails on that run has previous metrics in `funds.json` but nothing to keep in history.
- **ADs obeyed:** both units obey AD-4 as written. The rule's stated purpose is "prevents a half-written or emptied history", and the silent fallback produces exactly that.
- **Proposed AD-4 text:** "The producer reads the previous `nav-history.json` before fetching. If the file is absent, no fund has previous points, which is allowed only on the first run after FR-6. If the file exists and does not parse, the run exits 1 before any write. Reads of the previous state never fall back to empty silently."

## H5. "Replace the whole file in one call" is not atomic, and the two files can diverge

- **Unit A (current):** `OUTPUT.write_text(...)` opens with truncation and then writes, so a crash mid-write leaves a truncated file. With two files, `funds.json` can be written and `nav-history.json` can then fail, so the pair is out of step.
- **Unit B (AD-4 and AD-3):** "writes replace the whole file in one call" and "both files are staged in the same commit".
- **Incompatibility:** AD-3 protects the commit, not the local pair. A local run, or any run where the second write fails after the first succeeded, leaves `funds.json` describing the new run and the history describing the old one. The page reads both (AD-7). The repo already has a temp-file and `os.replace` pattern in `.claude/skills/bmad-retrospective/scripts/sprint_status.py`, which the producer does not use.
- **Proposed AD-4 text:** "Each file is written to a temp file in `data/` and moved into place with `os.replace`. Both temp files are written before either is moved, so a failure before the moves leaves both files unchanged, and `nav-history.json` is moved first so that `funds.json`, the file that defines the fund list, is the last to change."

## H6. Non-finite and zero closes break the contract, and one bad value breaks the whole page

- **Unit A (producer):** the filter `if p.get("C_p") is not None` lets through `0.0`, a negative number, or `nan` (from `float()` on odd input). `json.dumps` writes `NaN` and `Infinity`, which are not valid JSON.
- **Unit B (AD-2):** "`close` is a JSON number in NAV units."
- **Incompatibility:** `JSON.parse` throws on `NaN`, so `nav-history.json` cannot load at all. That is not a value AD-6 can turn into `'—'`, because the failure is at load time. A zero close produces `Infinity` in the page's return division. The producer's own `trailing_return` and `annualized_volatility` already treat `close <= 0` as invalid, so the spine's contract is looser than the producer it describes.
- **Proposed AD-2 text:** "`close` is a finite number greater than 0. The producer drops any other value, as it already drops `null` `C_p`. It serializes with `allow_nan=False`. A page that cannot parse `nav-history.json` shows the error next to the run control and disables the run; it never renders partial data."

## H7. Dates: the convention is broken in `funds.json`, and the range can be derived from either format

- **Unit A (existing `funds.json`):** `metrics.last_date` is `"22/10/2026"` (verified in `data/funds.json`). The producer does not convert it. The convention says "the source's `dd/mm/yyyy` is converted in the producer only", and `index.html` does not read `last_date` today.
- **Unit B (the backtest reader):** computes "last complete month" from `funds.json` `last_date`. `new Date("22/10/2026")` is an Invalid Date in V8, so the result is `NaN`, and AD-6 turns it into `'—'` without any error.
- **Unit C (the backtest reader, from points):** uses the ISO points in `nav-history.json`.
- **ADs obeyed:** AD-2 covers only `nav-history.json`, and the consistency table scopes ISO to "the contract", which the spine never defines to include `funds.json`. A and B obey the letter. C obeys AD-2.
- **Proposed AD-2 text:** "Every date in any file under `data/` is ISO `YYYY-MM-DD`. `metrics.last_date` in `funds.json` becomes ISO in the same change that adds `nav-history.json`. `index.html` does not read it today, so no page change is needed."

## H8. The clock and the range are unowned, and AD-1 is contradicted inside the spine

- **Spine contradiction:** AD-1 says `src/lib/` "never reads the clock". The capability map puts the "floor check" in `src/lib/backtest.js`. A floor check needs "the last complete calendar month", which needs today, which is a clock read.
- **Unit A (`index.html`):** the picker floor is the earliest first-date across funds. The "now" month is `new Date()` in local time.
- **Unit B (`backtest.js`):** the floor is the latest of each fund's first month (PRD glossary: "every fund has NAV data"). The "now" month comes from `generated_at` (producer clock, UTC).
- **Incompatibility:** the two disagree on the floor, and on the last month around the 1st of the month. A stale fund also ends the range early under the PRD's "every fund" rule, while FR-4 says a fund's gaps are carried forward, which would extend the range. Both units obey AD-5 and AD-6, because AD-5 does not define bounds at all.
- **Proposed new AD-8 (range and floor):** "`src/lib/backtest.js` exports `backtestBounds(navHistory, fundIds, nowMonth)`. `nowMonth` is passed in by `index.html` from the browser clock, and the lib never reads the clock. The floor is the latest of each fund's first month. The range ends at the last complete month before `nowMonth` in which every fund in `funds.json` has at least one point. A stale fund therefore ends the range, and the page must say so next to the control." Also fix the PRD glossary to match, or accept the stale truncation explicitly.

## H9. The fate of a no-NAV month's cash is unspecified

- **Unit A:** the cash from a month with no NAV for any fund stays at zero growth through the range end.
- **Unit B:** the cash is invested at the next month's first NAV, at the same weights.
- **ADs obeyed:** AD-5 says only "cash for months with no NAV at all". It does not say whether the cash is ever invested. The PRD says "held as cash at zero growth", which A reads literally and B could read as "held until invested".
- **Incompatibility:** the final values of both lines differ, so the SM-2 hand-computed fixture cannot pass for both.
- **Proposed AD-5 text:** "Cash from a month with no NAV for any fund is never invested. It stays in the cumulative value at zero growth through the range end, and the month is listed in the gap months."

## H10. AD-3's single writer is breached by the add-fund skill, and the commit path omits the history file

- **Unit A (`.claude/skills/add-fund/SKILL.md`):** a human or agent appends to `data/funds_config.json` (under `data/`), runs `fetch_data.py`, and commits "the config, README and `data/funds.json` together". It does not stage `data/nav-history.json`.
- **Unit B (AD-3):** "`scripts/fetch_data.py` is the only code that writes under `data/`", and the workflow is the only commit path that stages both data files.
- **ADs obeyed:** B is the rule. A is a second writer and a second commit path. It is not covered by AD-3's wording, which names only the workflow.
- **Incompatibility:** a commit made by following the skill adds a fund to `funds.json` with no history in the repo, so until the next daily run the page's floor and baseline use a fund with no points. The skill also commits generated output by hand, which the policy forbids.
- **Proposed AD-3 text:** "`data/funds_config.json` is the only human-written file under `data/`. Any commit that changes `data/funds.json` also changes `data/nav-history.json`. The add-fund skill runs `scripts/fetch_data.py` and stages both files, and never stages `funds.json` alone."

## H11. Low: the stale flag has two sources and no owner for the page's reading

- **Unit A (producer):** `stale` in `funds.json` and in `nav-history.json`, both set by fetch failure.
- **Unit B (page):** may derive "stale" from the age of the last point, which is also a reasonable reading of FR-7's "shows that fund's stored history as stale".
- **Incompatibility:** the page can show a fund stale that the producer did not mark, or the reverse.
- **Proposed AD-2 text:** "`stale` is set only by the producer when a fetch fails. `nav-history.json` and `funds.json` carry the same flag for the same id. The page reads the flag and never derives staleness from dates."

## H12. Low: the workflow's push path has no failure rule

- **Unit A (workflow):** `git push` with no rebase. If the push is rejected, the run fails and the day's pair is lost.
- **Unit B (AGENTS.md policy):** "pull with rebase" before pushing.
- **Incompatibility:** AD-4 covers producer failure only, so the commit and push failure path is unowned.
- **Proposed AD-3 text:** "The workflow runs `git pull --rebase` before `git push`, and a failed push fails the run."

---

## Summary of proposed changes

1. AD-4: define the all-fail abort as zero fresh fetches, before any write, and fix `main()` to match.
2. AD-4: a fund with no previous data is written as `points: []` with `stale: true`, and the fund set is `funds_config.json` only.
3. AD-2: a successful run merges by date and never drops a date. Remove the Deferred contradiction.
4. AD-2: `close` is finite and above 0, every date is ISO (including `funds.json`), and `stale` has one owner.
5. AD-3: the add-fund skill and any `funds.json` commit must stage both files.
6. AD-5: cash from a no-NAV month is never invested.
7. New AD-8: range and floor are computed in the lib from a `nowMonth` passed in by the page, which resolves the AD-1 contradiction.
8. AD-4: atomic writes (temp file and `os.replace`), and a previous-state read that fails aborts instead of falling back to empty.
