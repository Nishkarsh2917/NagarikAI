"""
Election Commission affidavit adapter. Scaffolded.

Real activation: point `config_json.feed_url` at a JSON manifest of affidavits for
a given election cycle. The pipeline will fetch each affidavit PDF.
"""
from __future__ import annotations

import json
import logging

import httpx

from app.ingestion.adapters.base import BaseAdapter, FetchedItem

logger = logging.getLogger(__name__)


class ECIAffidavitsAdapter(BaseAdapter):
    key = "eci_affidavits"

    def fetch(self, source) -> list[FetchedItem]:  # type: ignore[override]
        cfg = source.config_json or {}
        manifest_url = cfg.get("manifest_url")
        if not manifest_url:
            logger.info("ECI adapter: no manifest_url configured; skipping.")
            return []

        items: list[FetchedItem] = []
        with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "NagarikBot/0.1"}) as client:
            try:
                manifest_resp = client.get(manifest_url)
                manifest_resp.raise_for_status()
                manifest = json.loads(manifest_resp.content)
            except Exception as e:
                logger.error("ECI manifest fetch failed: %s", e)
                return items

            for entry in manifest.get("affidavits", []):
                url = entry.get("pdf_url")
                if not url:
                    continue
                try:
                    resp = client.get(url)
                    resp.raise_for_status()
                except Exception as e:
                    logger.warning("ECI affidavit fetch failed for %s: %s", url, e)
                    continue

                items.append(
                    FetchedItem(
                        source_url=url,
                        title=entry.get("candidate_name"),
                        raw_bytes=resp.content,
                        content_type="application/pdf",
                        published_at=None,
                    )
                )
        return items
