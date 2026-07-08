""" "Data Tools - wrap DataProvider methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .tool import Tool, ToolParameter

if TYPE_CHECKING:
    from data.provider import DataProvider

_INDEX_ENUM = ["sh000001", "sz399001", "sz399006", "sh000688"]


def register_data_tools(registry, provider: "DataProvider") -> None:
    registry.register(
        Tool(
            name="get_index_data",
            description="Fetch daily OHLCV for major A-share indices. Use for market direction assessment.",
            parameters=[
                ToolParameter("symbol", "string", "Index symbol", enum=_INDEX_ENUM),
                ToolParameter("start_date", "string", "Start date YYYY-MM-DD", required=False),
                ToolParameter("end_date", "string", "End date YYYY-MM-DD"),
            ],
            func=lambda symbol, end_date, start_date=None, **kw: provider.get_index_data(
                start_date or "2020-01-01", end_date
            ),  # noqa: E501
            category="data",
        )
    )
    registry.register(
        Tool(
            name="get_sector_performance",
            description="Fetch sector-level performance across A-share industries.",
            parameters=[],
            func=lambda **kw: provider.get_sector_performance(),
            category="data",
        )
    )
    registry.register(
        Tool(
            name="get_northbound_flow",
            description="Fetch north-bound capital flow via Stock Connect.",
            parameters=[ToolParameter("days", "integer", "Recent days", required=False, default=5)],
            func=lambda days=5, **kw: provider.get_northbound_flow(),
            category="data",
        )
    )
    registry.register(
        Tool(
            name="get_macro_indicators",
            description="Fetch macro indicators: SHIBOR, PMI, CPI.",
            parameters=[],
            func=lambda **kw: provider.get_macro_indicators(),
            category="data",
        )
    )
    registry.register(
        Tool(
            name="get_fundamentals",
            description="Fetch fundamental snapshot for stocks: PE, PB, market cap.",
            parameters=[
                ToolParameter("stock_codes", "array", "List of 6-digit stock codes"),
                ToolParameter("date", "string", "Analysis date YYYY-MM-DD"),
            ],
            func=lambda stock_codes, date, **kw: provider.get_fundamental_snapshot(stock_codes, date),
            category="data",
        )
    )
    registry.register(
        Tool(
            name="get_stock_basic_info",
            description="Fetch full A-share stock list with name, industry, listing date.",
            parameters=[],
            func=lambda **kw: provider.get_stock_basic_info(),
            category="data",
        )
    )
    registry.register(
        Tool(
            name="get_stock_price_history",
            description="Fetch daily OHLCV history for a single stock.",
            parameters=[
                ToolParameter("stock_code", "string", "6-digit stock code"),
                ToolParameter("start_date", "string", "Start date", required=False),
                ToolParameter("end_date", "string", "End date"),
            ],
            func=lambda stock_code, end_date, start_date=None, **kw: provider.get_index_data(
                start_date or "2020-01-01", end_date
            ),  # noqa: E501
            category="data",
        )
    )
    registry.register(
        Tool(
            name="fetch_news",
            description="Fetch recent financial news for a stock.",
            parameters=[
                ToolParameter("stock_code", "string", "6-digit stock code"),
                ToolParameter("limit", "integer", "Max articles", required=False),
            ],
            func=lambda stock_code, limit=20, **kw: provider.get_stock_news(stock_code, limit),
            category="data",
        )
    )
    registry.register(
        Tool(
            name="fetch_announcements",
            description="Fetch recent company announcements.",
            parameters=[
                ToolParameter("stock_code", "string", "6-digit stock code"),
                ToolParameter("limit", "integer", "Max announcements", required=False),
            ],
            func=lambda stock_code, limit=20, **kw: provider.get_announcements(stock_code, limit),
            category="data",
        )
    )
