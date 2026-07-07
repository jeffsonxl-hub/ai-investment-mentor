 # Tool Design ¡ª AI Investment Mentor

 This document defines every Tool in the system: what a Tool is, how it differs from an Agent and a Component, the Tool interface contract, the full 31-tool catalog, per-Agent assignments, and the MCP compatibility mapping.

 ## 1. The Three-Way Boundary

 Phase 6 answers the question: *If Agents think and Components execute, what is a Tool?*

 | | Agent | Tool | Component |
 |---|---|---|---|
 | **Has LLM?** | Yes ¡ª its core reasoning engine | No (except LLM-Powered Tools, which call LLM deterministically) | No |
 | **Makes decisions?** | Yes ¡ª chooses which Tools to call and what to do with results | No ¡ª executes when called, returns results | No |
 | **Has memory?** | Yes ¡ª reads/writes through Memory Tools | No ¡ª stateless between calls | No |
 | **Interface** | `run(**kwargs) ¡ú AgentResult` | `execute(**kwargs) ¡ú Any` with LLM-readable schema | Python method signatures |
 | **How does caller find it?** | Pipeline creates it at startup | Registered in ToolRegistry, exported as JSON schema to LLM | `import` statement |
 | **Who calls it?** | Pipeline (Advisor calls specialist Agents) | LLM (via function-calling JSON) | Other Components, Tools, or Pipeline |

 A Tool is the **adapter** between LLM reasoning and deterministic execution. It translates "I need to check the market regime" into concrete Component calls, executes them, and returns structured results the LLM can understand.

 ## 2. Why Not Just Expose Components?

 The DataProvider already has `get_index_data()`. Why not let the LLM call it directly?

 Because an LLM does not see method signatures. It sees text. If you give an LLM a Component's entire surface area ¡ª 15+ methods with raw parameter names ¡ª it will:

 1. Call the wrong method ("I need market temperature" ¡ú calls `get_stock_news` because "news" sounds relevant)
 2. Pass hallucinated parameters (inventing a `region="china"` argument)
 3. Skip critical calls (fails to understand that macro indicators are part of regime assessment)
 4. Call methods it should not have access to (Market Agent calling `fetch_news`)

 A Tool solves all four:

 1. **Description routing**: The LLM reads "Fetch daily OHLCV for major A-share indices" and matches it to "I need market data"
 2. **Schema constraints**: `enum: ["sh000001", "sz399001", ...]` ¡ª the LLM cannot hallucinate a symbol
 3. **Composition**: `assess_market_regime` calls 4 Components internally. The LLM calls one Tool, gets everything
 4. **Authorization**: Each Agent's tool list is explicit. Market Agent does not receive `fetch_news`

 ## 3. The Tool Interface

 ```python
 from dataclasses import dataclass, field
 from typing import Callable, Awaitable, Any


 @dataclass
 class ToolParameter:
     name: str
     type: str               # "string" | "number" | "integer" | "boolean" | "array" | "object"
     description: str        # Natural language. The LLM reads this to decide what value to pass.
     required: bool = True
     enum: list[str] | None = None    # Constrain to specific values ¡ª prevents hallucination
     default: Any = None              # Used when required=False


 @dataclass
 class Tool:
     """A callable capability exposed to an Agent's LLM via function calling.

     A Tool wraps one or more Component calls behind a natural-language
     interface that an LLM can decide to invoke. Tools are stateless ¡ª
     they do not remember anything between calls.
     """
     name: str
     description: str         # The LLM reads this to decide WHEN to call this tool
     parameters: list[ToolParameter]
     func: Callable[..., Awaitable[Any]]
     category: str = ""       # "data" | "analysis" | "memory" | "llm_powered" | "synthesis"
    dependencies: dict[str, Any] = field(default_factory=dict)
        # Injected at registration time. LLM-Powered Tools receive {"llm_client": ...}.
        # Unpacked into func kwargs at execution so func receives deps + user params.

     def to_openai_schema(self) -> dict:
         """Export to the exact format OpenAI function calling expects.

         This is the format injected into the LLM's system prompt. The LLM
         reads name + description to decide what to call, and uses the
         parameters JSON Schema to generate correctly-typed arguments.
         """
         properties = {}
         required_list = []
         for p in self.parameters:
             prop = {"type": p.type, "description": p.description}
             if p.enum:
                 prop["enum"] = p.enum
             if p.default is not None:
                 prop["default"] = p.default
             properties[p.name] = prop
             if p.required:
                 required_list.append(p.name)

         return {
             "type": "function",
             "function": {
                 "name": self.name,
                 "description": self.description,
                 "parameters": {
                     "type": "object",
                     "properties": properties,
                     "required": required_list,
                 },
             },
         }

     def to_mcp_tool_schema(self) -> dict:
         """MCP tool schema ¡ª identical structure, different top-level key name."""
         openai_schema = self.to_openai_schema()
         return {
             "name": self.name,
             "description": self.description,
             "inputSchema": openai_schema["function"]["parameters"],
         }

     async def execute(self, **kwargs) -> Any:
         """Execute the tool with validated keyword arguments.

         A single Tool can orchestrate multiple Component calls internally.
         The LLM never knows how many calls happened ¡ª it just sees the result.
         Dependencies (injected at registration) are unpacked into kwargs before
         the func receives them ¡ª the LLM never sees them in the schema.
         """
         self._validate_params(**kwargs)
         merged = {**self.dependencies, **kwargs}
         return await self.func(**merged)
 ```

 ### 3.1 The ToolRegistry

 The ToolRegistry is a Component (no LLM, deterministic). It owns the master list of all Tools and enforces per-Agent authorization:

 ```python
 class ToolRegistry:
     """Central registry of all tools. Agents request their authorized subset."""

     def __init__(self):
         self._tools: dict[str, Tool] = {}

     def register(self, tool: Tool) -> None:
         if tool.name in self._tools:
             raise ValueError(f"Tool '{tool.name}' already registered")
         self._tools[tool.name] = tool

     def get(self, name: str) -> Tool:
         return self._tools[name]

     def get_for_agent(self, tool_names: list[str]) -> list[Tool]:
         """Return the Tools authorized for a specific Agent.

         Raises KeyError if any requested tool is not registered.
         This prevents silent failures from typos in agent tool lists.
         """
         missing = set(tool_names) - set(self._tools)
         if missing:
             raise KeyError(f"Unknown tools: {missing}")
         return [self._tools[name] for name in tool_names]

     def export_for_llm(self, tool_names: list[str]) -> list[dict]:
         """Export authorized tools as LLM function-calling schema list."""
         return [t.to_openai_schema() for t in self.get_for_agent(tool_names)]

     async def execute(self, name: str, **kwargs) -> Any:
         """Execute a tool by name. Called by the Agent runtime when the LLM
         emits a function_call JSON block."""
         tool = self.get(name)
         return await tool.execute(**kwargs)
 ```

 ## 4. The Complete Tool Catalog (31 Tools)

 ### 4.1 Data Tools (wrap DataProvider)

 | # | Tool Name | Parameters | Returns | Used By |
 |---|---|---|---|---|
 | 1 | `get_index_data` | `symbol` (enum: sh000001, sz399001, sz399006, sh000688), `start_date`, `end_date` | List of OHLCV dicts | Market |
 | 2 | `get_sector_performance` | _(none)_ | List of sector performance dicts | Market |
 | 3 | `get_northbound_flow` | `days` (default 5) | Net flow dict with daily breakdown | Market |
 | 4 | `get_macro_indicators` | _(none)_ | SHIBOR, PMI, CPI dict | Market |
 | 5 | `get_fundamentals` | `stock_codes` (list of strings) | List of PE, PB, ROE, market cap dicts | Watchlist, Advisor |
 | 6 | `get_stock_basic_info` | _(none)_ | List of all A-share stocks with name, industry, list_date | Market, Research, Watchlist |
 | 7 | `get_stock_price_history` | `stock_code`, `start_date`, `end_date` | List of OHLCV dicts | Research, Watchlist |
 | 8 | `fetch_news` | `stock_code`, `limit` (default 20) | List of news article dicts | Research |
 | 9 | `fetch_announcements` | `stock_code`, `limit` (default 20) | List of announcement dicts | Research |

 ### 4.2 Analysis Tools (pure math ¡ª no LLM, no external calls)

 | # | Tool Name | Parameters | Returns | Used By |
 |---|---|---|---|---|
 | 10 | `calculate_rsi` | `prices` (list of closes), `period` (default 14) | RSI value (0¨C100) | Market, Watchlist |
 | 11 | `calculate_macd` | `prices` (list of closes), `fast` (12), `slow` (26), `signal` (9) | MACD line, signal line, histogram | Market, Watchlist |
 | 12 | `calculate_moving_averages` | `prices`, `periods` (list, default [5,10,20,60]) | Dict of MA values per period | Market, Watchlist |
 | 13 | `calculate_bollinger_bands` | `prices`, `period` (20), `std_dev` (2) | Upper, middle, lower bands | Market, Watchlist |
 | 14 | `calculate_volume_profile` | `prices`, `volumes`, `bins` (10) | Volume distribution dict | Market, Watchlist |
 | 15 | `calculate_returns` | `prices`, `period` (default 1) | List of period returns | Watchlist |

