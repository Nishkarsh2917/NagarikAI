"""Politicians and the elections they contested."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.geography import Constituency
    from app.models.manifesto import ManifestoItem


class Politician(Base):
    __tablename__ = "politicians"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    party: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_links_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    candidacies: Mapped[list["Candidacy"]] = relationship(back_populates="politician")
    manifesto_items: Mapped[list["ManifestoItem"]] = relationship(back_populates="politician")


class Candidacy(Base):
    __tablename__ = "candidacies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    politician_id: Mapped[int] = mapped_column(
        ForeignKey("politicians.id"), nullable=False, index=True
    )
    constituency_id: Mapped[int] = mapped_column(
        ForeignKey("constituencies.id"), nullable=False, index=True
    )
    election_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # contesting | won | lost | withdrew
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="contesting")

    affidavit_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )

    politician: Mapped["Politician"] = relationship(back_populates="candidacies")
    constituency: Mapped["Constituency"] = relationship(back_populates="candidacies")
