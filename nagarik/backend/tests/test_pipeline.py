"""
End-to-end smoke test: seed → run pipeline → verify documents land published.

Run with:  cd backend && pytest -q
"""
from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import select


@pytest.fixture(scope="module", autouse=True)
def _isolate_env(tmp_path_factory):
    """Use a per-test SQLite DB and storage dir so we don't touch the dev DB."""
    tmp = tmp_path_factory.mktemp("nagarik_test")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/test.db"
    os.environ["STORAGE_LOCAL_PATH"] = str(tmp / "storage")
    os.environ["ENABLE_SCHEDULER"] = "false"
    # Force config reload
    from app.config import get_settings
    get_settings.cache_clear()
    # Force engine rebuild
    import importlib

    import app.db as db_module
    import app.storage as storage_module
    importlib.reload(db_module)
    importlib.reload(storage_module)
    yield


def test_pipeline_ingests_mock_documents():
    from app.db import SessionLocal
    from app.ingestion.pipeline import run_all
    from app.models import Document, Source, Summary
    from app.seed import seed_all

    seed_all()

    result = run_all()
    assert any(s["source"] == "mock-demo" for s in result["sources"])

    with SessionLocal() as db:
        docs = db.execute(select(Document)).scalars().all()
        assert len(docs) >= 5, f"Expected at least 5 ingested docs, got {len(docs)}"

        for d in docs:
            assert d.status == "published"
            assert d.checksum
            assert d.source_url
            assert 0.0 <= d.confidence_score <= 1.0

        # At least one English summary should exist for at least one doc.
        en_summaries = db.execute(
            select(Summary).where(Summary.language == "en")
        ).scalars().all()
        assert en_summaries, "Expected at least one English summary"

        # Mock source should be marked active.
        mock = db.execute(select(Source).where(Source.slug == "mock-demo")).scalar_one()
        assert mock.active is True


def test_rerunning_pipeline_is_idempotent():
    from app.db import SessionLocal
    from app.ingestion.pipeline import run_all
    from app.models import Document

    with SessionLocal() as db:
        before = db.execute(select(Document)).scalars().all()
        before_count = len(before)

    run_all()  # second run

    with SessionLocal() as db:
        after = db.execute(select(Document)).scalars().all()
        assert len(after) == before_count, "Pipeline must be idempotent on re-run"
