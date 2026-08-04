import sys
from datetime import date, timedelta
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.agents.common import AgentDeps
from app.config import Settings


class FakeRepo:
    def overall_daily(self, day: date):
        return {
            "requests": 100_000, "fills": 40_000, "impressions": 38_000,
            "clicks": 760, "revenue": 8_000.0,
            "fill_rate": 0.4, "ctr": 0.02, "ecpm": 210.5,
        }, "SELECT ... overall_daily"

    def overall_baseline(self, target_date: date, baseline_days: int):
        return {
            "requests": 100_000, "fills": 50_000, "impressions": 48_000,
            "clicks": 960, "revenue": 10_000.0,
            "fill_rate": 0.5, "ctr": 0.02, "ecpm": 208.3,
        }, "SELECT ... overall_baseline"

    def daily_series(self, start: date, end: date):
        revenue_by_offset = [9_800.0, 10_100.0, 9_950.0, 10_050.0, 9_900.0, 10_200.0, 10_000.0]
        rows = []
        d = start
        i = 0
        while d <= end:
            revenue = revenue_by_offset[i % len(revenue_by_offset)]
            rows.append({
                "day": str(d),
                "requests": 100_000, "fills": 50_000, "impressions": 48_000,
                "clicks": 960, "revenue": revenue,
                "fill_rate": 0.5, "ctr": 0.02, "ecpm": 208.3,
            })
            d += timedelta(days=1)
            i += 1
        return rows, "SELECT ... daily_series"

    def hourly_series(self, start_date: date, end_date: date):
        rows = []
        for h in range(24):
            rows.append({
                "hour": f"{start_date} {h:02d}:00:00",
                "requests": 5_000, "fills": 2_500, "impressions": 2_400,
                "clicks": 48, "revenue": 10.0 + h,
                "fill_rate": 0.5, "ctr": 0.02, "ecpm": 208.3,
            })
        return rows, "SELECT ... hourly_series"

    def data_date_range(self):
        return date(2026, 1, 1), date(2026, 1, 15)

    def filtered_daily_series(self, start: date, end: date, app_id=None, region=None, publisher_tier=None):
        rows, sql = self.daily_series(start, end)
        return rows, sql.replace("SELECT ...", "SELECT ... filtered")

    def filtered_hourly_series(self, start_date: date, end_date: date, app_id=None, region=None, publisher_tier=None):
        rows, sql = self.hourly_series(start_date, end_date)
        return rows, sql.replace("SELECT ...", "SELECT ... filtered")

    def filtered_overall_range(self, start: date, end: date, app_id=None, region=None, publisher_tier=None, divide_by=1):
        return self.overall_baseline(end, divide_by)

    def dimension_breakdown(self, dimension: str, target_date: date, baseline_days: int):
        if dimension == "device":
            actual = [
                {"device_model": "Galaxy A54", "os_version": "Android 14",
                 "requests": 30_000, "fills": 6_000, "impressions": 5_800, "clicks": 100, "revenue": 1_000.0,
                 "fill_rate": 0.2, "ctr": 0.017, "ecpm": 172.4},
                {"device_model": "iPhone 15", "os_version": "iOS 18.1",
                 "requests": 30_000, "fills": 17_000, "impressions": 16_500, "clicks": 350, "revenue": 3_500.0,
                 "fill_rate": 0.567, "ctr": 0.021, "ecpm": 212.1},
            ]
            baseline = [
                {"device_model": "Galaxy A54", "os_version": "Android 14",
                 "requests": 30_000, "fills": 15_000, "impressions": 14_500, "clicks": 290, "revenue": 3_000.0,
                 "fill_rate": 0.5, "ctr": 0.02, "ecpm": 206.9},
                {"device_model": "iPhone 15", "os_version": "iOS 18.1",
                 "requests": 30_000, "fills": 17_000, "impressions": 16_500, "clicks": 350, "revenue": 3_500.0,
                 "fill_rate": 0.567, "ctr": 0.021, "ecpm": 212.1},
            ]
            return actual, baseline, "SELECT ... by_device"
        # every other dimension: flat / unchanged -> should be ruled out
        actual = [{"app_id": "app_00001" if dimension == "app" else "x",
                   "app_category": "gaming", "publisher_tier": "tier_1",
                   "advertiser_id": "adv_0001", "vertical": "auto", "campaign_type": "CPM",
                   "country": "US", "region": "NAM",
                   "ad_format": "banner",
                   "requests": 50_000, "fills": 20_000, "impressions": 19_000, "clicks": 380, "revenue": 4_000.0,
                   "fill_rate": 0.4, "ctr": 0.02, "ecpm": 210.5}]
        baseline = [dict(actual[0])]
        return actual, baseline, f"SELECT ... by_{dimension}"

    def filtered_dimension_breakdown(self, dimension: str, target_date: date, baseline_days: int, filter_column: str, filter_value: str):
        if filter_value == "Galaxy A54" and dimension == "geo":
            actual = [
                {"country": "IN", "region": "APAC",
                 "requests": 20_000, "fills": 4_000, "impressions": 3_800, "clicks": 60, "revenue": 600.0,
                 "fill_rate": 0.2, "ctr": 0.016, "ecpm": 157.9},
                {"country": "US", "region": "NAM",
                 "requests": 10_000, "fills": 2_000, "impressions": 2_000, "clicks": 40, "revenue": 400.0,
                 "fill_rate": 0.2, "ctr": 0.02, "ecpm": 200.0},
            ]
            baseline = [
                {"country": "IN", "region": "APAC",
                 "requests": 20_000, "fills": 10_000, "impressions": 9_500, "clicks": 190, "revenue": 2_000.0,
                 "fill_rate": 0.5, "ctr": 0.02, "ecpm": 210.5},
                {"country": "US", "region": "NAM",
                 "requests": 10_000, "fills": 5_000, "impressions": 5_000, "clicks": 100, "revenue": 1_000.0,
                 "fill_rate": 0.5, "ctr": 0.02, "ecpm": 200.0},
            ]
            return actual, baseline, "SELECT ... filtered_geo_within_device"

        actual = [{"country": "x", "region": "x", "os_version": "x", "app_id": "x",
                   "publisher_tier": "x", "ad_format": "x", "device_model": "x",
                   "requests": 1_000, "fills": 500, "impressions": 480, "clicks": 10, "revenue": 100.0,
                   "fill_rate": 0.5, "ctr": 0.02, "ecpm": 208.3}]
        baseline = [dict(actual[0])]
        return actual, baseline, f"SELECT ... filtered_{dimension}"

    def overall_excluding_segment(self, dimension: str, value: str, target_date: date):
        return {
            "requests": 70_000, "fills": 34_000, "impressions": 32_200,
            "clicks": 660, "revenue": 7_000.0,
            "fill_rate": 0.486, "ctr": 0.0205, "ecpm": 217.4,
        }, "SELECT ... excluding_segment"

    def counterfactual_revenue(self, dimension, value, target_date, baseline_fill_rate, baseline_ctr):
        return {
            "actual_total_revenue": 8_000.0,
            "projected_total_revenue": 9_500.0,
            "recovered_value": 1_500.0,
        }, "SELECT ... counterfactual"


