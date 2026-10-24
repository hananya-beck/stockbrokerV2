---
paths:
  - "data/**"
  - ".claude/skills/add-fund/**"
---

# Recovering a broken nav-history.json

- A `data/nav-history.json` that does not parse, including one left with conflict markers, stops the daily run before any fetch. That is intended. Do not work around it.
- Recover by regenerating the file: run `python scripts/fetch_data.py`. Do not hand-merge the history, because a hand merge can keep stale or invalid points.
- Dropping `nav-history.json` loses all accumulated history. Only do that when a human has decided the history is expendable.
