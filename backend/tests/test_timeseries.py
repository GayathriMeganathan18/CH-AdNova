import pytest
from app.analytics.timeseries import build_timeseries


def test_24h_window_returns_the_hourly_series(deps, base_state):
    result = build_timeseries(deps.repo, "revenue", base_state["target_date"], "24h")
    assert result["window"] == "24h"
    assert len(result["labels"]) == 24
    assert result["values"][0] == pytest.approx(10.0)
    assert result["values"][-1] == pytest.approx(33.0)
    assert result["forecast_values"] == []


def test_7d_window_uses_daily_series(deps, base_state):
    result = build_timeseries(deps.repo, "revenue", base_state["target_date"], "7d")
    assert len(result["labels"]) == 7
    assert len(result["values"]) == 7


def test_30d_window_uses_daily_series(deps, base_state):
    result = build_timeseries(deps.repo, "revenue", base_state["target_date"], "30d")
    assert len(result["labels"]) == 30


def test_forecast_extrapolates_the_exact_linear_trend(deps, base_state):
    result = build_timeseries(deps.repo, "revenue", base_state["target_date"], "24h", forecast_points=3)
    # y = 1.0 * hour + 10.0 exactly - least squares on a perfect line
    # recovers that slope/intercept exactly, so hour 24/25/26 -> 34/35/36.
    assert result["forecast_values"] == pytest.approx([34.0, 35.0, 36.0])
    assert len(result["forecast_labels"]) == 3


def test_forecast_defaults_to_empty_when_not_requested(deps, base_state):
    result = build_timeseries(deps.repo, "revenue", base_state["target_date"], "7d")
    assert result["forecast_values"] == []
    assert result["forecast_labels"] == []


def test_unsupported_metric_rejected(deps, base_state):
    with pytest.raises(ValueError):
        build_timeseries(deps.repo, "not_a_metric", base_state["target_date"], "7d")


def test_app_id_filter_routes_to_filtered_daily_series(deps, base_state):
    result = build_timeseries(deps.repo, "revenue", base_state["target_date"], "7d", app_id="app_00000")
    assert "filtered" in result["sql"]
    assert len(result["values"]) == 7


def test_region_filter_routes_to_filtered_hourly_series_for_24h(deps, base_state):
    result = build_timeseries(deps.repo, "revenue", base_state["target_date"], "24h", region="NAM")
    assert "filtered" in result["sql"]
    assert len(result["values"]) == 24


def test_no_filters_uses_unfiltered_series(deps, base_state):
    result = build_timeseries(deps.repo, "revenue", base_state["target_date"], "7d")
    assert "filtered" not in result["sql"]


def test_unsupported_window_rejected(deps, base_state):
    with pytest.raises(ValueError):
        build_timeseries(deps.repo, "revenue", base_state["target_date"], "3d")


def test_flat_series_forecast_carries_the_last_value_forward():
    from app.analytics.timeseries import _linear_forecast
    assert _linear_forecast([5.0], 3) == [5.0, 5.0, 5.0]
    assert _linear_forecast([], 2) == [0.0, 0.0]
