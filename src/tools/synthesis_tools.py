"""Synthesis Tools - multi-Component orchestration."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .tool import Tool, ToolParameter

if TYPE_CHECKING:
    from data.provider import DataProvider
    from memory.repository import MemoryRepository


def register_synthesis_tools(registry, provider: "DataProvider", memory: "MemoryRepository") -> None:
    registry.register(
        Tool(
            name="assess_market_regime",
            description="Gather all raw market data: indices, sectors, flow, macro in one call.",
            parameters=[ToolParameter("date", "string", "Analysis date YYYY-MM-DD")],
            func=lambda date, **kw: _assess_regime(provider, date),
            category="synthesis",
        )
    )
    registry.register(
        Tool(
            name="build_candidate_list",
            description="Build filtered candidate list. Applies market cap, ST, liquidity filters.",
            parameters=[
                ToolParameter("stock_universe", "array", "All A-share stocks with basic info"),
                ToolParameter("theme_sectors", "array", "Current leading theme sector names"),
            ],
            func=_build_candidates_impl,
            category="synthesis",
        )
    )
    registry.register(
        Tool(
            name="score_candidates",
            description="Score and rank candidates using multi-factor analysis.",
            parameters=[
                ToolParameter("candidates", "array", "Candidate stock dicts with evidence"),
                ToolParameter("market_context", "object", "Market context from assess_market_regime"),
                ToolParameter("watchlist_status", "object", "Watchlist status"),
            ],
            func=_score_impl,
            category="synthesis",
        )
    )
    registry.register(
        Tool(
            name="generate_narrative",
            description="Generate natural-language morning report narrative via LLM.",
            parameters=[
                ToolParameter("scored_candidates", "array", "Ranked candidates"),
                ToolParameter("market_context", "object", "Market context"),
            ],
            func=_narrative_impl,
            category="synthesis",
        )
    )
    registry.register(
        Tool(
            name="format_report",
            description="Format morning report as structured Markdown.",
            parameters=[ToolParameter("report_data", "object", "Full report data dict")],
            func=_format_report_impl,
            category="synthesis",
        )
    )
    registry.register(
        Tool(
            name="request_market_context",
            description="Request market context from Market Agent. V1: stub.",
            parameters=[ToolParameter("date", "string", "Analysis date")],
            func=lambda date, **kw: {"regime": "neutral", "confidence": 0.5, "source": "stub_market_agent"},
            category="synthesis",
        )
    )
    registry.register(
        Tool(
            name="request_events",
            description="Request events from Research Agent. V1: stub.",
            parameters=[ToolParameter("stock_codes", "array", "Stock codes or empty for market-wide")],
            func=lambda stock_codes=None, **kw: {"events": [], "source": "stub_research_agent"},
            category="synthesis",
        )
    )


async def _assess_regime(provider, date):
    indices = await provider.get_index_data("2026-06-01", date)
    sectors, flow, macro = await asyncio.gather(
        provider.get_sector_performance(), provider.get_northbound_flow(), provider.get_macro_indicators()
    )
    return {"date": date, "indices": indices, "sectors": sectors, "northbound_flow": flow, "macro": macro}


async def _build_candidates_impl(stock_universe, theme_sectors):
    if not stock_universe:
        return {"candidates": [], "count": 0, "filters_applied": []}
    theme_set = set(theme_sectors)
    filters = []
    candidates = stock_universe
    if any("market_cap" in s or "total_mv" in s for s in candidates[:1]):
        before = len(candidates)
        candidates = [
            s for s in candidates if (s.get("market_cap") or s.get("total_mv") or 0) >= 5_000_000_000
        ]  # noqa: E501
        filters.append(f"market_cap_5B:{before}->{len(candidates)}")
    if theme_set:
        before = len(candidates)
        candidates = [s for s in candidates if (s.get("industry") or s.get("sector") or "") in theme_set]
        filters.append(f"theme_sectors:{before}->{len(candidates)}")
    return {"candidates": candidates[:50], "count": len(candidates[:50]), "filters_applied": filters}


async def _score_impl(candidates, market_context=None, watchlist_status=None):
    if not candidates:
        return {"scored": [], "top_pick": None}
    scored = []
    for i, c in enumerate(candidates[:10]):
        code = c.get("code") or c.get("stock_code") or c.get("ts_code", f"unknown_{i}")
        name = c.get("name") or c.get("stock_name", "")
        scored.append(
            {
                "rank": i + 1,
                "stock_code": code,
                "stock_name": name,
                "score": 5.0,
                "score_breakdown": {
                    "fundamental": 5.0,
                    "technical": 5.0,
                    "news_sentiment": 5.0,
                    "capital_flow": 5.0,
                    "watchlist_priority": 5.0,
                    "theme_alignment": 5.0,
                },
            }
        )
    return {"scored": scored, "top_pick": scored[0] if scored else None}


async def _narrative_impl(scored_candidates, market_context=None, llm_client=None, **kw):
    if llm_client is None:
        return {"narrative": "Narrative generation requires an LLM client.", "source": "stub"}
    regime = (market_context or {}).get("regime", "unknown")
    ct = "\n".join(
        f"#{c['rank']} {c.get('stock_name', '')} ({c.get('stock_code', '')}): score {c.get('score', 0):.1f}"
        for c in scored_candidates[:5]
    )  # noqa: E501
    prompt = f"Write a concise morning market report narrative.\nMarket regime: {regime}\nTop candidates:\n{ct}\n\nInclude: market summary paragraph, one paragraph per candidate (thesis+evidence+risks), and one learning point."  # noqa: E501
    try:
        return {"narrative": await llm_client(prompt), "source": "llm"}
    except Exception:
        return {"narrative": "Narrative generation failed.", "source": "stub"}


async def _format_report_impl(report_data):
    return {"markdown": _md(report_data), "format": "markdown"}


def _md(data):
    lines = [f"# Morning Report - {data.get('report_date', 'Unknown')}", ""]
    market = data.get("market_summary", {})
    if market:
        lines.append("## Market Summary")
        lines.append(f"**Regime:** {market.get('regime', 'N/A')}")
        lines.append(market.get("narrative", ""))
        if market.get("risk_warning"):
            lines.append(f"> **Risk Warning:** {market['risk_warning']}")
        lines.append("")
    for c in data.get("candidates", []):
        lines.append(f"### #{c.get('rank', '?')} {c.get('stock_name', '')} ({c.get('stock_code', '')})")
        lines.append(f"**Score:** {c.get('score', 0):.1f}/10 | **Confidence:** {c.get('confidence', 0):.0%}")
        if c.get("thesis"):
            lines.append(f"**Thesis:** {c['thesis']}")
        if c.get("risks"):
            lines.append("**Risks:** " + "; ".join(c["risks"]))
        lines.append("")
    dd = data.get("deep_dive")
    if dd:
        lines.append("## Deep Dive")
        lines.append(f"### {dd.get('stock_name', '')} ({dd.get('stock_code', '')})")
        for k in (
            "business_summary",
            "catalyst",
            "valuation_context",
            "risk_scenario",
            "price_zone",
            "invalidation",
        ):  # noqa: E501
            if dd.get(k):
                lines.append(f"**{k.replace('_', ' ').title()}:** {dd[k]}")
        lines.append("")
    if data.get("learning_point"):
        lines.append("## Today's Learning Point")
        lines.append(data["learning_point"])
        lines.append("")
    if data.get("watchlist_alerts"):
        lines.append("## Watchlist Alerts")
        for a in data["watchlist_alerts"]:
            lines.append(f"- {a}")
        lines.append("")
    return "\n".join(lines)
