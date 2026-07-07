 # ADR-006: Tool-as-Adapter Boundary

 ## Status
 Accepted

 ## Context

 After Phases 3–5, the system has three well-defined layers: Agent (LLM-powered reasoning), Component (deterministic infrastructure), and Data (external sources). But there is a gap: how does an Agent actually *call* a Component?

 An Agent runs inside an LLM context window. It does not import Python modules or call methods on objects. It outputs text — specifically, structured JSON — that says "I want to call function X with arguments Y." The runtime intercepts that JSON, executes the real function, and feeds the result back into the LLM's context.

 This mechanism — function calling — is the universal interface between LLM reasoning and deterministic code. OpenAI, Anthropic, and Google all implement it, and MCP (Model Context Protocol) standardizes it at the transport layer. The function-calling JSON schema (name, description, JSON Schema parameters) is the invariant that survives across providers and frameworks.

 Our Component Layer has none of this. `DataProvider.get_index_data(symbol, start_date, end_date)` is a Python signature, not an LLM-readable function descriptor. An LLM cannot call it.

 The question: should we define a Tool as just "a Component method exposed to the LLM," or is a Tool a distinct abstraction with its own interface contract?

 ## Decision

 **A Tool is a distinct abstraction that wraps one or more Component calls behind a natural-language interface an LLM can consume.**

 Three design rules:

 1. **Every Tool has a name and a description.** The LLM reads the description to decide *when* to call the Tool. The description is not documentation for humans — it is the *only* signal the LLM has to route its reasoning. If the description is vague, the LLM will call the wrong Tool or fail to call the right one.

 2. **Every Tool parameter has a JSON Schema type and a description.** The LLM reads the parameter descriptions to decide *what values* to pass. The type constrains what it can output. An `enum` narrows the choice space and reduces hallucination risk.

 3. **A Tool can orchestrate multiple Component calls internally.** The LLM does not need to know that "assess market regime" requires four DataProvider calls. It calls one Tool, receives one result, and continues reasoning. Fewer Tool calls mean fewer LLM round-trips, lower latency, and lower cost. The internal orchestration logic (parallelism, error handling, fallbacks) lives in the Tool, not in the LLM prompt.

 The Tool interface is deliberately compatible with both OpenAI function calling and MCP. The underlying JSON schema is identical — MCP adds transport (stdio/HTTP/WebSocket) and discovery ("list your tools"), but the data shape does not change.

 **Full catalog: 34 Tools across 5 categories.**

 | Category | Count | Examples | Wraps |
 |---|---|---|---|
 | Data | 9 | `get_index_data`, `fetch_news` | DataProvider |
 | Analysis | 6 | `calculate_rsi`, `calculate_macd` | Pure Python (math) |
 | Memory | 8 | `get_watchlist`, `save_market_snapshot`, `save_decision` | MemoryRepository |
 | LLM-Powered | 4 | `summarize_article`, `classify_sentiment` | Internal LLM call |
 | Synthesis | 7 | `score_candidates`, `assess_market_regime` | Multiple Components + Agents |

 ## Consequences

 **What becomes easier:**
 - **Tool authorization.** Each Agent receives only the Tools it needs. The Market Agent physically cannot call `fetch_news` because it is not in its tool list. This enforces ADR-002's boundary at the infrastructure level, not just in documentation.
 - **Testing.** Each Tool is an isolated async function. Mock its internal Component calls, test the orchestration logic, verify the output schema.
 - **MCP migration.** When we adopt MCP in Phase 13+, each Tool registers as an MCP endpoint with zero schema changes. The `to_mcp_tool_schema()` output is exactly what MCP expects.
 - **LLM provider independence.** The `to_openai_schema()` format works with DeepSeek, GPT, Claude (via Anthropic tool use), and any OpenAI-compatible endpoint. No provider lock-in.
 - **Composability.** Analysis Tools like `calculate_rsi` can be called by multiple Agents (Market uses it for breadth analysis, Watchlist uses it for alert generation). One implementation, multiple consumers.

 **What becomes harder:**
 - **Description quality matters more than code quality.** A poorly written Tool description causes the LLM to call the wrong Tool or skip a needed call. Unlike a Python docstring, a Tool description is a runtime interface — it directly impacts system behavior.
 - **Orchestration Tool design requires judgment.** When does a Tool orchestrate multiple Component calls vs. letting the Agent make multiple individual calls? The trade-off is LLM round-trips vs. Tool flexibility. Our guideline: group Component calls that always happen together (like macro indicators + index data for regime assessment). Keep separate any calls the Agent might reasonably skip.
 - **Schema drift.** If `DataProvider.get_index_data()` adds a parameter, the corresponding Tool's `ToolParameter` list must be updated in two places (Tool definition + DataProvider). We mitigate this by keeping Tools and Components in close proximity in the codebase.

 ## Alternatives Considered

 ### Alternative A: No Tool layer — Agents call Components directly
 Agents import `DataProvider` and `MemoryRepository` and call their methods. Rejected because: (a) LLMs cannot call Python methods — they output text, (b) even with an adapter, exposing Component methods directly gives the LLM too much surface area and no guidance on *when* to call what, (c) it breaks the authorization boundary — nothing prevents Market Agent from calling `fetch_news`.

 ### Alternative B: One Tool per Component method (1:1 mapping)
 Every `DataProvider` method gets a matching Tool. Simple, systematic, zero design work. Rejected because it forces the LLM to orchestrate multi-call workflows that are always done together. The LLM would need ~8 sequential Tool calls for a market regime assessment instead of one `assess_market_regime` call. More latency, more cost, more failure points.

 ### Alternative C: Use LangChain Tools from the start
 LangChain has a `@tool` decorator and built-in tool management. Rejected because: (a) it adds a dependency we don't need for a 31-tool system, (b) it obscures the MCP mapping — our explicit `Tool` class makes the schema conversion visible and teachable, (c) LangGraph (Phase 12) has its own tool system that would conflict.
