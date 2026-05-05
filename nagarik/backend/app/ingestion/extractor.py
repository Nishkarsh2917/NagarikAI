"""Step 4b: structured fact extraction."""
from __future__ import annotations

from typing import Any

from app.ai import ai_call


# These keys mirror the ExtractedFact rows we'll create in the DB.
SCALAR_KEYS = ["who", "what", "where", "when", "affected_group"]
LIST_KEYS = ["key_numbers", "deadlines", "actions_required", "named_entities"]


def extract(title: str | None, text: str) -> tuple[list[dict[str, Any]], float]:
    """
    Returns (facts, confidence). Each fact is {key, value, confidence}.
    Lists are flattened to one fact per key with comma-joined value (the UI table treats it as text).
    """
    result = ai_call("extract", title=title or "", text=text)
    confidence = float(result.get("confidence", 0.3))

    facts: list[dict[str, Any]] = []
    for k in SCALAR_KEYS:
        v = result.get(k)
        if v is not None and str(v).strip():
            facts.append({"key": k, "value": str(v).strip(), "confidence": confidence})

    for k in LIST_KEYS:
        v = result.get(k) or []
        if isinstance(v, list) and v:
            joined = ", ".join(str(x).strip() for x in v if str(x).strip())
            if joined:
                facts.append({"key": k, "value": joined, "confidence": confidence})

    return facts, max(0.0, min(1.0, confidence))