class FakeLLM:
    enabled = False

    def complete(self, system: str, prompt: str, max_tokens: int = 500) -> str:
        return f"fake completion for: {prompt[:40]}"

    def complete_messages(self, system: str, messages: list[dict], max_tokens: int = 700) -> str:
        last = messages[-1]["content"] if messages else ""
        return f"fake conversation reply for: {last[:40]}"


class FailingFakeLLM(FakeLLM):
    enabled = True

    def complete(self, system: str, prompt: str, max_tokens: int = 500) -> str:
        raise RuntimeError("simulated LLM outage")

    def complete_messages(self, system: str, messages: list[dict], max_tokens: int = 700) -> str:
        raise RuntimeError("simulated LLM outage")


class WorkingFakeLLM(FakeLLM):
    enabled = True


class FakeTracerSpan:
    def update(self, **kwargs):
        pass


class FakeTrace:
    def update(self, **kwargs):
        pass

    def span(self, **kwargs):
        return FakeTracerSpan()


class FakeTracer:
    def __init__(self):
        self.generations = []  

    def agent_span(self, trace, agent_name, input_data):
        from contextlib import contextmanager

        @contextmanager
        def _cm():
            yield FakeTracerSpan()

        return _cm()

    def llm_generation(self, trace, name, model, system, prompt, completion, error=None):
        self.generations.append((name, model, system, prompt, completion, error))

    def flush(self):
        pass


@pytest.fixture
def deps():
    return AgentDeps(
        settings=Settings(),
        repo=FakeRepo(),
        llm=FakeLLM(),
        tracer=FakeTracer(),
        langfuse_trace=FakeTrace(),
    )


@pytest.fixture
def base_state():
    return {
        "metric": "revenue",
        "target_date": date(2026, 1, 15),
        "baseline_days": 7,
        "agent_log": [],
        "ruled_out": [],
    }
