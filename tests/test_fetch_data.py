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
    empty_metrics,
    fetch_fund_series,
    iso_last_date,
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


def test_main_drops_bad_closes_before_metrics_and_writes_strict_funds_json(tmp_path, monkeypatch):
    import fetch_data

    start = date(2021, 1, 1)
    days = [(start + timedelta(days=i)).isoformat() for i in range(1300)]
    negative_tail = [{"date": day, "close": 100.0 + i} for i, day in enumerate(days)]
    negative_tail[-1]["close"] = -5.0
    with_nan = [{"date": day, "close": 100.0 + i} for i, day in enumerate(days)]
    with_nan[600]["close"] = float("nan")
    series_by_id = {"1": negative_tail, "2": with_nan}

    config = tmp_path / "funds_config.json"
    config.write_text(json.dumps({"funds": [{"id": "1"}, {"id": "2"}]}), encoding="utf-8")
    monkeypatch.setattr(fetch_data, "FUNDS_CONFIG", config)
    monkeypatch.setattr(fetch_data, "OUTPUT", tmp_path / "funds.json")
    monkeypatch.setattr(fetch_data, "NAV_HISTORY", tmp_path / "nav-history.json")
    monkeypatch.setattr(fetch_data, "build_opener", lambda: None)
    monkeypatch.setattr(
        fetch_data, "fetch_fund_series", lambda opener, fund_id: series_by_id[fund_id]
    )
    fetch_data.main()

    funds = json.loads(
        (tmp_path / "funds.json").read_text(encoding="utf-8"), parse_constant=_reject_constant
    )["funds"]
    assert all(fund["stale"] is False for fund in funds)

    history = json.loads(
        (tmp_path / "nav-history.json").read_text(encoding="utf-8"),
        parse_constant=_reject_constant,
    )["funds"]
    assert days[-1] not in [point[0] for point in history["1"]["points"]]
    assert days[600] not in [point[0] for point in history["2"]["points"]]


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


def _configure(tmp_path, monkeypatch, config_ids, fetch):
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
    return fetch_data


def _run_main(tmp_path, monkeypatch, config_ids, fetch):
    _configure(tmp_path, monkeypatch, config_ids, fetch).main()
    return json.loads((tmp_path / "nav-history.json").read_text(encoding="utf-8"))


def _series(pairs):
    return [{"date": f"2026-01-0{d}", "close": c} for d, c in pairs]


def test_two_runs_keep_every_date_from_the_first(tmp_path, monkeypatch):
    first = _series([(1, 1.0), (2, 1.1), (3, 1.2)])
    second = _series([(3, 1.25), (4, 1.3)])
    _run_main(tmp_path, monkeypatch, ["1"], lambda o, i: first)
    history = _run_main(tmp_path, monkeypatch, ["1"], lambda o, i: second)
    assert history["funds"]["1"]["points"] == _pts((1, 1.0), (2, 1.1), (3, 1.25), (4, 1.3))




def _fail(opener, fund_id):
    raise RuntimeError("source unavailable")


def _fetch_failing(*failing, ok=None):
    def fetch(opener, fund_id):
        if fund_id in failing:
            raise RuntimeError("source unavailable")
        return ok

    return fetch


def _store(tmp_path, history=None, funds=None):
    if history is not None:
        (tmp_path / "nav-history.json").write_text(
            json.dumps({"generated_at": "t", "funds": history}), encoding="utf-8"
        )
    if funds is not None:
        (tmp_path / "funds.json").write_text(
            json.dumps({"generated_at": "t", "funds": funds}), encoding="utf-8"
        )


def _read_funds(tmp_path):
    funds = json.loads((tmp_path / "funds.json").read_text(encoding="utf-8"))["funds"]
    return {f["id"]: f for f in funds}


def _previous_fund(fund_id, last_date="2026-01-02", **metrics):
    return {
        "id": fund_id,
        "metrics": {**empty_metrics(), "last_date": last_date, **metrics},
        "stale": False,
    }


def test_empty_metrics_has_the_keys_compute_metrics_produces():
    computed = compute_metrics(make_series([100.0, 101.0]))
    assert set(empty_metrics()) == set(computed)
    assert all(value is None for value in empty_metrics().values())


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-10-22", "2026-10-22"),
        ("22/10/2026", "2026-10-22"),
        ("2026-1-5", None),
        ("garbage", None),
        ("31/02/2026", None),
        (None, None),
        (20261022, None),
    ],
)
def test_iso_last_date(value, expected):
    assert iso_last_date(value) == expected


