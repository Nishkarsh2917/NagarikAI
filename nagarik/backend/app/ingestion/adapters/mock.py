"""
MockAdapter reads sample documents from data/seed/sample_documents.json so the
pipeline runs offline. Real adapters use this same shape.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.ingestion.adapters.base import BaseAdapter, FetchedItem


class MockAdapter(BaseAdapter):
    key = "mock"

    def fetch(self, source) -> list[FetchedItem]:  # type: ignore[override]
        seed_path = (
            Path(__file__).resolve().parents[4] / "data" / "seed" / "sample_documents.json"
        )
        if not seed_path.exists():
            return []
        with seed_path.open("r", encoding="utf-8") as f:
            samples = json.load(f)

        items: list[FetchedItem] = []
        for s in samples:
            # Each sample has its own source_slug; only return ours.
            if s.get("source_slug") != source.slug:
                continue
            published_at = None
            if s.get("published_at"):
                try:
                    published_at = datetime.fromisoformat(s["published_at"]).replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    pass
            html = (
                f"<html><head><title>{s['title']}</title></head>"
                f"<body><article>{s['body_html']}</article></body></html>"
            )
            items.append(
                FetchedItem(
                    source_url=s["source_url"],
                    title=s["title"],
                    raw_bytes=html.encode("utf-8"),
                    content_type="text/html",
                    published_at=published_at,
                )
            )
        return items
