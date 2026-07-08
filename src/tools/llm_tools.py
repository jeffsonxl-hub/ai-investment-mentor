"""LLM-Powered Tools - deterministic wrappers with internal LLM calls."""

from __future__ import annotations

from .tool import Tool, ToolParameter

_EVENT_TYPES = [
    "earnings_guidance",
    "policy_impact",
    "product_news",
    "management_change",
    "industry_trend",
    "other",
]  # noqa: E501


def register_llm_tools(registry) -> None:
    registry.register(
        Tool(
            name="summarize_article",
            description="Summarize a financial news article into structured format.",
            parameters=[
                ToolParameter("url", "string", "Source URL"),
                ToolParameter("text", "string", "Article text"),
            ],
            func=_summarize_impl,
            category="llm_powered",
        )
    )
    registry.register(
        Tool(
            name="classify_sentiment",
            description="Classify sentiment as positive, negative, or neutral with confidence.",
            parameters=[ToolParameter("text", "string", "Text to classify")],
            func=_sentiment_impl,
            category="llm_powered",
        )
    )
    registry.register(
        Tool(
            name="extract_keywords",
            description="Extract investment-relevant keywords from text.",
            parameters=[
                ToolParameter("text", "string", "Input text"),
                ToolParameter("max_keywords", "integer", "Max count", required=False, default=10),
            ],  # noqa: E501
            func=_keywords_impl,
            category="llm_powered",
        )
    )
    registry.register(
        Tool(
            name="classify_event_type",
            description="Classify a financial event: earnings guidance, policy impact, product news, management change, industry trend, or other.",  # noqa: E501
            parameters=[ToolParameter("text", "string", "Event description text")],
            func=_event_type_impl,
            category="llm_powered",
        )
    )


async def _summarize_impl(url, text, llm_client=None, **kw):
    if llm_client is None:
        return {"error": "llm_client not available"}
    try:
        result = await llm_client(
            "Summarize this financial article. Return JSON with title, key_points, entities.\n\n"
            + text[:4000]  # noqa: E501
        )
        return _parse(result)
    except Exception:
        return {"error": "summarization failed", "raw_text": text[:500]}


async def _sentiment_impl(text, llm_client=None, **kw):
    if llm_client is None:
        return {"error": "llm_client not available"}
    try:
        result = await llm_client(
            'Classify sentiment. Return JSON: {"sentiment":"positive|negative|neutral","confidence":0.0-1.0}\n\n'  # noqa: E501
            + text[:2000]
        )
        return _parse(result)
    except Exception:
        return {"sentiment": "neutral", "confidence": 0.0, "error": "classification failed"}


async def _keywords_impl(text, max_keywords=10, llm_client=None, **kw):
    if llm_client is None:
        return {"error": "llm_client not available"}
    try:
        result = await llm_client(
            "Extract up to " + str(max_keywords) + " keywords. Return JSON: keywords list.\n\n" + text[:3000]
        )  # noqa: E501
        return _parse(result)
    except Exception:
        return {"keywords": [], "error": "extraction failed"}


async def _event_type_impl(text, llm_client=None, **kw):
    if llm_client is None:
        return {"error": "llm_client not available"}
    try:
        result = await llm_client(
            "Classify financial event type: "
            + ", ".join(_EVENT_TYPES)
            + ". Return JSON: event_type, confidence.\n\n"
            + text[:2000]  # noqa: E501
        )
        parsed = _parse(result)
        if isinstance(parsed, dict) and parsed.get("event_type") not in _EVENT_TYPES:
            parsed["event_type"] = "other"
        return parsed
    except Exception:
        return {"event_type": "other", "confidence": 0.0}


def _parse(raw):
    import json

    try:
        text = raw.strip()
        if "```" in text:
            s = text.find("{")
            e = text.rfind("}")
            if s >= 0 and e > s:
                text = text[s : e + 1]
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {"raw": raw}
