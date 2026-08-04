from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field

Metric = Literal["revenue", "requests", "fill_rate", "ctr", "ecpm", "impressions", "clicks"]
Dimension = Literal["app", "advertiser", "geo", "device", "format"]
ExtendedDimension = Literal["app", "advertiser", "geo", "region", "device", "os", "format", "publisher"]


class InvestigationRequest(BaseModel):
    metric: Metric = "revenue"
    target_date: date = Field(..., description="The day whose metric looks anomalous")
    baseline_days: int = Field(7, ge=1, le=30, description="How many preceding days form the baseline")


class MetricPoint(BaseModel):
    value: float
    baseline: float
    delta: float
    pct_change: float


class MetricTrigger(BaseModel):
    metric: Metric
    target_date: date
    overall: MetricPoint
    is_anomalous: bool
    reason: str


class FunnelCheck(BaseModel):
    stage: Literal["requests", "fill_rate", "ctr", "ecpm"]
    baseline: float
    actual: float
    pct_change: float
    is_abnormal: bool


class FunnelVolumes(BaseModel):
    requests: int
    fills: int
    impressions: int
    clicks: int


class DimensionValueResult(BaseModel):
    dimension: Dimension
    value: str
    metadata: dict[str, str] = Field(default_factory=dict)
    baseline_metric: float
    actual_metric: float
    delta: float
    share_of_total_delta_pct: float


class DimensionExploration(BaseModel):
    dimension: Dimension
    is_significant: bool
    top_contributor: DimensionValueResult | None
    all_values: list[DimensionValueResult]
    sql: str


class RecursiveDrilldownValueResult(BaseModel):
    dimension: ExtendedDimension
    value: str
    baseline_metric: float
    actual_metric: float
    delta: float
    share_of_parent_delta_pct: float


class RecursiveDrilldownFinding(BaseModel):
    depth: int
    parent_dimension: str
    parent_value: str
    dimension: ExtendedDimension
    is_significant: bool
    top_contributor: RecursiveDrilldownValueResult | None
    all_values: list[RecursiveDrilldownValueResult]
    sql: str


class Hypothesis(BaseModel):
    id: str
    statement: str
    dimension: Dimension
    value: str
    supporting_evidence: list[str]


class ValidatedHypothesis(Hypothesis):
    is_supported: bool
    validation_sql: str
    validation_note: str
    residual_after_removal_pct: float


class RankedRootCause(BaseModel):
    rank: int
    hypothesis: ValidatedHypothesis
    confidence: float = Field(..., ge=0, le=1)
    business_impact_value: float
    business_impact_pct: float


class Counterfactual(BaseModel):
    scenario: str
    projected_metric: float
    actual_metric: float
    recovered_value: float
    sql: str


class AgentLogEntry(BaseModel):
    agent: str
    started_at: datetime
    duration_ms: float
    sql_statements: list[str] = Field(default_factory=list)
    reasoning: str
    confidence: float | None = None


class InvestigationResult(BaseModel):
    investigation_id: str
    request: InvestigationRequest
    trigger: MetricTrigger
    funnel_checks: list[FunnelCheck]
    funnel_volumes: FunnelVolumes | None = None
    explorations: list[DimensionExploration]
    recursive_drilldowns: list[RecursiveDrilldownFinding] = Field(default_factory=list)
    ruled_out: list[str]
    root_causes: list[RankedRootCause]
    counterfactual: Counterfactual | None
    recommendations: list[str]
    executive_summary: str
    overall_confidence: float
    agent_log: list[AgentLogEntry]
    langfuse_trace_url: str | None = None
    created_at: datetime
