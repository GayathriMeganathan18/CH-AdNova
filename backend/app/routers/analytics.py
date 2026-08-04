from datetime import date
from fastapi import APIRouter, Depends
from app.analytics.anomaly import ANOMALY_STRATEGIES, AnomalyStrategy, detect_anomaly
from app.analytics.baseline import BASELINE_STRATEGIES, BaselineStrategy, SUPPORTED_METRICS, compute_baseline
from app.analytics.timeseries import WINDOWS, Window, build_timeseries
from app.config import Settings, get_settings
from app.dependencies import get_anomaly_store, get_repo
from app.repositories.anomaly_store import AnomalyStore
from app.repositories.clickhouse_repo import ClickHouseRepository
from app.schemas.analytics import AnomalyResponse, BaselineResponse, StrategyCatalog

router = APIRouter(prefix="/api/analytics")

DEPENDENCY_TREE_CHILDREN: tuple[str, ...] = ("requests", "fill_rate", "ctr", "ecpm", "impressions", "clicks")
_SEVERITY_COLOR = {"none": "green", "low": "amber", "medium": "amber", "high": "red"}

@router.get("/strategies", response_model=StrategyCatalog)
def strategies():
    return StrategyCatalog(
        baseline_strategies=list(BASELINE_STRATEGIES),
        anomaly_strategies=list(ANOMALY_STRATEGIES),
        metrics=sorted(SUPPORTED_METRICS),
        windows=list(WINDOWS),
    )


@router.get("/baseline", response_model=BaselineResponse)
def baseline(
    metric: str,
    target_date: date,
    baseline_days: int = 7,
    strategy: BaselineStrategy = "rolling_mean",
    threshold: float | None = None,
    repo: ClickHouseRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
):
    effective_threshold = threshold if threshold is not None else settings.significance_threshold_pct
    result = compute_baseline(
        repo, metric, target_date, baseline_days,
        strategy=strategy, severity_threshold_pct=effective_threshold,
    )
    return result.to_dict()


@router.get("/anomaly", response_model=AnomalyResponse)
def anomaly(
    metric: str,
    target_date: date,
    baseline_days: int = 7,
    strategy: AnomalyStrategy = "pct_deviation",
    threshold: float | None = None,
    store_result: bool = True,
    repo: ClickHouseRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
    store: AnomalyStore = Depends(get_anomaly_store),
):
    effective_threshold = threshold
    if effective_threshold is None and strategy == "pct_deviation":
        effective_threshold = settings.significance_threshold_pct
    result = detect_anomaly(
        repo, metric, target_date, baseline_days, strategy=strategy, threshold=effective_threshold
    )
    if store_result and result.is_anomalous:
        record = result.to_dict()
        record["status"] = "detected"
        record["source"] = "manual"
        store.save(result.id, record)
    return result.to_dict()


@router.get("/timeseries")
def timeseries(
    metric: str,
    target_date: date,
    window: Window = "7d",
    forecast_points: int = 0,
    app_id: str | None = None,
    region: str | None = None,
    publisher_tier: str | None = None,
    repo: ClickHouseRepository = Depends(get_repo),
):
    return build_timeseries(repo, metric, target_date, window, forecast_points, app_id, region, publisher_tier)


@router.get("/dependency-tree")
def dependency_tree(
    target_date: date,
    baseline_days: int = 7,
    strategy: BaselineStrategy = "rolling_mean",
    threshold: float | None = None,
    repo: ClickHouseRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
):
    
    effective_threshold = threshold if threshold is not None else settings.significance_threshold_pct

    def node_for(metric: str) -> dict:
        result = compute_baseline(
            repo, metric, target_date, baseline_days,
            strategy=strategy, severity_threshold_pct=effective_threshold,
        )
        d = result.to_dict()
        d["color"] = _SEVERITY_COLOR.get(d["severity"], "green")
        return d

    root = node_for("revenue")
    children = [node_for(m) for m in DEPENDENCY_TREE_CHILDREN]
    return {"root": root, "children": children}


@router.get("/alerts")
def list_alerts(
    limit: int = 50,
    metric: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    store: AnomalyStore = Depends(get_anomaly_store),
):
    records = store.list_recent(
        limit=limit, metric=metric, severity=severity, is_anomalous=True,
        status=status, start_date=start_date, end_date=end_date,
    )
    for r in records:
        r["id"] = r.pop("_id")
    return records
