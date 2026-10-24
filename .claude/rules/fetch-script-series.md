---
paths:
  - "scripts/**"
---

# Fetch script: one cleaned series, strict output

- Each fund's price series is cleaned once, before anything reads it: keep only finite closes above zero. Metrics, the stored history and any other output read that same cleaned series. Never compute metrics from the raw response.
- Every JSON file the producer writes is serialised with `allow_nan=False`, including `data/funds.json`. A non-finite value must fail the write loudly, not produce a file the page cannot parse.
- A test parses the written `data/funds.json` strictly (rejecting `NaN` and `Infinity`).
