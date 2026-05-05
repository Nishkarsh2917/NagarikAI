"""
Ingestion pipeline orchestrator.

Design notes (mirror ARCHITECTURE.md §4):
  - One IngestionRun row per (source, tick).
  - Each source isolated in its own try/except.
  - Each step on each item also wrapped — partial failures land at the latest
    successful status and stay reprocessable.
  - Idempotent: deduped by document.checksum (unique). Re-running the cron is safe.
  - Raw is persisted BEFORE parsing so we can re-run any later step with better
    prompts/parsers without re-fetching.
"""
from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.ingestion import classifier, dedupe, extractor, mapper, parsers, summarizer
from app.ingestion.adapters import get_adapter
from app.models import (
    AuditLog,
    Document,
    DocumentSnapshot,
    ExtractedFact,
    IngestionRun,
    Source,
    Summary,
)
from app.storage import checksum_of, get_store, make_storage_key

logger = logging.getLogger(__name__)


def run_all() -> dict:
    """Run ingestion for all active sources. Returns a summary dict."""
    db = SessionLocal()
    try:
        sources = db.execute(select(Source).where(Source.active.is_(True))).scalars().all()
        results = []
        for source in sources:
            try:
                results.append(_run_for_source(db, source))
            except Exception as e:
                logger.exception("Source %s totally failed", source.slug)
                results.append({"source": source.slug, "status": "failed", "error": str(e)})
        return {"sources": results, "ran_at": datetime.now(timezone.utc).isoformat()}
    finally:
        db.close()


def _run_for_source(db: Session, source: Source) -> dict:
    run = IngestionRun(source_id=source.id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    log_lines: list[str] = []
    fetched = new = errors = 0

    try:
        adapter = get_adapter(source.adapter_key)
        items = adapter.fetch(source)
        fetched = len(items)
        log_lines.append(f"adapter '{source.adapter_key}' returned {fetched} items")

        for item in items:
            try:
                created = _ingest_one(db, source, item)
                if created:
                    new += 1
            except Exception as e:
                errors += 1
                logger.warning("Item failed for source %s: %s", source.slug, e)
                log_lines.append(f"ERROR on {item.get('source_url')}: {e}")

        run.status = "success" if errors == 0 else "partial"
        source.last_fetched_at = datetime.now(timezone.utc)
        source.last_status = "ok" if errors == 0 else f"partial: {errors} errors"

    except Exception as e:
        run.status = "failed"
        log_lines.append(f"FATAL: {e}\n{traceback.format_exc()}")
        source.last_status = f"error: {e}"
        logger.exception("Run failed for source %s", source.slug)

    run.fetched_count = fetched
    run.new_count = new
    run.error_count = errors
    run.log_text = "\n".join(log_lines)[:20000]
    run.finished_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "source": source.slug,
        "status": run.status,
        "fetched": fetched,
        "new": new,
        "errors": errors,
    }


def _ingest_one(db: Session, source: Source, item: dict) -> bool:
    """
    Ingest a single fetched item end-to-end. Returns True if a new document was created.
    """
    raw_bytes: bytes = item["raw_bytes"]
    content_type: str = item["content_type"]
    source_url: str = item["source_url"]

    checksum = checksum_of(raw_bytes)

    # Step 3: dedupe
    existing = dedupe.is_duplicate(db, checksum)
    if existing is not None:
        return False

    # Step 1 (storage): persist raw BEFORE any processing — survives prompt changes.
    storage_key = make_storage_key(source.slug, raw_bytes, content_type)
    storage_path = get_store().put(storage_key, raw_bytes)

    # Step 2: parse
    parsed_title, extracted_text = parsers.parse(raw_bytes, content_type)
    title = item.get("title") or parsed_title or "(untitled)"
    language = parsers.detect_language(extracted_text)

    # Create the Document row at status='parsed' so failures past this are recoverable.
    doc = Document(
        source_id=source.id,
        source_url=source_url,
        canonical_url=source_url,
        title=title[:512] if title else None,
        document_type="unknown",
        raw_storage_path=storage_path,
        extracted_text=extracted_text or None,
        language=language,
        published_at=item.get("published_at"),
        fetched_at=datetime.now(timezone.utc),
        checksum=checksum,
        status="parsed",
        confidence_score=0.5,
    )
    db.add(doc)
    db.flush()

    # Snapshot — append-only.
    db.add(
        DocumentSnapshot(
            document_id=doc.id,
            fetched_at=doc.fetched_at,
            raw_storage_path=storage_path,
            checksum=checksum,
        )
    )

    # Step 4a: classify
    confidences: list[float] = []
    try:
        dtype, c_class = classifier.classify(title, extracted_text or "")
        doc.document_type = dtype
        doc.status = "classified"
        confidences.append(c_class)
    except Exception as e:
        logger.warning("Classify failed for doc %s: %s", doc.id, e)

    # Step 4b: extract facts
    try:
        facts, c_extract = extractor.extract(title, extracted_text or "")
        for f in facts:
            db.add(
                ExtractedFact(
                    document_id=doc.id,
                    key=f["key"],
                    value=f["value"],
                    confidence=f["confidence"],
                )
            )
        confidences.append(c_extract)
    except Exception as e:
        logger.warning("Extract failed for doc %s: %s", doc.id, e)

    # Step 5: summarize EN (always) + HI (best-effort)
    try:
        en = summarizer.summarize(title, extracted_text or "", language="en")
        db.add(Summary(document_id=doc.id, source_citation=source_url, **en))
        confidences.append(en["confidence_score"])
    except Exception as e:
        logger.warning("EN summary failed for doc %s: %s", doc.id, e)

    try:
        hi = summarizer.summarize(title, extracted_text or "", language="hi")
        db.add(Summary(document_id=doc.id, source_citation=source_url, **hi))
    except Exception as e:
        logger.info("HI summary skipped for doc %s: %s", doc.id, e)

    if confidences:
        doc.status = "summarized"

    # Step 6: map geography + topics
    try:
        m = mapper.map_document(db, title, extracted_text or "")
        doc.state_id = m["state_id"]
        doc.district_id = m["district_id"]
        doc.constituency_id = m["constituency_id"]
        doc.tags_json = m["tags"]
        confidences.append(m["confidence"])
    except Exception as e:
        logger.warning("Mapping failed for doc %s: %s", doc.id, e)

    # Step 7: finalize
    doc.confidence_score = min(confidences) if confidences else 0.3
    doc.status = "published"

    db.add(
        AuditLog(
            actor="pipeline",
            action="document.ingested",
            entity_type="document",
            entity_id=doc.id,
            payload_json={
                "source": source.slug,
                "checksum": checksum,
                "confidence": doc.confidence_score,
            },
        )
    )

    db.commit()
    return True
