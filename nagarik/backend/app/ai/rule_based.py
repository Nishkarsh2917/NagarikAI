"""
Deterministic, dependency-free fallbacks for every AI step.

Why this exists: the demo MUST run without an API key. Quality is intentionally
modest — we extract what's findable with regex/heuristics and label everything
with low confidence so the UI can flag it as `tentative`.
"""
from __future__ import annotations

import re
from typing import Any


_DOC_TYPE_KEYWORDS = {
    "press_release": ["press release", "press information", "pib delhi", "ministry of"],
    "budget": ["budget", "fiscal year", "appropriation", "expenditure outlay"],
    "bill": ["the bill", "act, 20", "amendment bill", "passed by"],
    "affidavit": ["affidavit", "form 26", "criminal cases", "assets and liabilities"],
    "policy": ["policy", "guidelines", "framework", "scheme"],
    "constituency_update": ["constituency", "voter", "polling station"],
    "local_update": ["municipal", "district magistrate", "ward"],
}

_NUMBER_RE = re.compile(r"(?:Rs\.?|₹|INR)\s?[\d,]+(?:\.\d+)?(?:\s?(?:crore|lakh|million|billion))?", re.I)
_DATE_RE = re.compile(
    r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+)?(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{2,4}\b",
    re.I,
)
_DEADLINE_RE = re.compile(
    r"(?:by|before|deadline|last date|on or before)\s+[^.,;\n]{4,80}", re.I
)


class RuleBasedFallback:
    """Mirrors the JSON shapes produced by the LLM prompts. Low-confidence by design."""

    @staticmethod
    def classify(title: str, excerpt: str) -> dict[str, Any]:
        text = (title + " " + excerpt).lower()
        for dtype, keywords in _DOC_TYPE_KEYWORDS.items():
            if any(k in text for k in keywords):
                return {"document_type": dtype, "confidence": 0.4}
        return {"document_type": "unknown", "confidence": 0.2}

    @staticmethod
    def extract(title: str, text: str) -> dict[str, Any]:
        sentences = _split_sentences(text)
        first = sentences[0] if sentences else ""
        return {
            "who": _first_match(text, [r"Ministry of [A-Z][\w &]+", r"Government of [A-Z][\w]+"]),
            "what": (first[:120] if first else None),
            "where": _first_match(text, [r"in\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})"]),
            "when": (_DATE_RE.search(text).group(0) if _DATE_RE.search(text) else None),
            "affected_group": None,
            "key_numbers": _NUMBER_RE.findall(text)[:5],
            "deadlines": [m.group(0) for m in _DEADLINE_RE.finditer(text)][:3],
            "actions_required": [],
            "named_entities": _extract_entities(text)[:8],
            "confidence": 0.35,
        }

    @staticmethod
    def summarize(title: str, text: str, language: str = "en") -> dict[str, Any]:
        sentences = _split_sentences(text)
        if not sentences:
            return {
                "one_line": title or "Document with no extractable text.",
                "three_bullets": ["No text could be extracted.", "See original source.", "Confidence is low."],
                "why_it_matters": "Original source contains the authoritative version.",
                "who_is_affected": "Unknown — see source.",
                "confidence": 0.1,
            }
        one_line = sentences[0][:240]
        bullets = [s[:200] for s in sentences[:3]]
        while len(bullets) < 3:
            bullets.append("See original source for further details.")
        return {
            "one_line": one_line,
            "three_bullets": bullets,
            "why_it_matters": (sentences[1] if len(sentences) > 1 else one_line)[:240],
            "who_is_affected": "See original source for affected groups.",
            "confidence": 0.3,
        }

    @staticmethod
    def map_topic(title: str, excerpt: str, topic_list: list[str]) -> dict[str, Any]:
        text = (title + " " + excerpt).lower()
        topics = [t for t in topic_list if t.lower() in text][:3]
        # No reliable geography heuristic without a gazetteer — leave nulls.
        return {
            "topics": topics,
            "state": None,
            "district": None,
            "constituency": None,
            "confidence": 0.3 if topics else 0.15,
        }

    @staticmethod
    def cluster_feedback(messages: list[str]) -> dict[str, Any]:
        if not messages:
            return {
                "summary": "No feedback received.",
                "recurring_complaints": [],
                "suggested_actions": [],
                "confidence": 0.1,
            }
        # Naive: pick the most common 4-word phrase as the recurring theme.
        phrases: dict[str, int] = {}
        for m in messages:
            words = re.findall(r"\w+", m.lower())
            for i in range(len(words) - 3):
                p = " ".join(words[i : i + 4])
                phrases[p] = phrases.get(p, 0) + 1
        recurring = [p for p, c in sorted(phrases.items(), key=lambda x: -x[1])[:3] if c > 1]
        return {
            "summary": f"{len(messages)} citizens submitted feedback. Common themes are listed below.",
            "recurring_complaints": recurring,
            "suggested_actions": [],
            "confidence": 0.25,
        }


# ---- helpers ----
def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def _first_match(text: str, patterns: list[str]) -> str | None:
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0)
    return None


def _extract_entities(text: str) -> list[str]:
    # Title-cased multi-word phrases — crude proper-noun heuristic.
    candidates = re.findall(r"\b(?:[A-Z][a-z]+\s){1,3}[A-Z][a-z]+\b", text)
    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        c = c.strip()
        if c not in seen and len(c) > 4:
            seen.add(c)
            out.append(c)
    return out
