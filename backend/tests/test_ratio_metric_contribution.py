from datetime import date
from app.agents import dimension_explorer
from app.agents.common import AgentDeps
from app.config import Settings
from conftest import FakeLLM, FakeTrace, FakeTracer


class RatioFakeRepo:
    def dimension_breakdown(self, dimension: str, target_date: date, baseline_days: int):
        actual = [
            {"device_model": "HighVolumeStable", "os_version": "x",
             "requests": 100_000, "fills": 80_000, "impressions": 78_000, "clicks": 800, "revenue": 800.0,
             "fill_rate": 0.8, "ctr": 0.01, "ecpm": 10.0},
            {"device_model": "LowVolumeCollapsed", "os_version": "y",
             "requests": 10_000, "fills": 4_000, "impressions": 3_900, "clicks": 40, "revenue": 40.0,
             "fill_rate": 0.4, "ctr": 0.01, "ecpm": 10.0},
        ]
        baseline = [
            {"device_model": "HighVolumeStable", "os_version": "x",
             "requests": 62_500, "fills": 50_000, "impressions": 48_750, "clicks": 500, "revenue": 500.0,
             "fill_rate": 0.8, "ctr": 0.01, "ecpm": 10.0},
            {"device_model": "LowVolumeCollapsed", "os_version": "y",
             "requests": 10_000, "fills": 8_000, "impressions": 7_800, "clicks": 80, "revenue": 80.0,
             "fill_rate": 0.8, "ctr": 0.01, "ecpm": 10.0},
        ]
        return actual, baseline, "SELECT ... device"


def _deps():
    return AgentDeps(
        settings=Settings(), repo=RatioFakeRepo(), llm=FakeLLM(), tracer=FakeTracer(), langfuse_trace=FakeTrace(),
    )


def _state(metric: str):
    return {
        "metric": metric,
        "target_date": date(2026, 1, 15),
        "baseline_days": 7,
        "agent_log": [],
        "ruled_out": [],
        "dimensions_to_check": ["device"],
        "dimensions_checked": [],
        "explorations": [],
        "flagged_dimensions": [],
        "_actual_overall": {"fills": 84_000, "clicks": 840, "revenue": 840.0},
        "_baseline_overall": {"fills": 58_000, "clicks": 580, "revenue": 580.0},
    }


def test_ratio_metric_ranks_by_own_rate_deviation_not_absolute_volume():
    state = dimension_explorer.run(_state("fill_rate"), _deps())
    exp = state["explorations"][0]

    assert exp["top_contributor"]["value"] == "LowVolumeCollapsed"
    assert exp["top_contributor"]["share_of_total_delta_pct"] == -50.0
    assert exp["is_significant"] is True 


def test_ratio_metric_baseline_and_actual_are_rates_not_raw_counts():
    state = dimension_explorer.run(_state("fill_rate"), _deps())
    top = state["explorations"][0]["top_contributor"]
    assert top["baseline_metric"] == 0.8
    assert top["actual_metric"] == 0.4


def test_count_metric_path_is_unchanged_ranks_by_absolute_delta():
    """revenue is a count metric - HighVolumeStable's absolute revenue delta
    (+300) dwarfs LowVolumeCollapsed's (-40), so it should still win, exactly
    as before this fix (no ratio branch involved)."""
    state = dimension_explorer.run(_state("revenue"), _deps())
    top = state["explorations"][0]["top_contributor"]
    assert top["value"] == "HighVolumeStable"
    assert top["delta"] == 300.0
