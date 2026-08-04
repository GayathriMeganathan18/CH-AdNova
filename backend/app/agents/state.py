from datetime import date, datetime
from typing import Any, TypedDict

DIMENSION_ORDER = ["device", "geo", "app", "advertiser", "format"]

class InvestigationState(TypedDict, total=False):
    investigation_id: str
    metric: str
    target_date: date
    baseline_days: int
    started_at: datetime
    trigger: dict[str, Any]
    funnel_checks: list[dict[str, Any]]
    _actual_overall: dict[str, Any]
    _baseline_overall: dict[str, Any]
    _abnormal_stages: list[str]
    dimensions_to_check: list[str]
    dimensions_checked: list[str]
    explorations: list[dict[str, Any]]
    flagged_dimensions: list[dict[str, Any]]  
    recursive_drilldowns: list[dict[str, Any]]  
    attribution: list[dict[str, Any]]
    hypotheses: list[dict[str, Any]]
    validated_hypotheses: list[dict[str, Any]]
    ruled_out: list[str]
    root_causes: list[dict[str, Any]]
    counterfactual: dict[str, Any] | None
    recommendations: list[str]
    executive_summary: str
    overall_confidence: float
    agent_log: list[dict[str, Any]]
