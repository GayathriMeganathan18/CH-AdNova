from datetime import date, timedelta
from fastapi import APIRouter, Depends
from app.dependencies import get_repo
from app.repositories.clickhouse_repo import ClickHouseRepository

router = APIRouter(prefix="/api/metrics")

@router.get("/date-range")
def date_range(repo: ClickHouseRepository = Depends(get_repo)):
    start, end = repo.data_date_range()
    return {"min_date": str(start) if start else None, "max_date": str(end) if end else None}

@router.get("/daily")
def daily(
    start: date, end: date,
    app_id: str | None = None, region: str | None = None, publisher_tier: str | None = None,
    repo: ClickHouseRepository = Depends(get_repo),
):
    if app_id or region or publisher_tier:
        rows, sql = repo.filtered_daily_series(start, end, app_id, region, publisher_tier)
    else:
        rows, sql = repo.daily_series(start, end)
    return {"rows": rows, "sql": sql}


@router.get("/kpis")
def kpis(
    target_date: date, baseline_days: int = 7,
    app_id: str | None = None, region: str | None = None, publisher_tier: str | None = None,
    repo: ClickHouseRepository = Depends(get_repo),
):
    if app_id or region or publisher_tier:
        actual, actual_sql = repo.filtered_overall_range(target_date, target_date, app_id, region, publisher_tier, divide_by=1)
        start = target_date - timedelta(days=baseline_days)
        end = target_date - timedelta(days=1)
        baseline, baseline_sql = repo.filtered_overall_range(start, end, app_id, region, publisher_tier, divide_by=baseline_days)
    else:
        actual, actual_sql = repo.overall_daily(target_date)
        baseline, baseline_sql = repo.overall_baseline(target_date, baseline_days)
    return {
        "target_date": str(target_date),
        "actual": actual,
        "baseline": baseline,
        "sql": [actual_sql, baseline_sql],
    }
