"""AI Investment Mentor - Entry Point.

Usage:
    python src/main.py                    # Print project info
    python src/main.py --run-morning-report  # Run daily analysis pipeline
"""

import argparse
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    parser = argparse.ArgumentParser(description="AI Investment Mentor")
    parser.add_argument(
        "--run-morning-report",
        action="store_true",
        help="Run the daily morning analysis pipeline",
    )
    args = parser.parse_args()

    # Load config (always)
    from config import load_config

    try:
        cfg = load_config()
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    print(f"AI Investment Mentor v0.1.0")
    print(f"Config loaded: model={cfg.llm_model}, db={cfg.db_path}")

    if args.run_morning_report:
        import asyncio
        from pipeline.pipeline import Pipeline, StepSeverity
        from pipeline.steps import build_candidates, score_candidates
        from memory.repository import MemoryRepository

        memory = MemoryRepository(cfg.db_path)

        # Mock Agent stubs until real Agents are built (Phase 8+)
        async def market_agent():
            return {"regime": "neutral", "confidence": 0.5, "source": "stub"}

        async def research_agent_market():
            return {"events": [], "market_wide_summary": {"source": "stub"}}

        async def watchlist_agent():
            return {"watchlist": [], "daily_summary": "stub"}

        async def research_agent_stocks(candidates=None):
            return {"events": [], "source": "stub"}

        async def advisor_agent(scored=None):
            return {
                "report_date": "2026-07-06",
                "market_summary": {"narrative": "Stub report"},
                "candidates": [],
                "source": "stub",
            }

        pipeline = Pipeline()
        pipeline.add_step("market", market_agent, severity=StepSeverity.CRITICAL)
        pipeline.add_step("research_market", research_agent_market, severity=StepSeverity.WARNING)
        pipeline.add_step("watchlist", watchlist_agent, severity=StepSeverity.WARNING)
        pipeline.add_step("build_candidates", build_candidates,
                          depends_on=["market", "research_market", "watchlist"],
                          severity=StepSeverity.CRITICAL)
        pipeline.add_step("research_stocks", research_agent_stocks,
                          depends_on=["build_candidates"],
                          severity=StepSeverity.WARNING)
        pipeline.add_step("score", score_candidates,
                          depends_on=["build_candidates", "market", "watchlist"],
                          severity=StepSeverity.CRITICAL)
        pipeline.add_step("advisor", advisor_agent,
                          depends_on=["score"],
                          severity=StepSeverity.CRITICAL)

        result = asyncio.run(pipeline.run())
        print(f"Pipeline: {result.status} in {result.total_duration_ms}ms")
        if result.degraded_steps:
            print(f"Degraded: {result.degraded_steps}")
        memory.close()
        print("")
    else:
        print("Ready. Use --run-morning-report to start daily analysis.")


if __name__ == "__main__":
    main()


