"""Step 5: plain-language summary generation. EN + HI as separate calls."""
from __future__ import annotations

from typing import Any

from app.ai import ai_call


def summarize(title: str | None, text: str, language: str = "en") -> dict[str, Any]:
    """
    Returns a dict shaped to fit the Summary model:
      one_line, three_bullets_json, why_it_matters, who_is_affected, confidence_score, model_used
    """
    result = ai_call("summarize", title=title or "", text=text, language=language)

    bullets = result.get("three_bullets") or []
    if isinstance(bullets, list):
        bullets = [str(b) for b in bullets][:3]
    else:
        bullets = []

    return {
        "language": language,
        "one_line": str(result.get("one_line") or "").strip() or None,
        "three_bullets_json": bullets if bullets else None,
        "why_it_matters": str(result.get("why_it_matters") or "").strip() or None,
        "who_is_affected": str(result.get("who_is_affected") or "").strip() or None,
        "confidence_score": max(0.0, min(1.0, float(result.get("confidence", 0.3)))),
        "model_used": str(result.get("_model", "unknown")),
    }
