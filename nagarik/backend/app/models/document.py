"""Document and its satellites: snapshots (versioning), facts (structured), summaries (multi-lang)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.geography import Constituency, District, State
    from app.models.source import Source


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_fetched_at_desc", "fetched_at"),
        Index("ix_documents_constituency_fetched", "constituency_id", "fetched_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    title: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # press_release | policy | budget | bill | affidavit |
    # constituency_update | local_update | feedback | unknown
    document_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")

    raw_storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # SHA-256 of normalized payload — unique dedup key
    checksum: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # fetched | parsed | classified | summarized | published | failed
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="fetched")

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    state_id: Mapped[int | None] = mapped_column(ForeignKey("states.id"), nullable=True)
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"), nullable=True)
    constituency_id: Mapped[int | None] = mapped_column(
        ForeignKey("constituencies.id"), nullable=True, index=True
    )

    tags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, default=list)

    source: Mapped["Source"] = relationship(back_populates="documents")
    constituency: Mapped["Constituency | None"] = relationship(back_populates="documents")
    district: Mapped["District | None"] = relationship()
    state: Mapped["State | None"] = relationship()

    snapshots: Mapped[list["DocumentSnapshot"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    facts: Mapped[list["ExtractedFact"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    summaries: Mapped[list["Summary"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentSnapshot(Base):
    """Append-only history. We never mutate raw payloads — we add a snapshot."""
    __tablename__ = "document_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="snapshots")


class ExtractedFact(Base):
    """Structured key-value pairs pulled out of the document by the extractor step."""
    __tablename__ = "extracted_facts"
    __table_args__ = (Index("ix_facts_doc_key", "document_id", "key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(64), nullable=False)  # who, what, where, when, amount…
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    # Where in extracted_text we sourced it — supports the "see in source" UI.
    source_span_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_span_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="facts")


class Summary(Base):
    """One row per (document, language). Versioned by `model_used`."""
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(8), nullable=False)  # en | hi

    one_line: Mapped[str | None] = mapped_column(String(512), nullable=True)
    three_bullets_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    why_it_matters: Mapped[str | None] = mapped_column(Text, nullable=True)
    who_is_affected: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_citation: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    model_used: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    document: Mapped["Document"] = relationship(back_populates="summaries")
