"""Step 3 of the pipeline: checksum-based deduplication."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document


def is_duplicate(db: Session, checksum: str) -> Document | None:
    """Return the existing Document if this checksum has been seen, else None."""
    return db.execute(select(Document).where(Document.checksum == checksum)).scalar_one_or_none()
