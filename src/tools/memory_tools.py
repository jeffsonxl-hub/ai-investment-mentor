"""Memory Tools - wrap MemoryRepository (5 read + 3 write)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .tool import Tool, ToolParameter

if TYPE_CHECKING:
    from memory.repository import MemoryRepository


def register_memory_tools(registry, memory: "MemoryRepository") -> None:
    registry.register(
        Tool(
            name="get_watchlist",
            description="Fetch the user active watchlist.",
            parameters=[],
            func=lambda **kw: memory.get_watchlist(),
            category="memory",
        )
    )
    registry.register(
        Tool(
            name="get_watchlist_entry",
            description="Fetch a single watchlist entry by stock code.",
            parameters=[ToolParameter("stock_code", "string", "6-digit stock code")],
            func=lambda stock_code, **kw: memory.get_watchlist_entry(stock_code),
            category="memory",
        )
    )
    registry.register(
        Tool(
            name="get_recent_decisions",
            description="Fetch past recommendations.",
            parameters=[ToolParameter("days", "integer", "Days to look back", required=False, default=5)],
            func=lambda days=5, **kw: memory.get_recent_decisions(days),
            category="memory",
        )
    )
    registry.register(
        Tool(
            name="get_rejected_stocks",
            description="Fetch stocks the user has rejected.",
            parameters=[ToolParameter("days", "integer", "Days to look back", required=False, default=20)],
            func=lambda days=20, **kw: memory.get_rejected_stocks(days),
            category="memory",
        )
    )
    registry.register(
        Tool(
            name="get_market_history",
            description="Fetch recent market snapshots.",
            parameters=[ToolParameter("days", "integer", "Days to look back", required=False, default=20)],
            func=lambda days=20, **kw: memory.get_market_snapshot_range(_days_ago(days), _today_str()),
            category="memory",
        )
    )
    registry.register(
        Tool(
            name="save_market_snapshot",
            description="Save market analysis snapshot to memory.",
            parameters=[ToolParameter("snapshot", "object", "Market snapshot dict")],
            func=lambda snapshot, **kw: _write(memory.save_market_snapshot, snapshot),
            category="memory",
        )
    )
    registry.register(
        Tool(
            name="save_decision",
            description="Save a recommendation decision to memory.",
            parameters=[ToolParameter("decision", "object", "Decision dict")],
            func=lambda decision, **kw: _write(memory.save_decision, decision),
            category="memory",
        )
    )
    # NOTE: MemoryRepository.save_decision() filters unknown columns against
    # the decisions table schema. If the LLM includes V2-only fields like
    # user_feedback, they are silently dropped by MemoryRepository.
    # No explicit whitelist needed here — schema enforcement is the Component's job.
    registry.register(
        Tool(
            name="update_watchlist_entry",
            description="Update a watchlist entry priority.",
            parameters=[
                ToolParameter("stock_code", "string", "6-digit stock code"),
                ToolParameter("priority", "string", "Priority", enum=["high", "medium", "low"]),
            ],
            func=lambda stock_code, priority, **kw: _write(
                memory.update_watchlist_priority, stock_code, priority
            ),
            category="memory",
        )
    )


async def _write(method, *args):
    method(*args)


def _today_str():
    from datetime import date

    return date.today().isoformat()


def _days_ago(n):
    from datetime import date, timedelta

    return (date.today() - timedelta(days=n)).isoformat()
