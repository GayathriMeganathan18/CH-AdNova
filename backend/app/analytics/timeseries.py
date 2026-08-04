from datetime import date, datetime, timedelta
from typing import Any, Literal
from app.analytics.baseline import SUPPORTED_METRICS

Window = Literal["24h", "7d", "30d"]
WINDOWS: tuple[str, ...] = ("24h", "7d", "30d")

def _linear_forecast(values: list[float], n_points: int) -> list[float]:
    n = len(values)
    if n_points <= 0:
        return []
    if n < 2:
        flat = values[-1] if values else 0.0
        return [round(flat, 4)] * n_points
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    den = sum((x - mean_x) ** 2 for x in xs)
    slope = (num / den) if den else 0.0
    intercept = mean_y - slope * mean_x
    return [round(slope * (n + i) + intercept, 4) for i in range(n_points)]

def build_timeseries(
    repo, metric: str, target_date: date, window: str, forecast_points: int = 0,
    app_id: str | None = None, region: str | None = None, publisher_tier: str | None = None,
) -> dict[str, Any]:
    if metric not in SUPPORTED_METRICS:
        raise ValueError(f"Unsupported metric '{metric}'. Supported: {sorted(SUPPORTED_METRICS)}")
    if window not in WINDOWS:
        raise ValueError(f"Unsupported window '{window}'. Supported: {WINDOWS}")
    filtered = bool(app_id or region or publisher_tier)
    if window == "24h":
        if filtered:
            rows, sql = repo.filtered_hourly_series(target_date, target_date, app_id, region, publisher_tier)
        else:
            rows, sql = repo.hourly_series(target_date, target_date)
        label_key = "hour"
        step = timedelta(hours=1)
    else:
        days_back = 6 if window == "7d" else 29
        start = target_date - timedelta(days=days_back)
        if filtered:
            rows, sql = repo.filtered_daily_series(start, target_date, app_id, region, publisher_tier)
        else:
            rows, sql = repo.daily_series(start, target_date)
        label_key = "day"
        step = timedelta(days=1)

    labels = [r[label_key] for r in rows]
    values = [r[metric] for r in rows]
    forecast_values = _linear_forecast(values, forecast_points)
    forecast_labels: list[str] = []
    if forecast_values and labels:
        last = datetime.fromisoformat(labels[-1]) if window == "24h" else date.fromisoformat(labels[-1])
        forecast_labels = [str(last + step * (i + 1)) for i in range(len(forecast_values))]

    return {
        "metric": metric,
        "window": window,
        "target_date": str(target_date),
        "labels": labels,
        "values": values,
        "forecast_labels": forecast_labels,
        "forecast_values": forecast_values,
        "sql": sql,
    }
