"""Step 6: constituency / topic mapping."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import ai_call
from app.models import Constituency, District, State, Topic


def map_document(db: Session, title: str | None, text: str) -> dict:
    """
    Returns: {
      state_id, district_id, constituency_id,   # ints or None
      tags: list[str],                          # topic slugs
      confidence: float,
    }
    """
    topics = db.execute(select(Topic.name)).scalars().all()
    result = ai_call(
        "map_topic",
        title=title or "",
        excerpt=text[:1500],
        topic_list=list(topics),
    )

    state_id = _lookup_state(db, result.get("state"))
    district_id = _lookup_district(db, result.get("district"), state_id)
    constituency_id = _lookup_constituency(db, result.get("constituency"), state_id)

    tags_raw = result.get("topics") or []
    tags = [str(t).strip() for t in tags_raw if str(t).strip()][:3]

    return {
        "state_id": state_id,
        "district_id": district_id,
        "constituency_id": constituency_id,
        "tags": tags,
        "confidence": max(0.0, min(1.0, float(result.get("confidence", 0.3)))),
    }


def _lookup_state(db: Session, name: str | None) -> int | None:
    if not name:
        return None
    row = db.execute(select(State).where(State.name.ilike(name.strip()))).scalar_one_or_none()
    return row.id if row else None


def _lookup_district(db: Session, name: str | None, state_id: int | None) -> int | None:
    if not name:
        return None
    stmt = select(District).where(District.name.ilike(name.strip()))
    if state_id:
        stmt = stmt.where(District.state_id == state_id)
    row = db.execute(stmt).scalar_one_or_none()
    return row.id if row else None


def _lookup_constituency(db: Session, name: str | None, state_id: int | None) -> int | None:
    if not name:
        return None
    stmt = select(Constituency).where(Constituency.name.ilike(name.strip()))
    if state_id:
        stmt = stmt.where(Constituency.state_id == state_id)
    row = db.execute(stmt).scalar_one_or_none()
    return row.id if row else None
