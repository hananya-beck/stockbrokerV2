import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from fetch_data import (  # noqa: E402
    allocate_weights,
    annualized_return,
    annualized_volatility,
    compute_metrics,
    fetch_fund_series,
    merge_points,
    nav_history_payload,
    nav_points,
    read_previous_history,
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
    history.write_text('{"funds": {}, "sentinel": true}', encoding="utf-8")
    monkeypatch.setattr(fetch_data, "FUNDS_CONFIG", config)
    monkeypatch.setattr(fetch_data, "OUTPUT", output)
    monkeypatch.setattr(fetch_data, "NAV_HISTORY", history)
    monkeypatch.setattr(fetch_data, "build_opener", lambda: None)

    def failing_fetch(opener, fund_id):
        raise RuntimeError("source unavailable")

    monkeypatch.setattr(fetch_data, "fetch_fund_series", failing_fetch)
    fetch_data.main()

    assert history.read_text(encoding="utf-8") == '{"funds": {}, "sentinel": true}'


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


def _reject_constant(name):
    raise ValueError(f"non-finite constant {name} in output")


def test_main_writes_strict_history_under_5_mb_and_iso_last_date(tmp_path, monkeypatch):
    import fetch_data

    config = tmp_path / "funds_config.json"
    config.write_text(
        json.dumps({"funds": [{"id": str(fund)} for fund in range(7)]}), encoding="utf-8"
    )
    monkeypatch.setattr(fetch_data, "FUNDS_CONFIG", config)
    monkeypatch.setattr(fetch_data, "OUTPUT", tmp_path / "funds.json")
    monkeypatch.setattr(fetch_data, "NAV_HISTORY", tmp_path / "nav-history.json")
    monkeypatch.setattr(fetch_data, "build_opener", lambda: None)

    start = date(2021, 1, 1)
    series = [
        {"date": (start + timedelta(days=i)).isoformat(), "close": 100.0 + i}
        for i in range(1260)
    ]
    monkeypatch.setattr(fetch_data, "fetch_fund_series", lambda opener, fund_id: series)
    fetch_data.main()

    history_path = tmp_path / "nav-history.json"
    assert history_path.stat().st_size < 5_000_000
    json.loads(history_path.read_text(encoding="utf-8"), parse_constant=_reject_constant)

    last_day = (start + timedelta(days=1259)).isoformat()
    funds = json.loads((tmp_path / "funds.json").read_text(encoding="utf-8"))["funds"]
    assert all(fund["metrics"]["last_date"] == last_day for fund in funds)


def _pts(*pairs):
    return [[f"2026-01-0{d}", c] for d, c in pairs]


def _entry(points, stale=False):
    return {"stale": stale, "points": points}


def test_merge_keeps_older_dates_and_sorts_ascending():
    previous = _pts((1, 1.0), (2, 1.1), (3, 1.2), (4, 1.3), (5, 1.4))
    fetched = _pts((6, 1.6), (4, 1.3), (5, 1.4))
    assert merge_points(previous, fetched) == _pts(
        (1, 1.0), (2, 1.1), (3, 1.2), (4, 1.3), (5, 1.4), (6, 1.6)
    )


def test_merge_prefers_this_runs_close_on_shared_date():
    assert merge_points(_pts((1, 1.0), (2, 1.1)), _pts((2, 9.9))) == _pts((1, 1.0), (2, 9.9))


def test_payload_merges_fetched_fund_and_marks_it_fresh():
    previous = {"1": _entry(_pts((1, 1.0), (2, 1.1)), stale=True)}
    series = [{"date": "2026-01-02", "close": 2.0}, {"date": "2026-01-03", "close": 3.0}]
    payload = nav_history_payload({"1": series}, "t", previous)
    assert payload["funds"]["1"] == _entry(_pts((1, 1.0), (2, 2.0), (3, 3.0)))


def test_payload_with_no_previous_holds_fetched_series_alone():
    series = [{"date": "2026-01-01", "close": 1.0}]
    payload = nav_history_payload({"1": series}, "t")
    assert payload["funds"] == {"1": _entry(_pts((1, 1.0)))}


def test_read_previous_history_absent_file_is_empty(tmp_path):
    assert read_previous_history(tmp_path / "missing.json") == {}


def test_read_previous_history_returns_stored_entries(tmp_path):
    path = tmp_path / "nav-history.json"
    entries = {"1": _entry(_pts((1, 1.0)), stale=True)}
    path.write_text(json.dumps({"funds": entries}), encoding="utf-8")
    assert read_previous_history(path) == entries


def _write_unreadable(tmp_path, monkeypatch, content, fetch_calls):
    import fetch_data

    config = tmp_path / "funds_config.json"
    config.write_text(json.dumps({"funds": [{"id": "1"}]}), encoding="utf-8")
    history = tmp_path / "nav-history.json"
    history.write_text(content, encoding="utf-8")
    monkeypatch.setattr(fetch_data, "FUNDS_CONFIG", config)
    monkeypatch.setattr(fetch_data, "OUTPUT", tmp_path / "funds.json")
    monkeypatch.setattr(fetch_data, "NAV_HISTORY", history)
    monkeypatch.setattr(fetch_data, "build_opener", lambda: None)
    monkeypatch.setattr(
        fetch_data,
        "fetch_fund_series",
        lambda opener, fund_id: fetch_calls.append(fund_id) or [],
    )


def _stored(point=None, **entry):
    body = {"stale": False, "points": [point or ["2026-01-01", 1.0]], **entry}
    return json.dumps({"funds": {"1": body}})


UNREADABLE_HISTORY = {
    "invalid-json": "not json",
    "no-funds-key": "{}",
    "top-level-list": "[]",
    "funds-is-list": '{"funds": []}',
    "string-close": _stored(["2026-01-01", "x"]),
    "nan-close": '{"funds": {"1": {"stale": false, "points": [["2026-01-01", NaN]]}}}',
    "missing-stale": '{"funds": {"1": {"points": []}}}',
    "three-element-point": _stored(["2026-01-01", 1.0, 2.0]),
    "non-string-date": _stored([20260101, 1.0]),
    "non-iso-date": _stored(["2026-1-5", 1.0]),
    "garbage-date": _stored(["x", 1.0]),
    "boolean-close": '{"funds": {"1": {"stale": false, "points": [["2026-01-01", true]]}}}',
    "zero-close": _stored(["2026-01-01", 0]),
    "negative-close": _stored(["2026-01-01", -1.0]),
    "infinity-close": '{"funds": {"1": {"stale": false, "points": [["2026-01-01", Infinity]]}}}',
    "non-boolean-stale": _stored(stale="no"),
    "non-list-points": '{"funds": {"1": {"stale": false, "points": {}}}}',
    "non-object-entry": '{"funds": {"1": []}}',
}


@pytest.mark.parametrize("content", UNREADABLE_HISTORY.values(), ids=UNREADABLE_HISTORY.keys())
def test_unreadable_previous_history_exits_before_any_write(tmp_path, monkeypatch, content):
    import fetch_data

    calls = []
    _write_unreadable(tmp_path, monkeypatch, content, calls)
    with pytest.raises(SystemExit) as exc:
        fetch_data.main()
    assert "nav-history.json" in str(exc.value)
    assert calls == []
    assert not (tmp_path / "funds.json").exists()
    assert (tmp_path / "nav-history.json").read_text(encoding="utf-8") == content


def _run_main(tmp_path, monkeypatch, config_ids, fetch):
    import fetch_data

    config = tmp_path / "funds_config.json"
    config.write_text(
        json.dumps({"funds": [{"id": i} for i in config_ids]}), encoding="utf-8"
    )
    monkeypatch.setattr(fetch_data, "FUNDS_CONFIG", config)
    monkeypatch.setattr(fetch_data, "OUTPUT", tmp_path / "funds.json")
    monkeypatch.setattr(fetch_data, "NAV_HISTORY", tmp_path / "nav-history.json")
    monkeypatch.setattr(fetch_data, "build_opener", lambda: None)
    monkeypatch.setattr(fetch_data, "fetch_fund_series", fetch)
    fetch_data.main()
    return json.loads((tmp_path / "nav-history.json").read_text(encoding="utf-8"))


def _series(pairs):
    return [{"date": f"2026-01-0{d}", "close": c} for d, c in pairs]


def test_two_runs_keep_every_date_from_the_first(tmp_path, monkeypatch):
    first = _series([(1, 1.0), (2, 1.1), (3, 1.2)])
    second = _series([(3, 1.25), (4, 1.3)])
    _run_main(tmp_path, monkeypatch, ["1"], lambda o, i: first)
    history = _run_main(tmp_path, monkeypatch, ["1"], lambda o, i: second)
    assert history["funds"]["1"]["points"] == _pts((1, 1.0), (2, 1.1), (3, 1.25), (4, 1.3))


def test_failed_fund_keeps_stored_entry_and_removed_fund_is_dropped(tmp_path, monkeypatch):
    stored = {
        "1": _entry(_pts((1, 1.0), (2, 1.1)), stale=True),
        "2": _entry(_pts((1, 5.0))),
        "gone": _entry(_pts((1, 7.0))),
    }
    (tmp_path / "nav-history.json").write_text(
        json.dumps({"generated_at": "t", "funds": stored}), encoding="utf-8"
    )

    def fetch(opener, fund_id):
        if fund_id == "1":
            raise RuntimeError("source unavailable")
        return _series([(2, 5.5)])

    history = _run_main(tmp_path, monkeypatch, ["1", "2"], fetch)
    assert history["funds"]["1"] == stored["1"]
    assert history["funds"]["2"] == _entry(_pts((1, 5.0), (2, 5.5)))
    assert "gone" not in history["funds"]
