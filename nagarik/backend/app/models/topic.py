"""Topics / Issues. Self-referential hierarchy (e.g. 'Health' > 'Public Hospitals')."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)

    parent: Mapped["Topic | None"] = relationship(remote_side="Topic.id", backref="children")
