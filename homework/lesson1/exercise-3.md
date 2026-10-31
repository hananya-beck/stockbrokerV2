# Exercise 3 — seven techniques in one prompt

> Written after the fact from commit `55b2a94` and its prompt file, `prompts/exercise-3-seven-techniques.md`. The prompt header asks for `/effort high` and says nothing about thinking harder.

## The prompt

The prompt combines the seven techniques in one message:

- **Data first:** `@`-references to the existing helpers, the render function, and the tokens file come before any instruction.
- **Role:** a front-end engineer who keeps business logic in pure, tested functions.
- **Brief once:** the goal, the reason, the scope, and the done-when condition are stated up front.
- **Be specific:** the file, function, inputs, outputs, and check are named.
- **Constraints:** what is in scope and what is out.
- **Multishot:** three examples with exact expected output. They double as the test cases.
- **XML structure:** every block is tagged.

## What changed

- **`src/lib/formatting.js`:** `summarizeAllocation(funds, amount)` returns `{ fundCount, totalAmount, weightedScore }`.
  - `totalAmount` sums each fund's rounded amount, so the rounding drift is shown, not hidden.
  - `weightedScore` is the weight-times-score average over funds that have a score, formatted with `formatScore`. It is "—" when no fund has a score.
- **`tests/js/formatting.test.js`:** four tests. Three cover the prompt's multishot examples (the weighted score, the rounding drift, and funds without a score), and one covers the "—" case when no fund has a score.
- **`index.html`:** a `<tfoot>` row in `#fundsTable` shows "סה״כ: ₪… · N קרנות · ציון משוקלל: …". It re-renders on amount input together with the body rows.
- **Styling:** the row uses only existing CSS variables (`--border`, `--space-4`).

## Scope the prompt set

Out of scope: no new dependencies, no network or storage calls, no edits to `scripts/`, `data/`, or the per-row cells. The done-when condition was `npm run check` green. The commit doesn't record that run's output.
