 # TASK-006: Tool Layer Implementation

 ## Context

 Phase 6 (Tool Design) defines the Tool abstraction: the interface between LLM reasoning and deterministic Component execution. ADR-006 establishes that Tools are LLM-readable function descriptors using the OpenAI function-calling JSON Schema, compatible with MCP. The full design is in `docs/architecture/08-tool-design.md`, with component specs in `components/tool.md` and `components/tool-registry.md`.

 This TASK implements the Tool class, the ToolRegistry, and all 31 Tools. No Agents are built yet — that is Phase 8+.

 ## Objective

 Implement the complete Tool Layer: the `Tool` and `ToolRegistry` classes plus all 31 Tool implementations, covering the 5 categories defined in the catalog.

 ## Requirements

 ### Core Infrastructure
 - [ ] `src/tools/__init__.py` — package init
 - [ ] `src/tools/tool.py` — `ToolParameter` and `Tool` dataclasses with `to_openai_schema()`, `to_mcp_tool_schema()`, `execute()`
 - [ ] `src/tools/registry.py` — `ToolRegistry` with `register()`, `get()`, `get_for_agent()`, `export_for_llm()`, `execute()`
 - [ ] `src/tools/factory.py` — `create_tool_registry()` factory function that registers all 31 Tools with their real implementations, accepts injected DataProvider and MemoryRepository

 ### Data Tools (9) — `src/tools/data_tools.py`
 - [ ] `get_index_data` — wraps `DataProvider.get_index_data()`
 - [ ] `get_sector_performance` — wraps `DataProvider.get_sector_performance()`
 - [ ] `get_northbound_flow` — wraps `DataProvider.get_northbound_flow()`
 - [ ] `get_macro_indicators` — wraps `DataProvider.get_macro_indicators()`
 - [ ] `get_fundamentals` — wraps `DataProvider.get_fundamental_snapshot()`
 - [ ] `get_stock_basic_info` — wraps `DataProvider.get_stock_basic_info()`
 - [ ] `get_stock_price_history` — wraps `DataProvider.get_index_data()` with stock symbol mapping
 - [ ] `fetch_news` — wraps `DataProvider.get_stock_news()`
 - [ ] `fetch_announcements` — wraps `DataProvider.get_announcements()`

 ### Analysis Tools (6) — `src/tools/analysis_tools.py`
 - [ ] `calculate_rsi` — pure Python, no deps. Input: list of closes. Uses Wilder's smoothing
 - [ ] `calculate_macd` — pure Python, no deps. Input: list of closes. Returns MACD line, signal, histogram
 - [ ] `calculate_moving_averages` — pure Python, no deps. Input: list of closes, list of periods
 - [ ] `calculate_bollinger_bands` — pure Python, no deps. Input: list of closes. Returns upper, middle, lower
 - [ ] `calculate_volume_profile` — pure Python, no deps. Input: prices + volumes. Bins volume by price level
 - [ ] `calculate_returns` — pure Python, no deps. Input: list of closes, period. Returns period-over-period returns

### Memory Tools (8) — `src/tools/memory_tools.py`
 - [ ] `get_watchlist` — wraps `MemoryRepository.get_watchlist()`
 - [ ] `get_watchlist_entry` — wraps `MemoryRepository.get_watchlist_entry()`
 - [ ] `get_recent_decisions` — wraps `MemoryRepository.get_recent_decisions()`
 - [ ] `get_rejected_stocks` — wraps `MemoryRepository.get_rejected_stocks()`
 - [ ] `get_market_history` — wraps `MemoryRepository.get_market_snapshot_range()`
- [ ] `save_market_snapshot` — wraps `MemoryRepository.save_market_snapshot()` (write)
- [ ] `save_decision` — wraps `MemoryRepository.save_decision()` (write)
- [ ] `update_watchlist_entry` — wraps `MemoryRepository.update_watchlist_priority()` (write)

