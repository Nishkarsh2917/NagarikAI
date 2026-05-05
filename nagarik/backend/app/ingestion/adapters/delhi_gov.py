"""
Delhi Government press releases adapter. Scaffold for local sources.

The configurable HTML-list pattern is reusable for many state department pages:
provide a list URL + CSS selectors for items, links, and dates.
"""
from __future__ import annotations

import logging
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.ingestion.adapters.base import BaseAdapter, FetchedItem

logger = logging.getLogger(__name__)


class DelhiGovAdapter(BaseAdapter):
    key = "delhi_gov_local"

    def fetch(self, source) -> list[FetchedItem]:  # type: ignore[override]
        cfg = source.config_json or {}
        list_url = cfg.get("list_url")
        if not list_url:
            logger.info("DelhiGov adapter: no list_url configured; skipping.")
            return []

        item_selector = cfg.get("item_selector", "a")
        max_items = int(cfg.get("max_items", 20))

        items: list[FetchedItem] = []
        with httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": "NagarikBot/0.1"}) as client:
            try:
                list_resp = client.get(list_url)
                list_resp.raise_for_status()
            except Exception as e:
                logger.error("DelhiGov list fetch failed: %s", e)
                return items

            soup = BeautifulSoup(list_resp.content, "lxml")
            anchors = soup.select(item_selector)[:max_items]

            for a in anchors:
                href = a.get("href")
                if not href:
                    continue
                full_url = urljoin(list_url, href)
                title = a.get_text(strip=True) or None
                try:
                    resp = client.get(full_url)
                    resp.raise_for_status()
                except Exception as e:
                    logger.warning("DelhiGov item fetch failed for %s: %s", full_url, e)
                    continue
                items.append(
                    FetchedItem(
                        source_url=full_url,
                        title=title,
                        raw_bytes=resp.content,
                        content_type=resp.headers.get("content-type", "text/html").split(";")[0],
                        published_at=None,
                    )
                )
        return items
