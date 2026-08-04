from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel

Metric = Literal["revenue", "requests", "fill_rate", "ctr", "ecpm", "impressions", "clicks"]
BaselineStrategyName = Literal[
    "rolling_mean", "rolling_median", "moving_average", "ewma", "week_over_week", "day_over_day"
]
AnomalyStrategyName = Literal["pct_deviation", "zscore", "iqr", "rolling_std"]
Severity = Literal["none", "low", "medium", "high"]


class BaselineResponse(BaseModel):
    metric: Metric
    strategy: BaselineStrategyName
    target_date: date
    baseline_days: int
    expected: float
    actual: float
    deviation: float
    deviation_pct: float
    severity: Severity
    confidence: float
    window_values: list[float]
    window_days: list[str]
    sql: list[str]


class AnomalyResponse(BaseModel):
    id: str
    metric: Metric
    target_date: date
    strategy: AnomalyStrategyName
    threshold: float
    is_anomalous: bool
    score: float
    severity: Severity
    baseline: BaselineResponse
    detected_at: datetime


class StrategyCatalog(BaseModel):
    baseline_strategies: list[str]
    anomaly_strategies: list[str]
    metrics: list[str]
    windows: list[str]
