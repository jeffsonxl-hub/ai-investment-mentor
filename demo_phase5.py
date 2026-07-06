# Demo script for Phase 5 data layer (AkShare-native).
# Run: pip install -r requirements.txt && python demo_phase5.py
# No TuShare token needed - uses AkShare for all data.

import asyncio, logging, sys
sys.path.insert(0, "src")

from data import AkShareClient, DataProvider
from logging_config import setup_logging
from memory.repository import MemoryRepository

TRADE_DATE = "2026-07-03"


async def main():
    setup_logging()
    log = logging.getLogger("demo")

    print("Trade date: " + TRADE_DATE)
    print("=" * 60)

    # Wire up Components (no TuShare needed)
    ak_client = AkShareClient()
    memory = MemoryRepository("data/ai_mentor.db")
    provider = DataProvider(ak_client, memory)

    # 1. Fetch a market snapshot
    print("\n[1/4] Fetching market snapshot...")
    snap = await provider.get_market_snapshot(TRADE_DATE)
    dq = snap["data_quality"]
    print("  Data quality: " + dq)
    if dq != "full":
        print("  (check logs/ai_mentor.log for details)")

    # 2. Fetch stock basic info
    print("\n[2/4] Fetching stock basic info...")
    stocks = await provider.get_stock_basic_info()
    print("  Retrieved " + str(len(stocks)) + " stocks")
    if stocks:
        for s in stocks[:3]:
            print("    " + s.get("code", "?") + "  " + s.get("name", "?"))

    # 3. Fetch fundamental snapshot (uses spot data)
    if stocks:
        sample_codes = [s["code"] for s in stocks[:2]]
        print("\n[3/4] Fetching fundamental snapshot for " + str(sample_codes) + "...")
        fundamentals = await provider.get_fundamental_snapshot(sample_codes, TRADE_DATE)
        if fundamentals:
            for f in fundamentals:
                pe = str(f.get("pe", "?"))
                pb = str(f.get("pb", "?"))
                mv = str(f.get("total_mv", "?"))
                print("    " + f.get("ts_code", "?") + "  PE=" + pe + "  PB=" + pb + "  MV=" + mv)
        else:
            print("  No fundamental data (check logs/ai_mentor.log)")

    # 4. Fetch news for one stock
    if stocks:
        code = stocks[0]["code"]
        print("\n[4/4] Fetching news for " + code + "...")
        news = await provider.get_stock_news(code, limit=3)
        print("  Retrieved " + str(len(news)) + " articles")
        for n in news:
            print("    " + n.get("title", "?")[:60])

    # 5. Source status
    print("\nSource Status")
    print("-" * 40)
    statuses = await provider.get_source_status(TRADE_DATE)
    for s in statuses:
        icon = "OK" if s["status"] == "success" else "!!"
        msg = "  [" + icon + "] " + s["source"] + ": " + s["status"]
        if s.get("error_message"):
            msg += " (" + s["error_message"][:80] + ")"
        print(msg)

    memory.close()
    print("\nFull details: logs/ai_mentor.log")


if __name__ == "__main__":
    asyncio.run(main())
