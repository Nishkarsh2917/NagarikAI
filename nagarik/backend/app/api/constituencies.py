"""GET /api/v1/constituencies  &  GET /api/v1/constituencies/{id}"""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.api._serializers import to_update_out
from app.db import get_db
from app.models import Candidacy, CitizenFeedback, Constituency, Document, Topic
from app.schemas import (
    CandidacyOut,
    ConstituencyDetail,
    ConstituencyOut,
    DistrictOut,
    PoliticianOut,
    StateOut,
)

router = APIRouter(prefix="/constituencies", tags=["constituencies"])


@router.get("", response_model=list[ConstituencyOut])
def list_constituencies(db: Session = Depends(get_db)) -> list[ConstituencyOut]:
    rows = db.execute(select(Constituency).order_by(Constituency.name)).scalars().all()
    return [ConstituencyOut.model_validate(r, from_attributes=True) for r in rows]


@router.get("/{cid}", response_model=ConstituencyDetail)
def get_constituency(cid: int, db: Session = Depends(get_db)) -> ConstituencyDetail:
    c = db.execute(
        select(Constituency)
        .where(Constituency.id == cid)
        .options(
            selectinload(Constituency.state),
            selectinload(Constituency.district),
            selectinload(Constituency.candidacies).selectinload(Candidacy.politician),
        )
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(404, "Constituency not found")

    # Recent updates — limit to last 10.
    recent_docs = (
        db.execute(
            select(Document)
            .where(Document.constituency_id == cid, Document.status == "published")
            .order_by(desc(Document.fetched_at))
            .options(selectinload(Document.source), selectinload(Document.summaries))
            .limit(10)
        )
        .scalars()
        .all()
    )

    # Top topics — derived from feedback for the constituency, falling back to doc tags.
    feedback_topic_ids = (
        db.execute(
            select(CitizenFeedback.topic_id).where(
                CitizenFeedback.constituency_id == cid,
                CitizenFeedback.topic_id.is_not(None),
            )
        )
        .scalars()
        .all()
    )
    counts = Counter(feedback_topic_ids)
    top_topic_rows: list[dict] = []
    if counts:
        top_ids = [tid for tid, _ in counts.most_common(5)]
        topics = db.execute(select(Topic).where(Topic.id.in_(top_ids))).scalars().all()
        by_id = {t.id: t for t in topics}
        for tid, count in counts.most_common(5):
            t = by_id.get(tid)
            if t:
                top_topic_rows.append({"id": t.id, "name": t.name, "slug": t.slug, "count": count})

    candidacies = [
        CandidacyOut(
            id=cand.id,
            politician=PoliticianOut.model_validate(cand.politician, from_attributes=True),
            constituency_id=cand.constituency_id,
            election_year=cand.election_year,
            status=cand.status,
            affidavit_document_id=cand.affidavit_document_id,
        )
        for cand in c.candidacies
    ]

    return ConstituencyDetail(
        id=c.id,
        name=c.name,
        type=c.type,
        number=c.number,
        state_id=c.state_id,
        district_id=c.district_id,
        state=StateOut.model_validate(c.state, from_attributes=True) if c.state else None,
        district=DistrictOut.model_validate(c.district, from_attributes=True) if c.district else None,
        recent_updates=[to_update_out(d) for d in recent_docs],
        candidates=candidacies,
        top_topics=top_topic_rows,
    )
