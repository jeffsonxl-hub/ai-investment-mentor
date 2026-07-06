"""Deterministic pipeline steps -- build candidate list and score candidates.

These are plain async functions, not Agents. No LLM, no reasoning.
"""


async def build_candidates(market_context=None, events=None, watchlist=None) -> dict:
    """Build candidate list from market context and events. V1: returns empty stub."""
    return {"candidates": [], "count": 0, "source": "stub"}


async def score_candidates(candidates=None, market_context=None, watchlist_status=None) -> dict:
    """Score and rank candidates. V1: returns empty stub."""
    return {"scored": [], "top_pick": None, "source": "stub"}
