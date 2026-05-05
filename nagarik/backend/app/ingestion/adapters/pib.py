"""
Press Information Bureau adapter. Scaffolded shape — flip on by setting the
correct feed URL in the Source row's `config_json` and activating the source.

The implementation pattern is: read RSS index → fetch each article HTML →
return as raw HTML bytes. The pipeline does the rest.
"""
from __future__ import annotations

import logging
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from app.ingestion.adapters.base import BaseAdapter, FetchedItem

logger = logging.getLogger(__name__)


class PIBAdapter(BaseAdapter):
    key = "pib"

    DEFAULT_FEED = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"

    def fetch(self, source) -> list[FetchedItem]:  # type: ignore[override]
        cfg = source.config_json or {}
        feed_url = cfg.get("feed_url", self.DEFAULT_FEED)
        max_items = int(cfg.get("max_items", 20))

        items: list[FetchedItem] = []
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as e:
            logger.error("PIB feed parse failed: %s", e)
            return items

        with httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": "NagarikBot/0.1"}) as client:
            for entry in parsed.entries[:max_items]:
                url = entry.get("link")
                if not url:
                    continue
                try:
                    resp = client.get(url)
                    resp.raise_for_status()
                except Exception as e:
                    logger.warning("PIB fetch failed for %s: %s", url, e)
                    continue

                published_at: datetime | None = None
                if entry.get("published"):
                    try:
                        published_at = parsedate_to_datetime(entry["published"])
                    except (TypeError, ValueError):
                        pass

                items.append(
                    FetchedItem(
                        source_url=url,
                        title=entry.get("title"),
                        raw_bytes=resp.content,
                        content_type=resp.headers.get("content-type", "text/html").split(";")[0],
                        published_at=published_at,
                    )
                )
        return items
