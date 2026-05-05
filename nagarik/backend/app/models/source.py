"""Source: every place we ingest from. Drives the adapter registry."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.audit import IngestionRun


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # central_gov | parliament | eci | open_data | local_gov | local_news | mock
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # official | third_party | tentative
    trust_label: Mapped[str] = mapped_column(String(32), nullable=False, default="official")

    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    adapter_key: Mapped[str] = mapped_column(String(64), nullable=False)
    config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    documents: Mapped[list["Document"]] = relationship(back_populates="source")
    runs: Mapped[list["IngestionRun"]] = relationship(back_populates="source")
