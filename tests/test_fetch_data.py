import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from fetch_data import (  # noqa: E402
    allocate_weights,
    annualized_return,
    annualized_volatility,
    compute_metrics,
    fetch_fund_series,
    nav_history_payload,
    nav_points,
    trailing_return,
)


def make_series(prices):
    return [{"date": f"day{i}", "close": p} for i, p in enumerate(prices)]


def test_trailing_return_simple_growth():
    series = make_series([100.0] * 10 + [110.0])
    assert math.isclose(trailing_return(series, 10), 0.10)


def test_trailing_return_insufficient_history_is_none():
    series = make_series([100.0, 101.0, 102.0])
    assert trailing_return(series, 10) is None


def test_annualized_return_matches_cagr_formula():
    series = make_series([100.0] * 252 + [121.0])
    ret = annualized_return(series, 252)
    assert math.isclose(ret, 0.21, abs_tol=1e-9)


def test_annualized_volatility_zero_for_flat_series():
    series = make_series([100.0] * 253)
    vol = annualized_volatility(series, 252)
    assert vol == 0.0


def test_compute_metrics_blended_volatility_uses_available_horizons_only():
    # Only a 1y-length window of real history (no 3y/5y data), so the
    # blended figure should equal the 1y volatility exactly.
    prices = [100.0]
    for i in range(1, 253):
        prices.append(prices[-1] * (1.001 if i % 2 == 0 else 0.999))
    series = make_series(prices)

    metrics = compute_metrics(series)

    assert metrics["volatility_3y"] is None
    assert metrics["volatility_5y"] is None
    assert metrics["volatility_1y"] is not None
    assert math.isclose(metrics["volatility_blended"], metrics["volatility_1y"])


def test_compute_metrics_no_history_gives_none_score_and_blend():
    series = make_series([100.0, 101.0])
    metrics = compute_metrics(series)
    assert metrics["risk_adjusted_score"] is None
    assert metrics["volatility_blended"] is None


def test_annualized_volatility_skips_zero_price_without_crashing():
    series = make_series([100.0] * 10 + [0.0] + [100.0] * 10)
    assert annualized_volatility(series, 20) == 0.0


def test_score_subtracts_risk_free_rate():
    prices = [100.0]
    for i in range(1, 253):
        prices.append(prices[-1] * (1.002 if i % 2 == 0 else 0.999))
    series = make_series(prices)
    m0 = compute_metrics(series, risk_free_rate=0.0)
    m4 = compute_metrics(series, risk_free_rate=0.04)
    expected = m0["risk_adjusted_score"] - 0.04 / m0["volatility_1y"]
    assert math.isclose(m4["risk_adjusted_score"], expected)


def test_young_fund_scored_on_partial_history():
    prices = [100.0]
    for i in range(1, 200):
        prices.append(prices[-1] * (1.002 if i % 2 == 0 else 0.999))
    metrics = compute_metrics(make_series(prices))
    assert metrics["score_basis"] == "partial_history"
    assert metrics["risk_adjusted_score"] is not None


def _fund(score):
    return {"metrics": {"risk_adjusted_score": score}}


def test_worst_fund_gets_more_than_floor():
    funds = [_fund(1.0), _fund(0.5), _fund(-0.5)]
    allocate_weights(funds)
    assert math.isclose(sum(f["suggested_weight"] for f in funds), 1.0)
    assert funds[2]["suggested_weight"] > 0.03 + 0.01


def test_floor_capped_for_many_funds():
    funds = [_fund(None) for _ in range(40)] + [_fund(1.0)]
    allocate_weights(funds)
    assert all(f["suggested_weight"] >= 0 for f in funds)
    assert math.isclose(sum(f["suggested_weight"] for f in funds), 1.0, abs_tol=1e-6)


class _Response:
    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body


class _FakeOpener:
    def __init__(self, body):
        self._body = body

    def open(self, req, timeout=None):
        return _Response(self._body)


PRICE_BODY = (
    b'~[{"D_p":"02/01/2026","C_p":"1.5"},'
    b'{"D_p":"03/01/2026","C_p":null},'
    b'{"D_p":"01/01/2026","C_p":"1.0"}]'
)


def test_fetch_series_has_iso_dates_sorted_ascending_and_skips_null_close():
    series = fetch_fund_series(_FakeOpener(PRICE_BODY), "123")
    assert [p["date"] for p in series] == ["2026-01-01", "2026-01-02"]
    assert [p["close"] for p in series] == [1.0, 1.5]


