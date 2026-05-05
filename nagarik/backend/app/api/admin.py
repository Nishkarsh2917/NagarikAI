"""Admin endpoints. Token-gated via X-Admin-Token header."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.ingestion.pipeline import run_all
from app.models import IngestionRun, Source
from app.schemas import IngestionRunOut, IngestionStatusOut, SourceOut

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")


@router.get(
    "/ingestion-status",
    response_model=IngestionStatusOut,
    dependencies=[Depends(require_admin)],
)
def ingestion_status(db: Session = Depends(get_db)) -> IngestionStatusOut:
    runs = (
        db.execute(select(IngestionRun).order_by(desc(IngestionRun.started_at)).limit(50))
        .scalars()
        .all()
    )
    sources = db.execute(select(Source).order_by(Source.name)).scalars().all()
    return IngestionStatusOut(
        runs=[IngestionRunOut.model_validate(r, from_attributes=True) for r in runs],
        sources=[SourceOut.model_validate(s, from_attributes=True) for s in sources],
    )


@router.post(
    "/run-ingestion",
    dependencies=[Depends(require_admin)],
    status_code=202,
)
def trigger_ingestion(background: BackgroundTasks) -> dict:
    """Fire-and-forget. Real result is visible in /ingestion-status."""
    background.add_task(run_all)
    return {"status": "queued"}