def test_payload_writes_failed_fund_stale_with_previous_points():
    previous = {"1": _entry(_pts((1, 1.0)))}
    payload = nav_history_payload({}, "t", previous, ["1"])
    assert payload["funds"] == {"1": _entry(_pts((1, 1.0)), stale=True)}


def test_payload_writes_failed_fund_without_previous_points_empty():
    assert nav_history_payload({}, "t", {}, ["1"])["funds"] == {"1": _entry([], stale=True)}


def test_payload_drops_funds_that_are_neither_fetched_nor_failed():
    previous = {"gone": _entry(_pts((1, 1.0)))}
    assert nav_history_payload({}, "t", previous)["funds"] == {}


def test_failed_fund_with_previous_data_stays_stale_with_its_points(tmp_path, monkeypatch, capsys):
    _store(
        tmp_path,
        history={"1": _entry(_pts((1, 1.0), (2, 1.1))), "gone": _entry(_pts((1, 7.0)))},
        funds=[_previous_fund("1", return_1m=0.5), _previous_fund("2")],
    )
    history = _run_main(
        tmp_path, monkeypatch, ["1", "2"], _fetch_failing("1", ok=_series([(2, 5.5)]))
    )

    assert history["funds"]["1"] == _entry(_pts((1, 1.0), (2, 1.1)), stale=True)
    assert history["funds"]["2"] == _entry(_pts((2, 5.5)))
    assert "gone" not in history["funds"]
    funds = _read_funds(tmp_path)
    assert funds["1"]["stale"] is True
    assert funds["1"]["metrics"]["return_1m"] == 0.5
    assert funds["2"]["stale"] is False
    err = capsys.readouterr().err
    assert "Failed to fetch fund 1" in err
    assert "fund 1 has no" not in err


def test_failed_fund_with_no_previous_data_is_listed_empty_and_warned(
    tmp_path, monkeypatch, capsys
):
    import fetch_data

    start = date(2026, 1, 1)
    scored = [
        {"date": (start + timedelta(days=i)).isoformat(), "close": 100.0 * (1.002 if i % 2 else 0.999) ** i}
        for i in range(200)
    ]
    history = _run_main(tmp_path, monkeypatch, ["1", "2"], _fetch_failing("2", ok=scored))

    assert history["funds"]["2"] == _entry([], stale=True)
    assert _read_funds(tmp_path)["1"]["metrics"]["risk_adjusted_score"] is not None
    funds = _read_funds(tmp_path)
    assert funds["2"]["stale"] is True
    assert funds["2"]["metrics"] == empty_metrics()
    assert funds["2"]["suggested_weight"] == fetch_data.MIN_WEIGHT
    assert math.isclose(sum(f["suggested_weight"] for f in funds.values()), 1.0)
    assert "fund 2 has no previous metrics and no stored points" in capsys.readouterr().err


def test_failed_fund_keeps_previous_score_rank_and_weight(tmp_path, monkeypatch):
    import fetch_data

    start = date(2026, 1, 1)
    scored = [
        {"date": (start + timedelta(days=i)).isoformat(), "close": 100.0 * (1.002 if i % 2 else 0.999) ** i}
        for i in range(200)
    ]
    _store(
        tmp_path,
        history={"1": _entry(_pts((1, 1.0)))},
        funds=[_previous_fund("1", risk_adjusted_score=1e6), _previous_fund("2")],
    )
    _run_main(tmp_path, monkeypatch, ["1", "2"], _fetch_failing("1", ok=scored))

    written = json.loads((tmp_path / "funds.json").read_text(encoding="utf-8"))["funds"]
    assert [f["id"] for f in written] == ["1", "2"]
    assert written[0]["metrics"]["risk_adjusted_score"] == 1e6
    assert written[0]["suggested_weight"] > fetch_data.MIN_WEIGHT


