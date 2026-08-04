import json
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.dependencies import get_investigation_service, get_investigation_store
from app.repositories.investigation_store import InvestigationStore
from app.schemas.investigation import InvestigationRequest, InvestigationResult
from app.services.investigation_service import InvestigationService
from app.services.report_export import build_markdown_report

router = APIRouter(prefix="/api")

@router.post("/investigate", response_model=InvestigationResult)
def investigate(
    request: InvestigationRequest,
    service: InvestigationService = Depends(get_investigation_service),
):
    return service.run_investigation(request)


@router.get("/investigations/{investigation_id}")
def get_investigation(
    investigation_id: str,
    store: InvestigationStore = Depends(get_investigation_store),
):
    record = store.get(investigation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Investigation not found")
    record["investigation_id"] = record.pop("_id")
    return record


@router.get("/investigations/{investigation_id}/export")
def export_investigation(
    investigation_id: str,
    format: Literal["markdown", "json"] = "markdown",
    store: InvestigationStore = Depends(get_investigation_store),
):
    record = store.get(investigation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Investigation not found")
    record["investigation_id"] = record.pop("_id")
    if format == "json":
        payload = {
            "report_type": "ch-adnova-incident-report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "investigation": record,
        }
        body = json.dumps(payload, indent=2, default=str)
        return Response(
            content=body,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="investigation-{investigation_id}.json"'},
        )

    markdown = build_markdown_report(record)
    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="investigation-{investigation_id}.md"'},
    )


@router.get("/investigations")
def list_investigations(store: InvestigationStore = Depends(get_investigation_store)):
    records = store.list_recent()
    for r in records:
        r["investigation_id"] = r.pop("_id")
    return records
