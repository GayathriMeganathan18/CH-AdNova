from fastapi import APIRouter, Depends
from app.dependencies import get_repo
from app.repositories.clickhouse_repo import ClickHouseRepository

router = APIRouter()

@router.get("/health")
def health(repo: ClickHouseRepository = Depends(get_repo)):
    try:
        ch_ok = repo.ping()
    except Exception as exc:
        return {"status": "degraded", "clickhouse": f"error: {exc}"}
    return {"status": "ok" if ch_ok else "degraded", "clickhouse": "up" if ch_ok else "down"}