Write tools exist to keep the rule consistent: Agents never touch Components directly.
The Agent has one dependency: the ToolRegistry.


 ### LLM-Powered Tools (4) — `src/tools/llm_tools.py`
 - [ ] `summarize_article` — calls LLM with summarization prompt. Returns structured {title, key_points, entities}
 - [ ] `classify_sentiment` — calls LLM with sentiment prompt. Returns {sentiment, confidence}
 - [ ] `extract_keywords` — calls LLM with keyword extraction prompt. Returns list of strings
 - [ ] `classify_event_type` — calls LLM with classification prompt. Returns event type enum

 ### Synthesis Tools (7) — `src/tools/synthesis_tools.py`
 - [ ] `assess_market_regime` — orchestrates get_index_data + get_sector_performance + get_northbound_flow + get_macro_indicators
 - [ ] `build_candidate_list` — deterministic filtering (market cap, volume, ST/*ST, trading status)
 - [ ] `score_candidates` — deterministic multi-factor scoring with regime-adjusted weights
 - [ ] `generate_narrative` — calls LLM with scored candidates + context to produce narrative text
 - [ ] `format_report` — deterministic Markdown formatting from structured report data
 - [ ] `request_market_context` — stub that will trigger Market Agent (Phase 8). V1: returns mock
 - [ ] `request_events` — stub that will trigger Research Agent (Phase 9). V1: returns mock

 ### Tests
 - [ ] `tests/test_tool.py` — test ToolParameter, Tool schema export (OpenAI + MCP format), execute
 - [ ] `tests/test_tool_registry.py` — test register, duplicate rejection, get_for_agent authorization, export_for_llm, execute dispatch, unknown tool error
 - [ ] `tests/test_data_tools.py` — test each Data Tool with mocked DataProvider
 - [ ] `tests/test_analysis_tools.py` — test each Analysis Tool with known price arrays + expected values
 - [ ] `tests/test_memory_tools.py` — test each Memory Tool with mocked MemoryRepository (or in-memory SQLite)
 - [ ] `tests/test_llm_tools.py` — test each LLM-Powered Tool with mocked LLM client
 - [ ] `tests/test_synthesis_tools.py` — test assess_market_regime orchestration, score_candidates with known inputs, build_candidate_list filters

 ### Integration
 - [ ] `src/main.py` — update to use `create_tool_registry()` and wire Tools into the mock Agents
- [ ] `demo_phase6.py` — registers all 34 Tools, exports schemas for all 4 Agents, runs `assess_market_regime` end-to-end, validates result shapes against schemas

 ## Acceptance Criteria

 1. `Tool.to_openai_schema()` output matches the exact format the OpenAI API expects for its `tools` parameter
 2. `Tool.to_mcp_tool_schema()` output matches the MCP `Tool` definition: `{name, description, inputSchema}`
 3. `ToolRegistry.export_for_llm(["get_index_data"])` returns a list with one dict in OpenAI format
 4. `ToolRegistry.get_for_agent(["nonexistent"])` raises `KeyError`
 5. `ToolRegistry.register(tool_with_duplicate_name)` raises `ValueError`
 6. All 6 Analysis Tools produce correct numeric output for known input arrays (test against manual calculations)
 7. `assess_market_regime.execute(date="2026-07-07")` orchestrates 4 DataProvider calls and returns a combined dict
 8. `demo_phase6.py` runs end-to-end with zero errors
9. All unit tests pass (`pytest tests/ -q` — tests for the new tool modules, 7 test files)
10. `Tool._validate_params(symbol=123)` raises `TypeError`; `Tool._validate_params(symbol="sh000001")` passes
11. LLM-Powered Tools receive `llm_client` via `dependencies`, never through the LLM-facing schema
 10. Environment: `pip install -r requirements.txt` succeeds; no new external dependencies beyond standard library
13. Total tool count: 34 (9 Data + 6 Analysis + 8 Memory + 4 LLM-Powered + 7 Synthesis)

 ## Out of Scope

 - Building actual Agents (Market, Research, Watchlist, Advisor) — that is Phase 8–11
- Agent Runtime (the loop that parses LLM `tool_calls` JSON and dispatches to `ToolRegistry.execute()`, feeds results back to context window) — designed in Phase 8. Phase 6 defines the execution flow but defers the Runtime implementation
 - Agent runtime (the loop that sends Tool schemas to the LLM and dispatches function_calls) — that is part of the Agent base class in Phase 8
 - MCP transport layer (stdio/HTTP server) — Phase 13+
 - LangGraph integration — Phase 12+
 - Tool execution history or metrics — V2
 - Dynamic tool discovery — V2

 ## References

 - [ADR-006: Tool-as-Adapter Boundary](../adr/ADR-006-tool-design.md)
 - [Architecture: Tool Design](../docs/architecture/08-tool-design.md)
 - [Component Spec: Tool](../components/tool.md)
 - [Component Spec: ToolRegistry](../components/tool-registry.md)
 - [ADR-002: Agent Responsibilities & Data Access Boundaries](../adr/ADR-002-agent-responsibilities.md)
 - [Architecture: System Overview](../docs/architecture/02-system-overview.md)
 - [Architecture: Agent Design](../docs/architecture/03-agent-design.md)
 - [Architecture: Decision Flow](../docs/architecture/04-decision-flow.md)
