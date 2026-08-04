import httpx
from fastapi import APIRouter, Depends
from app.config import Settings, get_settings
from app.dependencies import get_investigation_store, get_langfuse_tracer, get_repo
from app.observability.langfuse_tracer import LangfuseTracer
from app.repositories.clickhouse_repo import ClickHouseRepository
from app.repositories.investigation_store import InvestigationStore
from app.services.monitor_service import get_monitor_service

router = APIRouter(prefix="/api/system")

@router.get("/health")
def system_health(
    repo: ClickHouseRepository = Depends(get_repo),
    store: InvestigationStore = Depends(get_investigation_store),
    tracer: LangfuseTracer = Depends(get_langfuse_tracer),
    settings: Settings = Depends(get_settings),
):
    try:
        clickhouse_up = repo.ping()
    except Exception:
        clickhouse_up = False

    mongo_up = store.ping()

    try:
        resp = httpx.get(f"{settings.clickstack_host}/api/health", timeout=2.0)
        clickstack_up = resp.status_code == 200
    except Exception:
        clickstack_up = False

    try:
        monitor_running = get_monitor_service().status()["running"]
    except RuntimeError:
        monitor_running = False

    components = {
        "clickhouse": {"up": clickhouse_up, "required": True},
        "mongodb": {"up": mongo_up, "required": True},
        "langfuse": {
            "up": tracer.enabled, "required": False,
            "note": "optional - degrades to no-op tracing when LANGFUSE_PUBLIC_KEY/SECRET_KEY aren't set",
        },
        "clickstack": {
            "up": clickstack_up, "required": False, "note": "optional OpenTelemetry backend",
            "url": settings.clickstack_url or None,
        },
        "monitor": {"up": monitor_running, "required": False, "note": "real-time metric monitor scheduler"},
    }
    required_ok = all(c["up"] for c in components.values() if c["required"])
    return {"status": "ok" if required_ok else "degraded", "components": components}
