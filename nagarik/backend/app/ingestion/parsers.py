"""
Parse raw payloads into clean text + best-effort title.

Order of operations:
  1) Try fast text extraction per content type.
  2) If text comes out empty, try a fallback (OCR is a planned hook, not in MVP deps).
"""
from __future__ import annotations

import io
import logging
import re

from bs4 import BeautifulSoup
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def parse(raw: bytes, content_type: str) -> tuple[str | None, str]:
    """
    Returns (title, extracted_text). Either may be empty/None.
    """
    if "html" in content_type:
        return _parse_html(raw)
    if "pdf" in content_type:
        return _parse_pdf(raw)
    if "json" in content_type:
        # JSON payloads are pre-structured; we keep them as text.
        return None, raw.decode("utf-8", errors="ignore")
    # plain text fallback
    return None, raw.decode("utf-8", errors="ignore")


def _parse_html(raw: bytes) -> tuple[str | None, str]:
    soup = BeautifulSoup(raw, "lxml")

    # Strip noise.
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.h1:
        title = soup.h1.get_text(strip=True)

    # Prefer <main> / <article>; fall back to <body>.
    body = soup.find("main") or soup.find("article") or soup.body or soup
    text = body.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return title, text


def _parse_pdf(raw: bytes) -> tuple[str | None, str]:
    try:
        reader = PdfReader(io.BytesIO(raw))
        title = None
        if reader.metadata and reader.metadata.title:
            title = str(reader.metadata.title).strip() or None
        chunks: list[str] = []
        for page in reader.pages:
            try:
                chunks.append(page.extract_text() or "")
            except Exception as e:  # noqa: BLE001 — per-page resilience
                logger.warning("PDF page extract failed: %s", e)
        text = "\n\n".join(c for c in chunks if c).strip()
        # OCR hook would land here when text is empty — out of MVP scope but the
        # signature is ready: text = ocr_pdf(raw) if not text else text
        return title, text
    except Exception as e:
        logger.error("PDF parse failed entirely: %s", e)
        return None, ""


def detect_language(text: str) -> str:
    """
    Cheap language guess. Devanagari → hi, otherwise en. Sufficient for MVP labelling.
    A real implementation would use fasttext/lingua.
    """
    if not text:
        return "en"
    devanagari = sum(1 for c in text[:1000] if "\u0900" <= c <= "\u097F")
    return "hi" if devanagari > 30 else "en"
