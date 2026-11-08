---
description: Add a TASE fund, ETF or קרן סל to the dashboard by its bizportal security ID, then refresh the data and show the new weights. Also removes or renames a fund.
argument-hint: "<security ID> [Hebrew name] [English name]"
---

# Add a fund

Arguments: $ARGUMENTS

1. Get the bizportal security ID (the number in `bizportal.co.il/mutualfunds/quote/.../<id>`) and the Hebrew and English names. Ask for whichever is missing.
2. Check that `data/funds_config.json` doesn't already list that ID.
3. Check that data is available before editing anything:
   ```bash
   python -c "import sys; sys.path.insert(0,'scripts'); import fetch_data as f; s=f.fetch_fund_series(f.build_opener(), 'ID'); print(len(s), s[0], s[-1])"
   ```
   Stop and report if this fails or returns no points.
4. Append `{"id": "...", "name_he": "...", "name_en": "..."}` to `funds` in `data/funds_config.json`, keeping the UTF-8 Hebrew as-is.
5. Add the fund to the "The 7 funds" table in `README.md`, and update the count in the heading and anywhere else the README mentions it.
6. Run `python scripts/fetch_data.py`, then show the new fund's score, `score_basis` and the updated weights for every fund. Funds with under 6 months of history get only the minimum weight.
7. Run `python -m pytest tests -q`. Commit the config, README, `data/funds.json` and `data/nav-history.json` together, and push only if the user asks. Rebase onto the daily data bot's commit if the push is rejected.

To remove or rename a fund, edit the same two files and rerun step 6.