def test_failed_fund_with_metrics_only_keeps_them_and_warns_about_points(
    tmp_path, monkeypatch, capsys
):
    _store(tmp_path, funds=[_previous_fund("1", return_1m=0.5), _previous_fund("2")])
    history = _run_main(
        tmp_path, monkeypatch, ["1", "2"], _fetch_failing("1", ok=_series([(1, 1.0), (2, 1.1)]))
    )

    assert history["funds"]["1"] == _entry([], stale=True)
    assert _read_funds(tmp_path)["1"]["metrics"]["return_1m"] == 0.5
    err = capsys.readouterr().err
    assert "fund 1 has no stored points" in err
    assert "previous metrics" not in err


def test_failed_fund_with_points_only_keeps_them_and_warns_about_metrics(
    tmp_path, monkeypatch, capsys
):
    _store(tmp_path, history={"1": _entry(_pts((1, 1.0)))})
    history = _run_main(
        tmp_path, monkeypatch, ["1", "2"], _fetch_failing("1", ok=_series([(1, 1.0), (2, 1.1)]))
    )

    assert history["funds"]["1"] == _entry(_pts((1, 1.0)), stale=True)
    assert _read_funds(tmp_path)["1"]["metrics"] == empty_metrics()
    err = capsys.readouterr().err
    assert "fund 1 has no previous metrics" in err
    assert "stored points" not in err


@pytest.mark.parametrize(
    ("previous_date", "expected"),
    [("22/10/2026", "2026-10-22"), ("2026-10-22", "2026-10-22"), ("soon", None)],
)
def test_failed_fund_last_date_is_written_as_iso_or_null(
    tmp_path, monkeypatch, previous_date, expected
):
    _store(
        tmp_path,
        history={"1": _entry(_pts((1, 1.0)))},
        funds=[_previous_fund("1", last_date=previous_date), _previous_fund("2")],
    )
    _run_main(tmp_path, monkeypatch, ["1", "2"], _fetch_failing("1", ok=_series([(1, 1.0)])))
    assert _read_funds(tmp_path)["1"]["metrics"]["last_date"] == expected


def test_every_fetch_failing_exits_1_and_leaves_existing_files_untouched(tmp_path, monkeypatch):
    _store(
        tmp_path,
        history={"1": _entry(_pts((1, 1.0)))},
        funds=[_previous_fund("1", last_date="22/10/2026")],
    )
    names = ("funds.json", "nav-history.json")
    before = {name: (tmp_path / name).read_bytes() for name in names}
    fetch_data = _configure(tmp_path, monkeypatch, ["1"], _fail)

    with pytest.raises(SystemExit) as exc:
        fetch_data.main()

    assert isinstance(exc.value.code, str)
    assert {name: (tmp_path / name).read_bytes() for name in names} == before


def test_every_fetch_failing_with_no_previous_files_creates_none(tmp_path, monkeypatch):
    fetch_data = _configure(tmp_path, monkeypatch, ["1", "2"], _fail)

    with pytest.raises(SystemExit) as exc:
        fetch_data.main()

    assert isinstance(exc.value.code, str)
    assert not (tmp_path / "funds.json").exists()
    assert not (tmp_path / "nav-history.json").exists()


def test_stale_fund_recovers_on_the_next_successful_fetch(tmp_path, monkeypatch):
    _store(
        tmp_path,
        history={"1": _entry(_pts((1, 1.0)), stale=True)},
        funds=[{**_previous_fund("1"), "stale": True}],
    )
    history = _run_main(tmp_path, monkeypatch, ["1"], lambda o, i: _series([(2, 1.1)]))

    assert history["funds"]["1"] == _entry(_pts((1, 1.0), (2, 1.1)))
    assert _read_funds(tmp_path)["1"]["stale"] is False


def test_both_files_list_every_configured_fund_with_the_same_stale_flag(tmp_path, monkeypatch):
    _store(tmp_path, history={"1": _entry(_pts((1, 1.0)))}, funds=[_previous_fund("1")])
    history = _run_main(
        tmp_path, monkeypatch, ["1", "2", "3"], _fetch_failing("1", "2", ok=_series([(1, 1.0)]))
    )
    funds = _read_funds(tmp_path)
    assert set(funds) == set(history["funds"]) == {"1", "2", "3"}
    assert all(funds[i]["stale"] == history["funds"][i]["stale"] for i in funds)


def _ok_series():
    return _series([(1, 1.0), (2, 1.1)])


def _leftover_temps(tmp_path):
    return sorted(p.name for p in tmp_path.glob("*.tmp"))