### 4.3 Memory Tools (wrap MemoryRepository)

 | # | Tool Name | Parameters | Returns | Used By |
 |---|---|---|---|---|
 | 16 | `get_watchlist` | _(none)_ | List of active watchlist entries | Watchlist |
 | 17 | `get_watchlist_entry` | `stock_code` | Single watchlist entry or null | Watchlist |
 | 18 | `get_recent_decisions` | `days` (default 5) | List of recent decision dicts | Research, Advisor |
 | 19 | `get_rejected_stocks` | `days` (default 20) | List of rejected stock codes | Advisor |
 | 20 | `get_market_history` | `days` (default 20) | List of recent market snapshots | Market |
| 21 | `save_market_snapshot` | `snapshot` (dict) | None | Market |
| 22 | `save_decision` | `decision` (dict) | None | Advisor |
| 23 | `update_watchlist_entry` | `stock_code`, `field`, `value` | None | Watchlist |

Memory write Tools (#21\u201323) are plain pass-throughs to MemoryRepository methods.
They keep all Agent\u2192Memory traffic flowing through the Tool boundary \u2014 Agents
never touch Components directly, reads or writes.


 ### 4.4 LLM-Powered Tools (deterministic wrappers with internal LLM calls)

 These Tools use an LLM internally but are not Agents. They do not maintain state, do not decide *when* to run, and do not have memory. They receive text and return structured classification ¡ª the Agent decides whether to call them and what to do with the output.

 | # | Tool Name | Parameters | Returns | Used By |
 |---|---|---|---|---|
 | 24 | `summarize_article` | `url`, `text` | Structured summary (title, key_points, entities) | Research |
 | 25 | `classify_sentiment` | `text` | "positive" | "negative" | "neutral" with confidence | Research |
 | 26 | `extract_keywords` | `text`, `max_keywords` (10) | List of keyword strings | Research |
 | 27 | `classify_event_type` | `text` | Event type enum: earnings_guidance, policy_impact, product_news, management_change, industry_trend, other | Research |

 ### 4.5 Synthesis Tools (multi-Component orchestration)

 | # | Tool Name | Parameters | Returns | Used By |
 |---|---|---|---|---|
 | 28 | `assess_market_regime` | `date` | Full market snapshot: indices, sectors, flow, macro | Market |
 | 29 | `build_candidate_list` | `market_context`, `theme_list`, `stock_universe` | Filtered list of candidate stocks | Advisor |
 | 30 | `score_candidates` | `candidates`, `market_context`, `watchlist_status` | Ranked list with score breakdowns | Advisor |
 | 31 | `generate_narrative` | `scored_candidates`, `market_context` | Narrative text for morning report | Advisor |
 | 32 | `format_report` | `report_data` | Formatted Markdown report | Advisor |
 | 33 | `request_market_context` | `date` | Triggers Market Agent, returns MarketContext | Advisor |
 | 34 | `request_events` | `stock_codes` (or "market_wide") | Triggers Research Agent, returns Events | Advisor |

 ## 5. Per-Agent Tool Assignments

 Each Agent is initialized with a specific list of Tool names. The ToolRegistry exports only those schemas to the LLM's context window:

 **Market Agent** (11 tools):
 ```
 get_index_data, get_sector_performance, get_northbound_flow,
 get_macro_indicators, get_stock_basic_info,
 calculate_rsi, calculate_macd, calculate_moving_averages,
 calculate_bollinger_bands, calculate_volume_profile,
    get_market_history, save_market_snapshot, assess_market_regime
 ```

 **Research Agent** (10 tools):
 ```
 get_stock_basic_info, get_stock_price_history,
 fetch_news, fetch_announcements,
 summarize_article, classify_sentiment,
 extract_keywords, classify_event_type,
 get_recent_decisions
 ```

 **Watchlist Agent** (13 tools):
 ```
 get_watchlist, get_watchlist_entry,
 get_stock_basic_info, get_stock_price_history,
 get_fundamentals,
 calculate_rsi, calculate_macd, calculate_moving_averages,
 calculate_bollinger_bands, calculate_volume_profile,
    calculate_returns, update_watchlist_entry
 ```

 **Advisor Agent** (12 tools):
 ```
 build_candidate_list, score_candidates,
 generate_narrative, format_report,
 request_market_context, request_events,
 get_fundamentals, get_recent_decisions,
    get_rejected_stocks, save_decision
 ```

 ## 6. MCP Compatibility

 MCP (Model Context Protocol) is an open standard from Anthropic that defines how LLM applications discover and call external tools. It has two components:

 1. **Tool schema** ¡ª what the LLM sees: name, description, `inputSchema` (JSON Schema). **Identical to our `to_openai_schema()` output.**
 2. **Transport** ¡ª how the LLM communicates with the tool host: stdio, HTTP with SSE, or WebSocket. This is the layer we do not implement in V1.

 The mapping is a structural rename, not a schema change:

 ```
 OpenAI function calling:        MCP:
 {                               {
   "type": "function",             "name": "get_index_data",
   "function": {                   "description": "Fetch daily...",
     "name": "get_index_data",     "inputSchema": {
     "description": "Fetch...",      "type": "object",
     "parameters": {                 "properties": { ... },
       "type": "object",             "required": [ ... ]
       "properties": { ... },      }
       "required": [ ... ]       }
     }
   }
 }
 ```

 Every Tool already defines both. When we adopt MCP in Phase 13+:
 - Each Tool's `to_mcp_tool_schema()` becomes its `tools/list` response
 - `ToolRegistry.execute(name, **kwargs)` becomes the `tools/call` handler
 - The transport layer (MCP server process) is new, but the Tool code does not change

 ## 7. Execution Flow

 Here is what happens when an Agent reasons its way to a Tool call:

 ```mermaid
 sequenceDiagram
     participant Agent as Agent (LLM)
     participant Runtime as Agent Runtime
     participant Registry as ToolRegistry
     participant Tool as Tool
     participant Comp as Component(s)

     Note over Agent: Reasoning: "I need index data to assess regime"
     Agent->>Runtime: { "tool_calls": [{ "function": { "name": "get_index_data", "arguments": { "symbol": "sh000001" } } }] }

     Runtime->>Registry: execute("get_index_data", symbol="sh000001")
     Registry->>Tool: execute(symbol="sh000001")

     opt Multi-call orchestration
         Tool->>Comp: DataProvider.get_index_data()
         Comp-->>Tool: OHLCV data
     end

     Tool-->>Registry: result dict
     Registry-->>Runtime: result dict

     Runtime->>Agent: Append result to context window
     Note over Agent: Reasoning: "Index is above 20-day MA. Now I need sector data..."
 ```

 The key insight: from the LLM's perspective, there is one call and one result. Whether the Tool orchestrated 1 or 4 Component calls internally is invisible.

 ## 8. Tool Design Heuristics

 These are the rules of thumb we apply when deciding whether something is a Tool, an Agent, or a Component:

 | If... | Then it is a... | Example |
 |---|---|---|
 | It needs reasoning about *when* to do something | Agent | "Should I check sector performance, or is yesterday's context enough?" |
 | It needs an LLM to decide *what value* to pass | Agent (decides) + Tool (receives) | The LLM picks `symbol="sh000001"` ¡ª the Tool receives it |
 | It is pure math or data retrieval | Tool | `calculate_rsi`, `get_index_data` |
 | It is persistent storage | Component | `MemoryRepository` |
 | It transforms structured data | Tool | `score_candidates` |
 | It generates unstructured text from data | Tool (LLM-Powered) | `generate_narrative` |
 | It maintains state across calls | Not a Tool. Agent or Component | Watchlist (Agent manages, Component stores) |

 ## 9. Error Handling

 | Scenario | Tool Behavior | LLM Sees |
 |---|---|---|
 | Component call succeeds | Return structured result | Result in context window |
 | Component call times out | Return `{"error": "timeout", "detail": "..."}` with partial data if available | Error dict ¡ª LLM decides: retry, skip, or degrade |
 | Invalid parameter (e.g., wrong enum) | Raise `ValueError` before execution | Runtime catches and returns error to LLM |
 | LLM calls non-existent Tool | `ToolRegistry.get()` raises `KeyError` | Runtime returns error to LLM |
 | LLM-Powered Tool''s internal LLM call fails | Retry once. If still fails, return `{"error": "llm_unavailable"}` | LLM decides: skip classification or use fallback |
| LLM passes wrong parameter type | `_validate_params()` raises `TypeError` before `func` is called | Runtime catches TypeError, returns error to LLM |

Note: `_validate_params()` closes the critical gap where LLM-generated type
mismatches (e.g., `123` for `"sh000001"`) would silently reach Components and
produce opaque network errors. Validation is cheap (O(n) over params) and
enabled by default; it can be skipped by setting `skip_validation=True` on
the Tool for trusted callers (internal Synthesis Tools).

 ## 10. V2 Evolution

 - **Tool composition**: Allow Tools to call other Tools (today Tools only call Components). This enables recursive orchestration.
 - **Tool discovery**: Instead of static per-Agent lists, let Agents dynamically request Tools from the registry based on their current task.
 - **Tool performance tracking**: Log every Tool call's duration, success rate, and parameter patterns to identify underused or misused Tools.
 - **Per-call Tool filtering**: The Agent runtime selects a subset of Tools based on current task description, reducing context window overhead. A simple "regime classification" call does not need `calculate_bollinger_bands` in the schema.
- **MCP transport**: Add stdio and HTTP transport layers so Tools can be called by external MCP clients.
