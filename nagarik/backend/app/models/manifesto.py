"""Manifesto promises and their progress over time."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.politician import Politician


class ManifestoItem(Base):
    __tablename__ = "manifesto_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    politician_id: Mapped[int | None] = mapped_column(
        ForeignKey("politicians.id"), nullable=True, index=True
    )
    party: Mapped[str | None] = mapped_column(String(128), nullable=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # promised | in_progress | achieved | broken | unknown
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="promised")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    politician: Mapped["Politician | None"] = relationship(back_populates="manifesto_items")
    progress_updates: Mapped[list["ManifestoProgressUpdate"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class ManifestoProgressUpdate(Base):
    __tablename__ = "manifesto_progress_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manifesto_item_id: Mapped[int] = mapped_column(
        ForeignKey("manifesto_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # mirrors ManifestoItem.status
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    item: Mapped["ManifestoItem"] = relationship(back_populates="progress_updates")
    document: Mapped["Document | None"] = relationship()
