---
description: Compare two funds from data/funds.json by id — score, returns, volatility and suggested weight.
argument-hint: "<fund-id> <fund-id>  (comma or space)"
allowed-tools: Bash(git log *), Read
---

Data last changed in git: !`git log -1 --format=%cI -- data/funds.json`

@data/funds.json

The arguments are $ARGUMENTS: two fund ids separated by a comma, a space, or both. Compare those two funds from the JSON above. If either id is missing, say so and stop.

Show a table with one row per metric: `risk_adjusted_score`, `return_1y`, `return_3y`, `volatility_blended`, `stale`, `suggested_weight`. Then name the fund with the higher score in one sentence.

End with one line: the score is a heuristic over past returns, not financial advice.
