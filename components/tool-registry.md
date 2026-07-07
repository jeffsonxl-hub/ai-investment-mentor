 # ToolRegistry

 ## Name
 ToolRegistry

 ## Purpose
 Central registry of all Tools in the system. Owns the master Tool catalog, enforces per-Agent authorization by exporting only the subset of Tools each Agent is permitted to call, and dispatches function-call requests from the Agent runtime to the correct Tool.

 ## Responsibilities

 - Maintain the master list of all registered Tools (31 in V1)
 - Validate that every Tool has a unique name (reject duplicates on registration)
 - Export the OpenAI function-calling schema list for a given set of Tool names
 - Enforce Agent authorization: an Agent can only receive Tools in its allowed list
 - Dispatch execution requests by Tool name, forwarding keyword arguments to the Tool's `execute()` method
 - Raise clear errors for unknown Tool names (prevents silent failures from typos)

 This component does NOT:
 - Make decisions about which Tools an Agent should receive — that is defined in the Agent's initialization
 - Modify Tool schemas at runtime
 - Call an LLM
 - Maintain execution history (that is the Agent runtime's responsibility)

 ## Public Interface

 ```python
 class ToolRegistry:
     def __init__(self) -> None:
         """Create an empty registry."""

     def register(self, tool: Tool) -> None:
         """Register a Tool. Raises ValueError if name already exists."""

     def get(self, name: str) -> Tool:
         """Retrieve a Tool by name. Raises KeyError if not found."""

     def get_for_agent(self, tool_names: list[str]) -> list[Tool]:
         """Return Tools authorized for an Agent. Raises KeyError for unknown names."""

     def export_for_llm(self, tool_names: list[str]) -> list[dict]:
         """Export authorized Tools as OpenAI function-calling schema list.
         This is the list injected into the LLM's context window."""

     async def execute(self, name: str, **kwargs) -> Any:
         """Execute a Tool by name with keyword arguments.
         Called by the Agent runtime when the LLM emits a function_call."""
 ```

 ### Registration Pattern

 ```python
 registry = ToolRegistry()

 # Data Tools
 registry.register(Tool(
     name="get_index_data",
     description="Fetch daily OHLCV data for a major A-share index...",
     parameters=[
         ToolParameter("symbol", "string", "Index symbol", enum=["sh000001", "sz399001", "sz399006", "sh000688"]),
         ToolParameter("start_date", "string", "Start date in YYYY-MM-DD", required=False),
         ToolParameter("end_date", "string", "End date in YYYY-MM-DD"),
     ],
     func=_get_index_data_impl,
     category="data",
 ))

# ... register all 30 remaining Tools ...

 # At Agent initialization:
 market_agent_tools = registry.export_for_llm([
     "get_index_data", "get_sector_performance", ...
 ])
 ```

 ### Execution Pattern

 ```python
 # Agent runtime receives function_call from LLM:
 function_call = {"name": "get_index_data", "arguments": {"symbol": "sh000001", "end_date": "2026-07-07"}}

 # Dispatch:
 result = await registry.execute(**function_call)
 # result = [{"date": "2026-07-07", "open": 3021.5, ...}, ...]
 ```

 ## Dependencies

 - **`Tool`** — the Tool dataclass (defined in `src/tools/tool.py`)
 - **Python standard library**: `asyncio`, `typing`
 - **No LLM dependency.** This is a Component, not an Agent

 ## Consumers

 | Consumer | How It Uses ToolRegistry |
 |---|---|
 | `src/main.py` (startup) | Creates registry, registers all 31 Tools |
 | Each Agent's `__init__` | Calls `export_for_llm(allowed_tool_names)` to receive its Tool schemas |
 | Agent Runtime (in each Agent) | Calls `execute(name, **kwargs)` when the LLM emits a function_call |
 | Tests | Creates registry with mock Tools to verify authorization and dispatch |

 ## Constraints

 - **No LLM access.** This is a Component — deterministic dispatch, no reasoning
 - **Immutable after registration.** Once `register()` is called for all Tools, the registry does not change during a pipeline run
 - **Must reject duplicate names.** `register()` raises `ValueError` on conflict — not a warning, not a silent overwrite
 - **Must reject unknown names in `get_for_agent()`.** A typo in an Agent's tool list (e.g., `"get_indexdata"`) must fail with a clear `KeyError`, not silently skip the Tool
 - **Thread safety for V1.** Single-threaded access. If multi-agent parallel execution is added later, add an `asyncio.Lock` around `execute()`

 ## Failure Handling

 | Scenario | Behavior |
 |---|---|
 | Tool name collision on register | `ValueError` at startup. Pipeline does not start |
 | Unknown tool in Agent's list | `KeyError` at Agent init. Pipeline does not start |
 | LLM requests unknown Tool | `KeyError` at execute time. Runtime returns error to LLM |
 | Tool.execute() raises | Exception propagates to Agent runtime, which returns error to LLM |
 | Tool.execute() times out | `asyncio.TimeoutError` caught by Agent runtime (not ToolRegistry) |

 ## Future Evolution

 - **V2: Dynamic tool discovery.** Allow Agents to query the registry for Tools matching a capability description, rather than receiving a static list
 - **V2: Tool usage metrics.** Track how often each Tool is called, by which Agent, with what parameters, and how long it takes. Feed into Tool deprecation and optimization decisions
 - **V2: Hot-reload.** Allow adding or updating Tools without restarting the pipeline (useful for prompt iteration during development)
