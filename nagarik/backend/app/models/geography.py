"""Geographic hierarchy. Constituencies map to districts map to states."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.politician import Candidacy


class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True)  # e.g. "DL"

    districts: Mapped[list["District"]] = relationship(back_populates="state")


class District(Base):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), nullable=False, index=True)

    state: Mapped["State"] = relationship(back_populates="districts")
    constituencies: Mapped[list["Constituency"]] = relationship(back_populates="district")


class Constituency(Base):
    __tablename__ = "constituencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # lok_sabha | vidhan_sabha
    type: Mapped[str] = mapped_column(String(16), nullable=False)

    # PC number for Lok Sabha, AC number for Vidhan Sabha
    number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), nullable=False, index=True)
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"), nullable=True, index=True)

    state: Mapped["State"] = relationship()
    district: Mapped["District | None"] = relationship(back_populates="constituencies")

    documents: Mapped[list["Document"]] = relationship(back_populates="constituency")
    candidacies: Mapped[list["Candidacy"]] = relationship(back_populates="constituency")
