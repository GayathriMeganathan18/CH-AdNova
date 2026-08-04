from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import mean, median, pstdev
from typing import Any, Literal

SUPPORTED_METRICS = {"revenue", "requests", "fill_rate", "ctr", "ecpm", "impressions", "clicks"}
BaselineStrategy = Literal[
    "rolling_mean", "rolling_median", "moving_average", "ewma", "week_over_week", "day_over_day"
]
BASELINE_STRATEGIES: tuple[str, ...] = (
    "rolling_mean", "rolling_median", "moving_average", "ewma", "week_over_week", "day_over_day"
)
Severity = Literal["none", "low", "medium", "high"]
EWMA_ALPHA_DEFAULT = 0.3

@dataclass
class BaselineResult:
    metric: str
    strategy: str
    target_date: date
    baseline_days: int
    expected: float
    actual: float
    deviation: float           
    deviation_pct: float
    severity: Severity
    confidence: float
    window_values: list[float] = field(default_factory=list)
    window_days: list[str] = field(default_factory=list)
    sql: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "strategy": self.strategy,
            "target_date": str(self.target_date),
            "baseline_days": self.baseline_days,
            "expected": self.expected,
            "actual": self.actual,
            "deviation": self.deviation,
            "deviation_pct": self.deviation_pct,
            "severity": self.severity,
            "confidence": self.confidence,
            "window_values": self.window_values,
            "window_days": self.window_days,
            "sql": self.sql,
        }


def _severity_from_ratio(deviation_pct: float, threshold_pct: float) -> Severity:
    if threshold_pct <= 0:
        threshold_pct = 0.01  
    ratio = abs(deviation_pct) / threshold_pct
    if ratio < 1.0:
        return "none"
    if ratio < 1.5:
        return "low"
    if ratio < 2.5:
        return "medium"
    return "high"


def _confidence_from_window(window_values: list[float], baseline_days: int) -> float:
    if len(window_values) < 2:
        return 0.3
    m = mean(window_values)
    cv = (pstdev(window_values) / m) if m else 1.0
    stability = max(0.0, min(1.0, 1 - cv))
    sample_factor = min(1.0, baseline_days / 7)
    confidence = stability * (0.5 + 0.5 * sample_factor)
    return round(max(0.1, min(confidence, 0.95)), 2)

def _ewma(values: list[float], alpha: float = EWMA_ALPHA_DEFAULT) -> float:
    if not values:
        return 0.0
    result = values[0]
    for v in values[1:]:
        result = alpha * v + (1 - alpha) * result
    return result


def compute_baseline(
    repo,
    metric: str,
    target_date: date,
    baseline_days: int = 7,
    strategy: BaselineStrategy = "rolling_mean",
    severity_threshold_pct: float = 8.0,
    ewma_alpha: float = EWMA_ALPHA_DEFAULT,
) -> BaselineResult:
    if metric not in SUPPORTED_METRICS:
        raise ValueError(f"Unsupported metric '{metric}'. Supported: {sorted(SUPPORTED_METRICS)}")
    if strategy not in BASELINE_STRATEGIES:
        raise ValueError(f"Unsupported strategy '{strategy}'. Supported: {BASELINE_STRATEGIES}")

    window_start = target_date - timedelta(days=baseline_days)
    window_end = target_date - timedelta(days=1)
    window_rows, window_sql = repo.daily_series(window_start, window_end)
    window_values = [row[metric] for row in window_rows]
    window_days = [row["day"] for row in window_rows]

    actual_row, actual_sql = repo.overall_daily(target_date)
    actual = actual_row[metric]
    sql_statements = [window_sql, actual_sql]

    if strategy in ("rolling_mean", "moving_average"):
        expected = mean(window_values) if window_values else 0.0
    elif strategy == "rolling_median":
        expected = median(window_values) if window_values else 0.0
    elif strategy == "ewma":
        expected = _ewma(window_values, ewma_alpha)
    elif strategy in ("week_over_week", "day_over_day"):
        offset_days = 7 if strategy == "week_over_week" else 1
        cmp_date = target_date - timedelta(days=offset_days)
        cmp_row, cmp_sql = repo.overall_daily(cmp_date)
        expected = cmp_row[metric]
        sql_statements.append(cmp_sql)
    else:  # pragma: no cover - guarded above
        expected = 0.0

    deviation = actual - expected
    deviation_pct = (deviation / expected * 100) if expected else 0.0
    severity = _severity_from_ratio(deviation_pct, severity_threshold_pct)
    confidence = _confidence_from_window(window_values, baseline_days)

    return BaselineResult(
        metric=metric,
        strategy=strategy,
        target_date=target_date,
        baseline_days=baseline_days,
        expected=expected,
        actual=actual,
        deviation=deviation,
        deviation_pct=deviation_pct,
        severity=severity,
        confidence=confidence,
        window_values=window_values,
        window_days=window_days,
        sql=sql_statements,
    )
