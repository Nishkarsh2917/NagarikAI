"""GET /api/v1/manifestos"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ManifestoItem
from app.schemas import ManifestoItemOut

router = APIRouter(prefix="/manifestos", tags=["manifestos"])


@router.get("", response_model=list[ManifestoItemOut])
def list_manifestos(
    db: Session = Depends(get_db),
    politician_id: int | None = None,
    party: str | None = None,
    status: str | None = None,
) -> list[ManifestoItemOut]:
    stmt = select(ManifestoItem)
    if politician_id is not None:
        stmt = stmt.where(ManifestoItem.politician_id == politician_id)
    if party:
        stmt = stmt.where(ManifestoItem.party == party)
    if status:
        stmt = stmt.where(ManifestoItem.status == status)
    rows = db.execute(stmt).scalars().all()
    return [ManifestoItemOut.model_validate(r, from_attributes=True) for r in rows]
