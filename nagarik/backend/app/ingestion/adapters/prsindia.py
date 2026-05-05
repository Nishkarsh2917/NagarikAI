"""
PRS Legislative Research adapter. PRS publishes high-quality bill/act summaries
and the underlying PDFs. We treat them as a third-party-but-high-trust source.
"""
from __future__ import annotations

import logging
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from app.ingestion.adapters.base import BaseAdapter, FetchedItem

logger = logging.getLogger(__name__)


class PRSIndiaAdapter(BaseAdapter):
    key = "prsindia"

    DEFAULT_FEED = "https://prsindia.org/rss"  # placeholder — confirm URL on activation

    def fetch(self, source) -> list[FetchedItem]:  # type: ignore[override]
        cfg = source.config_json or {}
        feed_url = cfg.get("feed_url", self.DEFAULT_FEED)
        max_items = int(cfg.get("max_items", 15))

        items: list[FetchedItem] = []
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as e:
            logger.error("PRS feed parse failed: %s", e)
            return items

        with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "NagarikBot/0.1"}) as client:
            for entry in parsed.entries[:max_items]:
                url = entry.get("link")
                if not url:
                    continue
                try:
                    resp = client.get(url)
                    resp.raise_for_status()
                except Exception as e:
                    logger.warning("PRS fetch failed for %s: %s", url, e)
                    continue

                published_at: datetime | None = None
                if entry.get("published"):
                    try:
                        published_at = parsedate_to_datetime(entry["published"])
                    except (TypeError, ValueError):
                        pass

                content_type = resp.headers.get("content-type", "text/html").split(";")[0]
                items.append(
                    FetchedItem(
                        source_url=url,
                        title=entry.get("title"),
                        raw_bytes=resp.content,
                        content_type=content_type,
                        published_at=published_at,
                    )
                )
        return items