def test_main_moves_history_before_fund_list_and_leaves_no_temp(tmp_path, monkeypatch):
    import fetch_data

    moved = []
    real_replace = fetch_data.os.replace
    monkeypatch.setattr(
        fetch_data.os, "replace", lambda src, dst: moved.append(Path(dst).name) or real_replace(src, dst)
    )
    _run_main(tmp_path, monkeypatch, ["1"], lambda o, i: _ok_series())

    assert moved == ["nav-history.json", "funds.json"]
    assert _leftover_temps(tmp_path) == []


def test_unserialisable_history_writes_neither_file(tmp_path, monkeypatch):
    _store(tmp_path, history={"1": _entry(_pts((1, 1.0)))}, funds=[_previous_fund("1")])
    names = ("funds.json", "nav-history.json")
    before = {name: (tmp_path / name).read_bytes() for name in names}
    fetch_data = _configure(tmp_path, monkeypatch, ["1"], lambda o, i: _ok_series())
    monkeypatch.setattr(
        fetch_data, "nav_history_payload", lambda *a, **k: {"funds": {"1": float("nan")}}
    )

    with pytest.raises(ValueError):
        fetch_data.main()

    assert {name: (tmp_path / name).read_bytes() for name in names} == before
    assert _leftover_temps(tmp_path) == []


def test_failed_temp_write_replaces_nothing_and_removes_temps(tmp_path):
    import fetch_data

    first, second = tmp_path / "a.json", tmp_path / "b.json"
    first.write_text("old", encoding="utf-8")

    with pytest.raises(TypeError):
        fetch_data.write_files_atomically([(first, "new"), (second, None)])

    assert first.read_text(encoding="utf-8") == "old"
    assert not second.exists()
    assert _leftover_temps(tmp_path) == []


def test_failed_fund_list_move_leaves_new_history_old_funds_and_no_temp(tmp_path, monkeypatch):
    import fetch_data

    _store(tmp_path, history={"1": _entry(_pts((1, 1.0)))}, funds=[_previous_fund("1")])
    old_funds = (tmp_path / "funds.json").read_bytes()
    old_history = (tmp_path / "nav-history.json").read_bytes()
    real_replace = fetch_data.os.replace

    def replace(src, dst):
        if Path(dst).name == "funds.json":
            raise OSError("disk gone")
        real_replace(src, dst)

    main = _configure(tmp_path, monkeypatch, ["1"], lambda o, i: _ok_series())
    monkeypatch.setattr(fetch_data.os, "replace", replace)

    with pytest.raises(OSError):
        main.main()

    assert (tmp_path / "funds.json").read_bytes() == old_funds
    assert (tmp_path / "nav-history.json").read_bytes() != old_history
    assert _leftover_temps(tmp_path) == []


REPO = Path(__file__).resolve().parent.parent


def _lines_naming(path, needle):
    return [
        line
        for line in (REPO / path).read_text(encoding="utf-8").splitlines()
        if needle in line
    ]


@pytest.mark.parametrize(
    "path", [".github/workflows/update-data.yml", ".claude/skills/add-fund/SKILL.md"]
)
def test_every_line_staging_funds_json_also_stages_nav_history(path):
    lines = _lines_naming(path, "data/funds.json")
    assert lines
    assert all("data/nav-history.json" in line for line in lines)


def test_workflow_pulls_with_rebase_before_a_push_that_is_not_swallowed():
    text = (REPO / ".github/workflows/update-data.yml").read_text(encoding="utf-8")
    assert "git pull --rebase" in text
    assert text.index("git pull --rebase") < text.index("git push")
    assert all("||" not in line for line in _lines_naming(".github/workflows/update-data.yml", "git push"))


def test_workflow_serialises_runs_and_fetches_before_it_commits():
    lines = (REPO / ".github/workflows/update-data.yml").read_text(encoding="utf-8").splitlines()
    assert "concurrency:" in lines
    assert "  group: update-data" in lines
    assert "  cancel-in-progress: false" in lines
    fetch = next(i for i, line in enumerate(lines) if "scripts/fetch_data.py" in line)
    stage = next(i for i, line in enumerate(lines) if "git add data/" in line)
    assert fetch < stage


def test_commit_step_never_swallows_a_failure():
    text = (REPO / ".github/workflows/update-data.yml").read_text(encoding="utf-8")
    assert "continue-on-error" not in text
    assert "set +e" not in text
