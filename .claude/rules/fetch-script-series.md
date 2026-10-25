---
paths:
  - "scripts/**"
---

# Fetch script: one cleaned series, strict output

Added 2026-10-25. Reason: `_bmad-output/implementation-artifacts/epic-1-retro-2026-10-25.md` findings F1 and F2. Story 1.1 let the metrics read the raw response, so one negative close aborted the daily run and one NaN close wrote an unparseable `funds.json`. Fixed in commit `025b302`.

- Each fund's price series is cleaned once, before anything reads it: keep only finite closes above zero. Metrics, the stored history and any other output read that same cleaned series. Never compute metrics from the raw response.
- Every JSON file the producer writes is serialised with `allow_nan=False`, including `data/funds.json`. A non-finite value must fail the write loudly, not produce a file the page cannot parse.

**Bad**

```python
series = fetch_fund_series(opener, entry["id"])
metrics = compute_metrics(series, risk_free_rate)
```

**Good**

```python
series = clean_series(fetch_fund_series(opener, entry["id"]))
metrics = compute_metrics(series, risk_free_rate)
```

Enforced by `tests/test_fetch_data.py::test_main_drops_bad_closes_before_metrics_and_writes_strict_funds_json`, which fails if the raw series reaches the metrics.
