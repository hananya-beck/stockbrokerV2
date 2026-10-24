#!/usr/bin/env python3
"""Fetch daily NAV history for the configured TASE funds from bizportal.co.il
and compute trailing returns, volatility and a suggested monthly allocation.

Writes the result to data/funds.json, which the static site (index.html) reads.
"""
import itertools
import json
import math
import sys
import statistics
import time
import urllib.request
from datetime import UTC, date, datetime
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FUNDS_CONFIG = ROOT / "data" / "funds_config.json"
OUTPUT = ROOT / "data" / "funds.json"
NAV_HISTORY = ROOT / "data" / "nav-history.json"

USER_AGENT = "Mozilla/5.0 (compatible; stockbroker-fetch/1.0)"
BASE = "https://www.bizportal.co.il"

TRADING_DAYS_PER_YEAR = 252

# Short horizons: reported as simple cumulative return, for context only.
SHORT_HORIZONS = {"1m": 21, "3m": 63, "6m": 126}

# Long horizons: reported as annualized (CAGR) return + annualized volatility,
# and blended into the risk-adjusted score. Longer windows are weighted more
# heavily since they're less noisy, but 1y keeps the score responsive to
# recent trend. A horizon only counts if the fund has a full window of history.
LONG_HORIZONS = {"1y": 252, "3y": 756, "5y": 1260}
LONG_HORIZON_WEIGHTS = {"1y": 0.25, "3y": 0.35, "5y": 0.40}

# Minimum weight floor per fund so the recommendation never drops a fund to 0%,
# keeping the user's existing diversification across all 7 baskets.
MIN_WEIGHT = 0.03

# Annual risk-free rate subtracted from returns before dividing by volatility,
# so the score is a Sharpe ratio rather than raw return/vol. Roughly the Bank of
# Israel rate; override per run with "risk_free_rate" in funds_config.json.
DEFAULT_RISK_FREE_RATE = 0.04

# Funds younger than 1y are scored on their full history instead, as long as
# they have at least this many trading days; the score is discounted since a
# short window is noisier.
MIN_PARTIAL_HISTORY_DAYS = SHORT_HORIZONS["6m"]
PARTIAL_HISTORY_DISCOUNT = 0.5

# When shifting scores positive, the worst fund is placed this fraction of the
# score range above zero, so it still gets some share above MIN_WEIGHT.
SHIFT_FLOOR_FRACTION = 0.1


def build_opener():
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-Agent", USER_AGENT)]
    return opener


