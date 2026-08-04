from fastapi import APIRouter
from app.services.monitor_service import get_monitor_service

router = APIRouter(prefix="/api/monitor")

@router.get("/status")
def status():
    return get_monitor_service().status()


@router.post("/run-now")
def run_now():
    results = get_monitor_service().run_now()
    return {"results": results}
