"""Shared serialization helpers — keeps routers thin and consistent."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, Summary
from app.schemas import FactOut, SummaryOut, UpdateDetail, UpdateOut


def _summary_one_line(doc: Document, lang: str) -> str | None:
    for s in doc.summaries:
        if s.language == lang:
            return s.one_line
    return None


def to_update_out(doc: Document) -> UpdateOut:
    return UpdateOut(
        id=doc.id,
        title=doc.title,
        document_type=doc.document_type,
        source_id=doc.source_id,
        source_name=doc.source.name if doc.source else None,
        source_trust_label=doc.source.trust_label if doc.source else None,
        source_url=doc.source_url,
        published_at=doc.published_at,
        fetched_at=doc.fetched_at,
        confidence_score=doc.confidence_score,
        constituency_id=doc.constituency_id,
        summary_one_line_en=_summary_one_line(doc, "en"),
        summary_one_line_hi=_summary_one_line(doc, "hi"),
        tags_json=doc.tags_json,
    )


def to_update_detail(doc: Document) -> UpdateDetail:
    base = to_update_out(doc).model_dump()
    base["canonical_url"] = doc.canonical_url
    base["extracted_text_preview"] = (doc.extracted_text or "")[:2500] or None
    base["facts"] = [
        FactOut.model_validate(f, from_attributes=True) for f in doc.facts
    ]
    base["summaries"] = [
        SummaryOut.model_validate(s, from_attributes=True) for s in doc.summaries
    ]
    return UpdateDetail(**base)
