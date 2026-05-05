"""Step 4a: document type classification."""
from __future__ import annotations

from app.ai import ai_call

VALID_TYPES = {
    "press_release", "policy", "budget", "bill", "affidavit",
    "constituency_update", "local_update", "feedback", "unknown",
}


def classify(title: str | None, text: str) -> tuple[str, float]:
    result = ai_call("classify", title=title or "", excerpt=text[:1500])
    dtype = result.get("document_type", "unknown")
    if dtype not in VALID_TYPES:
        dtype = "unknown"
    confidence = float(result.get("confidence", 0.3))
    return dtype, max(0.0, min(1.0, confidence))
