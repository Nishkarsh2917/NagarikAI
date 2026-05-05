"""GET /api/v1/feedback (clusters)  &  POST /api/v1/feedback (submit)"""
import hashlib
from typing import Optional

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CitizenFeedback, FeedbackCluster
from app.schemas import FeedbackClusterOut, FeedbackIn, FeedbackOut

router = APIRouter(prefix="/feedback", tags=["feedback"])

# Per-IP rate limit on submission endpoint.
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=list[FeedbackClusterOut])
def list_clusters(
    db: Session = Depends(get_db),
    constituency_id: Optional[int] = None,
    topic_id: Optional[int] = None,
) -> list[FeedbackClusterOut]:
    stmt = select(FeedbackCluster).order_by(desc(FeedbackCluster.count))
    if constituency_id is not None:
        stmt = stmt.where(FeedbackCluster.constituency_id == constituency_id)
    if topic_id is not None:
        stmt = stmt.where(FeedbackCluster.topic_id == topic_id)
    rows = db.execute(stmt).scalars().all()
    return [FeedbackClusterOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=FeedbackOut, status_code=201)
@limiter.limit("5/minute")
def submit_feedback(
    payload: FeedbackIn,
    request: Request,
    db: Session = Depends(get_db),
) -> FeedbackOut:
    ip = get_remote_address(request) or "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:32]

    fb = CitizenFeedback(
        text=payload.text.strip(),
        language=payload.language,
        constituency_id=payload.constituency_id,
        document_id=payload.document_id,
        topic_id=payload.topic_id,
        ip_hash=ip_hash,
        status="pending",       # moderation queue
        sentiment=0.0,          # set later by clustering job
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return FeedbackOut.model_validate(fb, from_attributes=True)