def test_last_date_is_iso():
    series = fetch_fund_series(_FakeOpener(PRICE_BODY), "123")
    assert compute_metrics(series)["last_date"] == "2026-01-02"


def test_nav_points_drop_zero_negative_and_non_finite_closes():
    series = [
        {"date": "2026-01-01", "close": 1.0},
        {"date": "2026-01-02", "close": 0.0},
        {"date": "2026-01-03", "close": -2.0},
        {"date": "2026-01-04", "close": float("nan")},
        {"date": "2026-01-05", "close": float("inf")},
        {"date": "2026-01-06", "close": 2.0},
    ]
    assert nav_points(series) == [["2026-01-01", 1.0], ["2026-01-06", 2.0]]


def test_nav_history_payload_serializes_as_strict_json():
    series = [
        {"date": "2026-01-01", "close": 1.0},
        {"date": "2026-01-02", "close": float("nan")},
    ]
    payload = nav_history_payload({"123": series}, "2026-01-07T00:00:00+00:00")
    text = json.dumps(payload, allow_nan=False)
    assert json.loads(text)["funds"]["123"] == {
        "stale": False,
        "points": [["2026-01-01", 1.0]],
    }


def test_failed_fund_is_absent_from_history_and_run_continues(tmp_path, monkeypatch):
    import fetch_data

    config = tmp_path / "funds_config.json"
    config.write_text(
        json.dumps({"funds": [{"id": "1"}, {"id": "2"}]}), encoding="utf-8"
    )
    monkeypatch.setattr(fetch_data, "FUNDS_CONFIG", config)
    monkeypatch.setattr(fetch_data, "OUTPUT", tmp_path / "funds.json")
    monkeypatch.setattr(fetch_data, "NAV_HISTORY", tmp_path / "nav-history.json")
    monkeypatch.setattr(fetch_data, "build_opener", lambda: None)

    series = [
        {"date": "2026-01-01", "close": 1.0},
        {"date": "2026-01-02", "close": 1.1},
    ]

    def fake_fetch(opener, fund_id):
        if fund_id == "2":
            raise RuntimeError("source unavailable")
        return series

    monkeypatch.setattr(fetch_data, "fetch_fund_series", fake_fetch)
    fetch_data.main()

    history = json.loads((tmp_path / "nav-history.json").read_text(encoding="utf-8"))
    assert list(history["funds"]) == ["1"]
    assert history["funds"]["1"]["points"] == [["2026-01-01", 1.0], ["2026-01-02", 1.1]]
    assert (tmp_path / "funds.json").exists()


def test_all_fetches_failing_keeps_last_good_history(tmp_path, monkeypatch):
    import fetch_data

    config = tmp_path / "funds_config.json"
    config.write_text(json.dumps({"funds": [{"id": "1"}]}), encoding="utf-8")
    output = tmp_path / "funds.json"
    output.write_text(
        json.dumps({"funds": [{"id": "1", "metrics": {"risk_adjusted_score": None}}]}),
        encoding="utf-8",
    )
    history = tmp_path / "nav-history.json"
    history.write_text('{"sentinel": true}', encoding="utf-8")
    monkeypatch.setattr(fetch_data, "FUNDS_CONFIG", config)
    monkeypatch.setattr(fetch_data, "OUTPUT", output)
    monkeypatch.setattr(fetch_data, "NAV_HISTORY", history)
    monkeypatch.setattr(fetch_data, "build_opener", lambda: None)

    def failing_fetch(opener, fund_id):
        raise RuntimeError("source unavailable")

    monkeypatch.setattr(fetch_data, "fetch_fund_series", failing_fetch)
    fetch_data.main()

    assert history.read_text(encoding="utf-8") == '{"sentinel": true}'


def test_seven_funds_full_history_is_under_5_mb():
    start = date(2021, 1, 1)
    series_by_id = {
        str(fund): [
            {"date": (start + timedelta(days=i)).isoformat(), "close": 100.0 + i}
            for i in range(1260)
        ]
        for fund in range(7)
    }
    payload = nav_history_payload(series_by_id, "2026-10-25T00:00:00+00:00")
    size = len(json.dumps(payload, indent=2, allow_nan=False).encode("utf-8"))
    assert size < 5_000_000