def fetch_fund_series(opener, fund_id):
    quote_url = f"{BASE}/mutualfunds/quote/graphs/{fund_id}"
    # Visit the quote page first to pick up the session cookie the AJAX endpoint requires.
    req = urllib.request.Request(quote_url, headers={"User-Agent": USER_AGENT})
    opener.open(req, timeout=20).read()

    ajax_url = (
        f"{BASE}/ajax/biz_papers_helper.ashx?action=get_paper_yearly_graph"
        f"&request_type=1&paper_id={fund_id}&dd={int(time.time() * 1000)}"
    )
    req = urllib.request.Request(
        ajax_url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": quote_url,
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    raw = opener.open(req, timeout=20).read().decode("utf-8")
    # bizportal prefixes the JSON array with a stray "~" marker.
    raw = raw[raw.index("[") :]
    points = json.loads(raw)
    # Points come back newest-first; sort ascending by date for return calculations.
    series = [
        {
            "date": datetime.strptime(p["D_p"], "%d/%m/%Y").date().isoformat(),
            "close": float(p["C_p"]),
        }
        for p in points
        if p.get("C_p") is not None
    ]
    # ISO dates sort lexically, so this orders the series by date.
    series.sort(key=lambda p: p["date"])
    return series


def nav_points(series):
    return [
        [p["date"], p["close"]]
        for p in series
        if math.isfinite(p["close"]) and p["close"] > 0
    ]


def merge_points(previous, fetched):
    by_date = {**dict(previous), **dict(fetched)}
    return [[date, close] for date, close in sorted(by_date.items())]


def _is_iso_date(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _is_point(point):
    return (
        isinstance(point, list)
        and len(point) == 2
        and _is_iso_date(point[0])
        and isinstance(point[1], (int, float))
        and not isinstance(point[1], bool)
        and math.isfinite(point[1])
        and point[1] > 0
    )


def _is_history_entry(entry):
    return (
        isinstance(entry, dict)
        and isinstance(entry.get("stale"), bool)
        and isinstance(entry.get("points"), list)
        and all(_is_point(p) for p in entry["points"])
    )


def read_previous_history(path):
    """Stored `{fund_id: {"stale", "points"}}`; `{}` when no file exists yet."""
    if not path.exists():
        return {}
    try:
        funds = json.loads(path.read_text(encoding="utf-8"))["funds"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        sys.exit(f"Cannot read previous history {path}: {exc}")
    if not isinstance(funds, dict) or not all(map(_is_history_entry, funds.values())):
        sys.exit(f"Previous history {path} has an unexpected shape")
    return funds


def nav_history_payload(series_by_id, generated_at, previous=None):
    previous = previous or {}
    merged = {
        fund_id: {
            "stale": False,
            "points": merge_points(
                previous.get(fund_id, {}).get("points", []), nav_points(series)
            ),
        }
        for fund_id, series in series_by_id.items()
    }
    carried = {k: v for k, v in previous.items() if k not in series_by_id}
    return {"generated_at": generated_at, "funds": {**merged, **carried}}


def trailing_return(series, days):
    """Simple cumulative return over the trailing `days`, or None if not enough history."""
    if len(series) <= days:
        return None
    start = series[-days - 1]["close"]
    end = series[-1]["close"]
    if start == 0:
        return None
    return (end / start) - 1.0


def annualized_return(series, days):
    """CAGR over the trailing `days`, or None if not enough history."""
    cum = trailing_return(series, days)
    if cum is None:
        return None
    return (1.0 + cum) ** (TRADING_DAYS_PER_YEAR / days) - 1.0


def annualized_volatility(series, days):
    """Annualized stdev of daily log returns over the trailing `days`.

    Requires a *full* window (not a partial one) so volatility is comparable
    across funds with different amounts of history.
    """
    if len(series) <= days:
        return None
    window = series[-days - 1 :]
    daily_returns = [
        math.log(cur["close"] / prev["close"])
        for prev, cur in itertools.pairwise(window)
        if prev["close"] > 0 and cur["close"] > 0
    ]
    if len(daily_returns) < 2:
        return None
    return statistics.pstdev(daily_returns) * math.sqrt(TRADING_DAYS_PER_YEAR)


def compute_metrics(series, risk_free_rate=DEFAULT_RISK_FREE_RATE):
    metrics = {}
    for label, days in SHORT_HORIZONS.items():
        metrics[f"return_{label}"] = trailing_return(series, days)

    horizon_scores = {}
    horizon_vols = {}
    for label, days in LONG_HORIZONS.items():
        ret = annualized_return(series, days)
        vol = annualized_volatility(series, days)
        metrics[f"return_{label}"] = ret
        metrics[f"volatility_{label}"] = vol
        if vol is not None:
            horizon_vols[label] = vol
        if ret is not None and vol:
            horizon_scores[label] = (ret - risk_free_rate) / vol

    metrics["score_basis"] = None
    if horizon_scores:
        weight_sum = sum(LONG_HORIZON_WEIGHTS[l] for l in horizon_scores)
        metrics["risk_adjusted_score"] = sum(
            horizon_scores[l] * LONG_HORIZON_WEIGHTS[l] for l in horizon_scores
        ) / weight_sum
        metrics["score_basis"] = "long_horizons"
    else:
        metrics["risk_adjusted_score"] = None
        days = len(series) - 1
        if days >= MIN_PARTIAL_HISTORY_DAYS:
            ret = annualized_return(series, days)
            vol = annualized_volatility(series, days)
            if ret is not None and vol:
                metrics["risk_adjusted_score"] = (
                    PARTIAL_HISTORY_DISCOUNT * (ret - risk_free_rate) / vol
                )
                metrics["score_basis"] = "partial_history"

    # Blended volatility: same 1y/3y/5y weights as the score, averaged over
    # whichever horizons the fund has a full window for.
    if horizon_vols:
        weight_sum = sum(LONG_HORIZON_WEIGHTS[l] for l in horizon_vols)
        metrics["volatility_blended"] = sum(
            horizon_vols[l] * LONG_HORIZON_WEIGHTS[l] for l in horizon_vols
        ) / weight_sum
    else:
        metrics["volatility_blended"] = None

    metrics["history_days"] = len(series)
    metrics["last_price"] = series[-1]["close"]
    metrics["last_date"] = series[-1]["date"]
    return metrics


def allocate_weights(funds):
    scored = [f for f in funds if f["metrics"]["risk_adjusted_score"] is not None]
    if not scored:
        equal = round(1.0 / len(funds), 4)
        for f in funds:
            f["suggested_weight"] = equal
        return

    # Shift scores positive so a negative risk-adjusted score doesn't zero out a
    # fund; the worst fund lands a fraction of the score range above zero.
    scores = [f["metrics"]["risk_adjusted_score"] for f in scored]
    lo, hi = min(scores), max(scores)
    shift = 0
    if lo <= 0:
        shift = -lo + max(SHIFT_FLOOR_FRACTION * (hi - lo), 0.01)
    shifted = {id(f): f["metrics"]["risk_adjusted_score"] + shift for f in scored}
    total_shifted = sum(shifted.values())

    n = len(funds)
    # Cap the floor so it can never exceed 100% in total.
    min_weight = min(MIN_WEIGHT, 1.0 / n)
    remaining = 1.0 - min_weight * n
    for f in funds:
        base = min_weight
        if f["metrics"]["risk_adjusted_score"] is not None:
            base += remaining * (shifted[id(f)] / total_shifted)
        f["suggested_weight"] = round(base, 4)

    # Normalize rounding drift back to exactly 1.0.
    drift = 1.0 - sum(f["suggested_weight"] for f in funds)
    funds[0]["suggested_weight"] = round(funds[0]["suggested_weight"] + drift, 4)


def main():
    config = json.loads(FUNDS_CONFIG.read_text(encoding="utf-8"))
    risk_free_rate = config.get("risk_free_rate", DEFAULT_RISK_FREE_RATE)
    configured_ids = {entry["id"] for entry in config["funds"]}
    stored_history = {
        fund_id: entry
        for fund_id, entry in read_previous_history(NAV_HISTORY).items()
        if fund_id in configured_ids
    }
    opener = build_opener()

    # Previous output, used as a fallback for any fund whose fetch fails.
    previous = {}
    if OUTPUT.exists():
        try:
            old = json.loads(OUTPUT.read_text(encoding="utf-8"))
            previous = {f["id"]: f["metrics"] for f in old.get("funds", [])}
        except (OSError, ValueError, KeyError):
            pass

    funds = []
    failures = []
    series_by_id = {}
    for entry in config["funds"]:
        try:
            series = fetch_fund_series(opener, entry["id"])
            if not series:
                raise ValueError("empty price series")
            metrics = compute_metrics(series, risk_free_rate)
            funds.append({**entry, "metrics": metrics, "stale": False})
            series_by_id[entry["id"]] = series
        except Exception as exc:  # noqa: BLE001 - one bad fund shouldn't stop the run
            failures.append(entry["id"])
            print(f"Failed to fetch fund {entry['id']}: {exc}", file=sys.stderr)
            if entry["id"] in previous:
                funds.append({**entry, "metrics": previous[entry["id"]], "stale": True})

    if not funds:
        sys.exit("All fund fetches failed; leaving existing output untouched")

    funds.sort(
        key=lambda f: (f["metrics"]["risk_adjusted_score"] is None,
                        -(f["metrics"]["risk_adjusted_score"] or 0))
    )
    allocate_weights(funds)

    output = {
        "generated_at": datetime.now(UTC).isoformat(),
        "funds": funds,
    }
    OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {OUTPUT} with {len(funds)} funds")
    if series_by_id:
        # Keep the last good history when every fetch failed.
        history = nav_history_payload(
            series_by_id, output["generated_at"], stored_history
        )
        NAV_HISTORY.write_text(
            json.dumps(history, ensure_ascii=False, indent=2, allow_nan=False),
            encoding="utf-8",
        )
        print(f"Wrote {NAV_HISTORY} with {len(series_by_id)} funds")
    if failures:
        print(f"Warning: {len(failures)} fund(s) failed: {', '.join(failures)}", file=sys.stderr)


if __name__ == "__main__":
    main()
