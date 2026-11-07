---
description: Compare two funds from data/funds.json by id — score, returns, volatility and suggested weight.
argument-hint: "<fund-id-a> <fund-id-b>"
arguments: [a, b]
allowed-tools: Bash(git log *), Read
---

Data last changed in git: !`git log -1 --format=%cI -- data/funds.json`

@data/funds.json

Compare the funds with id **$a** and **$b** from the JSON above. If either id is missing, say so and stop.

Show a table with one row per metric: `risk_adjusted_score`, `return_1y`, `return_3y`, `volatility_blended`, `stale`, `suggested_weight`. Then name the fund with the higher score in one sentence.

End with one line: the score is a heuristic over past returns, not financial advice.
