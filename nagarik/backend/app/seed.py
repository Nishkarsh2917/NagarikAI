"""
Seed the database from data/seed/*.json. Idempotent — safe to run repeatedly.

Loads in dependency order: states → districts → constituencies → topics
→ sources → politicians → candidacies → manifesto items.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.models import (
    Candidacy,
    Constituency,
    District,
    ManifestoItem,
    Politician,
    Source,
    State,
    Topic,
)

logger = logging.getLogger(__name__)

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "seed"


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def _load(name: str) -> list[dict]:
    path = SEED_DIR / name
    if not path.exists():
        logger.warning("Seed file missing: %s", path)
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _upsert_by(db, model, by_field: str, row: dict):
    existing = db.execute(
        select(model).where(getattr(model, by_field) == row[by_field])
    ).scalar_one_or_none()
    if existing:
        for k, v in row.items():
            setattr(existing, k, v)
        return existing
    obj = model(**row)
    db.add(obj)
    db.flush()
    return obj


def seed_all() -> None:
    init_db()
    db = SessionLocal()
    try:
        # 1. States — keyed by `code`
        for row in _load("states.json"):
            _upsert_by(db, State, "code", row)

        # 2. Districts — keyed by (name, state_code) — resolve state_code → state_id
        for row in _load("districts.json"):
            state = db.execute(select(State).where(State.code == row.pop("state_code"))).scalar_one()
            existing = db.execute(
                select(District).where(District.name == row["name"], District.state_id == state.id)
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(District(**row, state_id=state.id))
        db.flush()

        # 3. Constituencies — keyed by (name, type, state_code)
        for row in _load("constituencies.json"):
            state = db.execute(select(State).where(State.code == row.pop("state_code"))).scalar_one()
            district = None
            district_name = row.pop("district_name", None)
            if district_name:
                district = db.execute(
                    select(District).where(
                        District.name == district_name, District.state_id == state.id
                    )
                ).scalar_one_or_none()
            existing = db.execute(
                select(Constituency).where(
                    Constituency.name == row["name"],
                    Constituency.type == row["type"],
                    Constituency.state_id == state.id,
                )
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(
                Constituency(
                    **row,
                    state_id=state.id,
                    district_id=district.id if district else None,
                )
            )
        db.flush()

        # 4. Topics — keyed by slug
        for row in _load("topics.json"):
            _upsert_by(db, Topic, "slug", row)

        # 5. Sources — keyed by slug
        for row in _load("sources.json"):
            _upsert_by(db, Source, "slug", row)

        # 6. Politicians — keyed by name (cheap demo key)
        for row in _load("politicians.json"):
            _upsert_by(db, Politician, "name", row)
        db.flush()

        # 7. Candidacies — keyed by (politician_name, constituency_name, election_year)
        for row in _load("candidacies.json"):
            pol = db.execute(
                select(Politician).where(Politician.name == row.pop("politician_name"))
            ).scalar_one()
            cname = row.pop("constituency_name")
            ctype = row.pop("constituency_type", "lok_sabha")
            con = db.execute(
                select(Constituency).where(Constituency.name == cname, Constituency.type == ctype)
            ).scalar_one()
            existing = db.execute(
                select(Candidacy).where(
                    Candidacy.politician_id == pol.id,
                    Candidacy.constituency_id == con.id,
                    Candidacy.election_year == row["election_year"],
                )
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(Candidacy(politician_id=pol.id, constituency_id=con.id, **row))

        # 8. Manifesto items
        for row in _load("manifesto_items.json"):
            pol_name = row.pop("politician_name", None)
            pol_id = None
            if pol_name:
                pol = db.execute(select(Politician).where(Politician.name == pol_name)).scalar_one_or_none()
                pol_id = pol.id if pol else None
            existing = db.execute(
                select(ManifestoItem).where(
                    ManifestoItem.title == row["title"],
                    ManifestoItem.politician_id == pol_id,
                )
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(ManifestoItem(politician_id=pol_id, **row))

        db.commit()
        logger.info("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_all()
