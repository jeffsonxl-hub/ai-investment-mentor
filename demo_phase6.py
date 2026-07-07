"""Phase 6 demo — create ToolRegistry and run key Tools."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import load_config
from data.ak_share_client import AkShareClient
from data.provider import DataProvider
from memory.repository import MemoryRepository
from tools.factory import create_tool_registry

async def main():
    cfg = load_config()
    memory = MemoryRepository(cfg.db_path); memory.initialize()
    ak = AkShareClient()
    provider = DataProvider(ak, memory)
    registry = create_tool_registry(provider, memory)

    print(f"=== Phase 6: Tool Layer ===")
    print(f"{registry.tool_count} tools registered\n")

    # Show per-agent tool counts
    for agent, tools in {
        "Market": ["get_index_data","get_sector_performance","get_northbound_flow",
            "get_macro_indicators","get_stock_basic_info","calculate_rsi","calculate_macd",
            "calculate_moving_averages","calculate_bollinger_bands","calculate_volume_profile",
            "get_market_history","save_market_snapshot","assess_market_regime"],
        "Research": ["get_stock_basic_info","get_stock_price_history","fetch_news",
            "fetch_announcements","summarize_article","classify_sentiment",
            "extract_keywords","classify_event_type","get_recent_decisions"],
        "Watchlist": ["get_watchlist","get_watchlist_entry","get_stock_basic_info",
            "get_stock_price_history","get_fundamentals","calculate_rsi","calculate_macd",
            "calculate_moving_averages","calculate_bollinger_bands","calculate_volume_profile",
            "calculate_returns","update_watchlist_entry"],
        "Advisor": ["build_candidate_list","score_candidates","generate_narrative",
            "format_report","request_market_context","request_events","get_fundamentals",
            "get_recent_decisions","get_rejected_stocks","save_decision"],
    }.items():
        schemas = registry.export_for_llm(tools)
        print(f"  {agent}: {len(schemas)} tools")

    # Run analysis tools on sample prices
    prices = [100+i*0.5 for i in range(30)]
    rsi = await registry.execute("calculate_rsi", prices=prices, period=14)
    ma  = await registry.execute("calculate_moving_averages", prices=prices)
    bb  = await registry.execute("calculate_bollinger_bands", prices=prices)
    print(f"\nSample prices: {prices[:5]}...")
    print(f"  RSI: {rsi['rsi']}")
    print(f"  MA5/MA20: {ma['ma5']} / {ma['ma20']}")
    print(f"  Bollinger: {bb['middle']} [{bb['lower']}-{bb['upper']}]")

    # Format a stub report
    report = await registry.execute("format_report", report_data={
        "report_date":"2026-07-07",
        "market_summary":{"regime":"risk_on","narrative":"Tech rotation continues."},
        "candidates":[{"rank":1,"stock_code":"600519","stock_name":"Kweichow Moutai",
            "score":8.5,"confidence":0.75,"thesis":"Premium demand.","risks":["Valuation"]}],
        "learning_point":"Price is what you pay; value is what you get.",
    })
    print(f"\n=== Sample Report (first 200 chars) ===")
    print(report["markdown"][:200] + "...")

    # MCP schema export
    mcp = registry.get("calculate_rsi").to_mcp_tool_schema()
    print(f"\n=== MCP schema (calculate_rsi) ===")
    print(f"  name: {mcp['name']}")
    print(f"  inputSchema type: {mcp['inputSchema']['type']}")

    memory.close()
    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(main())
