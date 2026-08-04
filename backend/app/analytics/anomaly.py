import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from statistics import mean, pstdev, quantiles
from typing import Any, Literal
from app.analytics.baseline import BaselineResult, compute_baseline

AnomalyStrategy = Literal["pct_deviation", "zscore", "iqr", "rolling_std"]
ANOMALY_STRATEGIES: tuple[str, ...] = ("pct_deviation", "zscore", "iqr", "rolling_std")
DEFAULT_THRESHOLDS: dict[str, float] = {
    "pct_deviation": 8.0,
    "zscore": 2.5,
    "iqr": 1.5,
    "rolling_std": 2.0,
}

Severity = Literal["none", "low", "medium", "high"]

@dataclass
class AnomalyResult:
    id: str
    metric: str
    target_date: date
    strategy: str
    threshold: float
    is_anomalous: bool
    score: float
    severity: Severity
    baseline: BaselineResult
    detected_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "metric": self.metric,
            "target_date": str(self.target_date),
            "strategy": self.strategy,
            "threshold": self.threshold,
            "is_anomalous": self.is_anomalous,
            "score": self.score,
            "severity": self.severity,
            "baseline": self.baseline.to_dict(),
            "detected_at": self.detected_at.isoformat(),
        }


def _severity(ratio: float) -> Severity:
    if ratio < 1.0:
        return "none"
    if ratio < 1.5:
        return "low"
    if ratio < 2.5:
        return "medium"
    return "high"


def detect_anomaly(
    repo,
    metric: str,
    target_date: date,
    baseline_days: int = 7,
    strategy: AnomalyStrategy = "pct_deviation",
    threshold: float | None = None,
) -> AnomalyResult:
    if strategy not in ANOMALY_STRATEGIES:
        raise ValueError(f"Unsupported strategy '{strategy}'. Supported: {ANOMALY_STRATEGIES}")
    effective_threshold = threshold if threshold is not None else DEFAULT_THRESHOLDS[strategy]
    baseline = compute_baseline(repo, metric, target_date, baseline_days, strategy="rolling_mean")
    window = baseline.window_values
    actual = baseline.actual
    if strategy == "pct_deviation":
        score = baseline.deviation_pct
        ratio = abs(score) / effective_threshold if effective_threshold else 0.0

    elif strategy == "zscore":
        m = mean(window) if window else 0.0
        sd = pstdev(window) if len(window) > 1 else 0.0
        score = (actual - m) / sd if sd else 0.0
        ratio = abs(score) / effective_threshold if effective_threshold else 0.0

    elif strategy == "rolling_std":
        m = mean(window) if window else 0.0
        sd = pstdev(window) if len(window) > 1 else 0.0
        score = (actual - m) / sd if sd else 0.0
        band = effective_threshold * sd
        ratio = (abs(actual - m) / band) if band else 0.0

    else:  
        if len(window) >= 4:
            q1, _, q3 = quantiles(window, n=4)
        else:
            q1 = q3 = (window[0] if window else actual)
        iqr_range = q3 - q1
        lower = q1 - effective_threshold * iqr_range
        upper = q3 + effective_threshold * iqr_range
        if actual > upper:
            score = actual - upper
        elif actual < lower:
            score = lower - actual
        else:
            score = 0.0
        span = (upper - lower) or 1.0
        ratio = abs(score) / span if span else 0.0

    severity = _severity(ratio)
    is_anomalous = severity != "none"

    return AnomalyResult(
        id=str(uuid.uuid4()),
        metric=metric,
        target_date=target_date,
        strategy=strategy,
        threshold=effective_threshold,
        is_anomalous=is_anomalous,
        score=round(score, 4),
        severity=severity,
        baseline=baseline,
        detected_at=datetime.now(timezone.utc),
    )
