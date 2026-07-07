 # Tool

 ## Name
 Tool

 ## Purpose
 Defines the interface contract for a callable capability exposed to an Agent's LLM via function calling. A Tool wraps one or more Component calls behind a natural-language interface that an LLM can decide to invoke based on its description and parameter schemas.

 ## Responsibilities

 - Hold a name and natural-language description the LLM reads to decide *when* to call this Tool
 - Define parameter schemas (name, type, description, required, enum) the LLM reads to decide *what values* to pass
 - Export to OpenAI function-calling format (`to_openai_schema()`) — the JSON injected into the LLM's context window
 - Export to MCP tool schema format (`to_mcp_tool_schema()`) — structurally identical, different top-level key names
 - Execute the wrapped function asynchronously with validated keyword arguments
 - Orchestrate multiple Component calls internally when the Tool is a synthesis Tool

 This component does NOT:
 - Make decisions about *when* to call itself — the LLM decides
 - Maintain state between calls — Tools are stateless
 - Call an LLM for reasoning (except LLM-Powered Tools, which call LLM deterministically for NLP tasks)
 - Validate parameters against the schema at execution time (validation happens at the schema declaration level — the LLM is constrained by the JSON Schema)

 ## Public Interface

 ```python
 from dataclasses import dataclass, field
 from typing import Callable, Awaitable, Any

 @dataclass
 class ToolParameter:
     name: str
     type: str               # "string" | "number" | "integer" | "boolean" | "array" | "object"
     description: str        # Natural language. The LLM reads this to decide what value to pass.
     required: bool = True
     enum: list[str] | None = None
     default: Any = None

 @dataclass
 class Tool:
     name: str
     description: str         # The LLM reads this to decide WHEN to call this tool
     parameters: list[ToolParameter]
     func: Callable[..., Awaitable[Any]]
     category: str = ""       # "data" | "analysis" | "memory" | "llm_powered" | "synthesis"
    dependencies: dict[str, Any] = field(default_factory=dict)  # Injected at registration (e.g., llm_client)


    def _validate_params(self, **kwargs) -> None: ...  # Raises TypeError on type mismatch
     def to_openai_schema(self) -> dict: ...
     def to_mcp_tool_schema(self) -> dict: ...
    async def execute(self, **kwargs) -> Any: ...  # Validates params, unpacks dependencies, calls func
 ```

 ### Schema Export Methods

 `to_openai_schema()` returns the exact format the OpenAI Chat Completions API expects for its `tools` parameter. This is the format injected into the LLM's system prompt so the LLM knows what it can call.

 `to_mcp_tool_schema()` returns the MCP format: `{name, description, inputSchema}`. The `inputSchema` is structurally identical to the OpenAI `function.parameters` block — only the top-level key names differ.

 ### execute()

 Calls the wrapped `func` with the given keyword arguments. A single Tool may orchestrate multiple Component calls internally. The LLM never knows how many calls happened — it sees one result.

 ## Dependencies

 - **Python standard library**: `dataclasses`, `typing`
 - **Function implementation** (injected via `func`): May depend on DataProvider, MemoryRepository, or other Components
 - **No LLM dependency** (except LLM-Powered Tools, which receive an LLM client via the `dependencies` field at registration time)

 ## Consumers

 | Consumer | How It Uses Tool |
 |---|---|
 | `ToolRegistry` | Registers, retrieves, and executes Tools by name |
 | Agent Runtime | Passes Tool schema list to LLM context window, then dispatches function_call JSON to `ToolRegistry.execute()` |
 | Tests | Creates Tools with mock `func` implementations for isolated testing |

 ## Constraints

 - **Stateless.** A Tool must not store data between calls. If it needs persistent state, it goes through a Component (MemoryRepository)
 - **No Agent-level reasoning.** A Tool does not decide *whether* to do something. The LLM decides. The Tool executes
 - **Description is a runtime interface.** A vague or misleading description directly causes incorrect LLM behavior. Tool descriptions require the same rigor as API documentation
 - **Parameter enums are mandatory where applicable.** If a parameter accepts a known set of values (e.g., index symbols), an `enum` must be declared. This prevents LLM hallucination
 - **Parameter validation is mandatory.** `_validate_params()` runs before every `execute()` call. LLMs occasionally generate correct JSON with wrong types — validation catches this before the error reaches Components. Set `skip_validation=True` only for internal Synthesis Tools called by trusted code paths (not by LLMs)

 ## Future Evolution

 - **V2: Tool-to-Tool calls.** Allow synthesis Tools to call other Tools (currently they only call Components). Requires cycle detection in the call graph
 - **V2: Streaming results.** For Tools that produce large outputs (e.g., `fetch_news` for 50 stocks), stream results incrementally instead of waiting for the full batch
 - **V2: Tool versioning.** Add a `version` field to support deprecating old Tool schemas without breaking existing Agent prompts
