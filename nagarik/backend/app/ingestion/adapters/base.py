"""Adapter contract. All source adapters must conform."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from app.models import Source


class FetchedItem(TypedDict, total=False):
    source_url: str           # required
    title: str | None
    raw_bytes: bytes          # required
    content_type: str         # required: text/html | application/pdf | application/json
    published_at: datetime | None


class BaseAdapter:
    """
    Subclasses set `key` to match `source.adapter_key`. The pipeline calls `fetch(source)`
    once per scheduled tick and gets a list of items to ingest. Implementations should:

      - Be idempotent: returning the same payload twice should produce no duplicates
        (the pipeline dedupes on checksum, but adapters should still avoid hammering).
      - Be polite: respect robots.txt and rate-limit when scraping.
      - Save raw bytes verbatim — the pipeline persists them before parsing.
      - Surface partial failures by returning what they could and raising for total failure.
    """
    key: str = ""

    def fetch(self, source: "Source") -> list[FetchedItem]:
        raise NotImplementedError
