import pytest
from app.analytics.anomaly import DEFAULT_THRESHOLDS, detect_anomaly
from app.analytics.baseline import compute_baseline


@pytest.fixture
def repo(deps):
    return deps.repo


def test_rolling_mean_baseline_matches_known_window_mean(repo, base_state):
    result = compute_baseline(repo, "revenue", base_state["target_date"], 7, strategy="rolling_mean")
    assert result.expected == pytest.approx(10_000.0)
    assert result.actual == 8_000.0
    assert result.deviation_pct == pytest.approx(-20.0)
    assert result.severity == "high"
    assert 0.0 < result.confidence <= 0.95


def test_rolling_median_baseline(repo, base_state):
    result = compute_baseline(repo, "revenue", base_state["target_date"], 7, strategy="rolling_median")
    assert result.expected == pytest.approx(10_000.0)


def test_ewma_baseline_is_close_to_window_mean(repo, base_state):
    result = compute_baseline(repo, "revenue", base_state["target_date"], 7, strategy="ewma")
    assert result.expected == pytest.approx(10_000.0, abs=50)


def test_week_over_week_and_day_over_day_use_overall_daily(repo, base_state):
    wow = compute_baseline(repo, "revenue", base_state["target_date"], 7, strategy="week_over_week")
    dod = compute_baseline(repo, "revenue", base_state["target_date"], 7, strategy="day_over_day")
    assert wow.deviation_pct == 0.0
    assert dod.deviation_pct == 0.0
    assert wow.severity == "none"


def test_unsupported_metric_rejected(repo, base_state):
    with pytest.raises(ValueError):
        compute_baseline(repo, "not_a_metric", base_state["target_date"], 7)


def test_unsupported_strategy_rejected(repo, base_state):
    with pytest.raises(ValueError):
        compute_baseline(repo, "revenue", base_state["target_date"], 7, strategy="not_a_strategy")


def test_pct_deviation_anomaly_detects_the_20pct_drop(repo, base_state):
    result = detect_anomaly(repo, "revenue", base_state["target_date"], 7, strategy="pct_deviation")
    assert result.is_anomalous is True
    assert result.score == pytest.approx(-20.0)
    assert result.severity == "high"
    assert result.threshold == DEFAULT_THRESHOLDS["pct_deviation"]


def test_zscore_anomaly_detects_the_drop(repo, base_state):
    result = detect_anomaly(repo, "revenue", base_state["target_date"], 7, strategy="zscore")
    assert result.is_anomalous is True
    assert result.score < -10  # far outside a ~122-unit stdev window


def test_rolling_std_anomaly_detects_the_drop(repo, base_state):
    result = detect_anomaly(repo, "revenue", base_state["target_date"], 7, strategy="rolling_std")
    assert result.is_anomalous is True
    assert result.severity in ("medium", "high")


def test_iqr_anomaly_detects_the_drop(repo, base_state):
    result = detect_anomaly(repo, "revenue", base_state["target_date"], 7, strategy="iqr")
    assert result.is_anomalous is True


def test_anomaly_result_carries_its_baseline_for_evidence(repo, base_state):
    result = detect_anomaly(repo, "revenue", base_state["target_date"], 7, strategy="pct_deviation")
    assert result.baseline.metric == "revenue"
    assert result.baseline.sql  
    d = result.to_dict()
    assert d["baseline"]["expected"] == pytest.approx(10_000.0)


def test_flat_metric_with_no_deviation_is_not_anomalous(repo, base_state):
    result = detect_anomaly(repo, "requests", base_state["target_date"], 7, strategy="pct_deviation")
    assert result.is_anomalous is False
    assert result.severity == "none"
