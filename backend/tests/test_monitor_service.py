from dataclasses import dataclass, field
from app.services.monitor_service import MONITORED_METRICS, run_cycle

class FakeAnomalyStore:
    def __init__(self):
        self._data: dict[str, dict] = {}

    def get(self, anomaly_id):
        return self._data.get(anomaly_id)

    def save(self, anomaly_id, record):
        self._data[anomaly_id] = dict(record)

    def attach_investigation(self, anomaly_id, investigation_id, root_cause_summary, executive_summary):
        self._data[anomaly_id].update({
            "investigation_id": investigation_id,
            "root_cause_summary": root_cause_summary,
            "executive_summary": executive_summary,
            "status": "investigated",
        })


@dataclass
class _FakeInvestigationResult:
    investigation_id: str
    root_causes: list = field(default_factory=list)
    executive_summary: str = "synthetic summary"


class FakeInvestigationService:
    def __init__(self):
        self.calls = []

    def run_investigation(self, request):
        self.calls.append(request)
        return _FakeInvestigationResult(investigation_id=f"inv-{len(self.calls)}")


def test_run_cycle_flags_exactly_the_anomalous_metrics(deps, base_state):
    store = FakeAnomalyStore()
    inv_service = FakeInvestigationService()

    summary = run_cycle(deps.repo, store, inv_service, deps.settings)

    assert {e["metric"] for e in summary} == set(MONITORED_METRICS)
    anomalous = {e["metric"] for e in summary if e["is_anomalous"]}
    assert anomalous == {"revenue", "fill_rate", "impressions", "clicks"}
    assert len(inv_service.calls) == 4
    assert all(e["triggered"] for e in summary if e["is_anomalous"])


def test_run_cycle_is_idempotent_on_repeated_ticks(deps, base_state):
    """The critical dedup guarantee: a static dataset re-checked on every
    tick must not spawn a new investigation each time."""
    store = FakeAnomalyStore()
    inv_service = FakeInvestigationService()

    run_cycle(deps.repo, store, inv_service, deps.settings)
    assert len(inv_service.calls) == 4

    second = run_cycle(deps.repo, store, inv_service, deps.settings)
    assert len(inv_service.calls) == 4  

    already_flagged = [e for e in second if e["is_anomalous"]]
    assert all(e.get("already_alerted") for e in already_flagged)
    assert all(not e["triggered"] for e in already_flagged)


def test_run_cycle_persists_alert_with_root_cause(deps, base_state):
    store = FakeAnomalyStore()
    inv_service = FakeInvestigationService()

    run_cycle(deps.repo, store, inv_service, deps.settings)

    revenue_records = [r for r in store._data.values() if r["metric"] == "revenue"]
    assert len(revenue_records) == 1
    record = revenue_records[0]
    assert record["status"] == "investigated"
    assert record["source"] == "scheduler"
    assert record["investigation_id"].startswith("inv-")
    assert "No concentrated root cause" in record["root_cause_summary"]


def test_run_cycle_handles_missing_data_gracefully():
    class EmptyRepo:
        def data_date_range(self):
            return None, None

    from app.config import Settings
    summary = run_cycle(EmptyRepo(), FakeAnomalyStore(), FakeInvestigationService(), Settings())
    assert summary == []
