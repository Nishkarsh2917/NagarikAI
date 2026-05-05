"""GET /api/v1/search?q=… and GET /api/v1/sources"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api._serializers import to_update_out
from app.db import get_db
from app.models import Document, Source
from app.schemas import SourceOut, UpdateOut

router = APIRouter(tags=["search-sources"])


@router.get("/search", response_model=list[UpdateOut])
def search(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
) -> list[UpdateOut]:
    """
    MVP search: case-insensitive LIKE across title, extracted_text, and summary.one_line.
    For production switch to Postgres tsvector with a GIN index.
    """
    like = f"%{q}%"
    rows = (
        db.execute(
            select(Document)
            .where(
                Document.status == "published",
                or_(
                    Document.title.ilike(like),
                    Document.extracted_text.ilike(like),
                ),
            )
            .options(selectinload(Document.source), selectinload(Document.summaries))
            .order_by(desc(Document.fetched_at))
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [to_update_out(d) for d in rows]


@router.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)) -> list[SourceOut]:
    rows = db.execute(select(Source).order_by(Source.name)).scalars().all()
    return [SourceOut.model_validate(r, from_attributes=True) for r in rows]
