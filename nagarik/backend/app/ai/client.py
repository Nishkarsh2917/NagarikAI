"""
Single entry point for AI calls. If ANTHROPIC_API_KEY is set we call Claude with
JSON-mode prompts; otherwise we fall back to deterministic rules so the demo still
runs end-to-end.

The function name is intentionally generic — `ai_call(step, **kwargs)` — so the
pipeline doesn't care which backend ran.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.ai import prompts
from app.ai.rule_based import RuleBasedFallback
from app.config import get_settings

logger = logging.getLogger(__name__)


# Lazy import: anthropic package is optional at runtime.
def _get_anthropic_client():
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _llm_json(prompt: str, max_tokens: int = 1024) -> dict[str, Any] | None:
    """Call the LLM expecting a JSON object back. Returns None on any failure."""
    client = _get_anthropic_client()
    if client is None:
        return None
    settings = get_settings()
    try:
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))  # type: ignore[attr-defined]
        # Tolerate a stray code fence.
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        logger.warning("LLM JSON call failed: %s", e)
        return None


def _model_id() -> str:
    settings = get_settings()
    return settings.anthropic_model if settings.anthropic_api_key else "rule-based-fallback"


def ai_call(step: str, **kwargs: Any) -> dict[str, Any]:
    """
    Dispatch to the right prompt + parser per pipeline step.
    Falls back to rule_based on any failure. Always returns a dict.
    """
    if step == "classify":
        title = kwargs.get("title", "")
        excerpt = (kwargs.get("excerpt", "") or "")[:1500]
        result = _llm_json(prompts.CLASSIFY_PROMPT.format(title=title, excerpt=excerpt))
        if result is None or "document_type" not in result:
            result = RuleBasedFallback.classify(title, excerpt)
        result["_model"] = _model_id()
        return result

    if step == "extract":
        title = kwargs.get("title", "")
        text = (kwargs.get("text", "") or "")[:8000]
        result = _llm_json(prompts.EXTRACT_PROMPT.format(title=title, text=text), max_tokens=1500)
        if result is None or "what" not in result:
            result = RuleBasedFallback.extract(title, text)
        result["_model"] = _model_id()
        return result

    if step == "summarize":
        title = kwargs.get("title", "")
        text = (kwargs.get("text", "") or "")[:8000]
        language = kwargs.get("language", "en")
        prompt = (prompts.SUMMARIZE_PROMPT_HI if language == "hi" else prompts.SUMMARIZE_PROMPT_EN).format(
            title=title, text=text
        )
        result = _llm_json(prompt, max_tokens=1500)
        if result is None or "one_line" not in result:
            result = RuleBasedFallback.summarize(title, text, language)
        result["_model"] = _model_id()
        return result

    if step == "map_topic":
        title = kwargs.get("title", "")
        excerpt = (kwargs.get("excerpt", "") or "")[:1500]
        topic_list = kwargs.get("topic_list", [])
        prompt = prompts.MAP_TOPIC_PROMPT.format(
            title=title, excerpt=excerpt, topic_list=", ".join(topic_list)
        )
        result = _llm_json(prompt)
        if result is None or "topics" not in result:
            result = RuleBasedFallback.map_topic(title, excerpt, topic_list)
        result["_model"] = _model_id()
        return result

    if step == "cluster_feedback":
        messages = kwargs.get("messages", [])
        joined = "\n---\n".join(messages[:50])
        prompt = prompts.CLUSTER_FEEDBACK_PROMPT.format(messages=joined)
        result = _llm_json(prompt)
        if result is None or "summary" not in result:
            result = RuleBasedFallback.cluster_feedback(messages)
        result["_model"] = _model_id()
        return result

    raise ValueError(f"Unknown AI step: {step}")
