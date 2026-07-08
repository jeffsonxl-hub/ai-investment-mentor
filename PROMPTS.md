# PROMPTS.md -- AI Investment Mentor

How agent prompts are authored, structured, validated, versioned, and tested. Prompts are the source code of agents -- treat them with the same discipline as Python.

---

## Where Prompts Live

```
src/prompts/              # Shared across all agents
  __init__.py             # build_prompt(), validate_output(), version helpers
  base_template.py        # Six-section template builder
  output_models.py        # Shared Pydantic output models (if any)

src/agents/market/        # Agent-specific
  prompts.py              # System prompt, output schema, few-shot examples
  test_prompts.py         # Prompt-specific tests
```

Shared infrastructure lives in `src/prompts/`. Agent-specific prompts live with the agent they belong to. The boundary: if two agents need it, it goes in `src/prompts/`. If only one agent uses it, it stays local.

**Note:** The shared utilities described below (`build_agent_prompt`, `validate_agent_output`, `to_prompt_constraint`) are specified here but implementation ships in Phase 8 alongside the first agent (Market Agent). Phase 7 creates the package with stub signatures only. See TASK-007 Step 5.

---

## System Prompt Template

Every agent prompt follows this fixed template. Six sections, always in this order:

```
1. ROLE        -- "You are a Market Analysis Agent for the Chinese A-share market."
2. TASK        -- "Your job is to assess current market conditions using available tools..."
3. TOOLS       -- Auto-generated from ToolRegistry. Never hand-written.
4. OUTPUT      -- "You must respond with valid JSON matching this schema: {...}"
5. CONSTRAINTS -- "Never guess a value. Set unavailable fields to null."
6. EXAMPLES    -- Few-shot: sample input, correct output.
```

### Why this order

The LLM reads top to bottom. Role and Task establish identity and mission. Tools define capability. Output format tells it what shape to return. Constraints prevent common failure modes (hallucination, overconfidence). Examples ground the abstract format in concrete cases.

### Auto-generated Tools section

Section 3 is never hand-written. `ToolRegistry` already produces LLM-readable tool descriptions:

```python
from src.tools.registry import ToolRegistry

tools_section = ToolRegistry.get_tools_for_agent("market").to_prompt_string()
# Result:
# Available tools:
# - get_index_data: Fetch OHLCV data for a market index...
# - assess_market_regime: Determine current market regime...
```

This eliminates manual sync between tool definitions and prompt text -- a source of drift in hand-maintained prompts.

---

## Two-Layer Output Validation

Every agent output schema uses both layers. The Pydantic model is the source of truth; the prompt schema is derived from it.

### Layer 1: Prompt constraint

Derived automatically from the Pydantic model:

```python
from pydantic import BaseModel, Field

class MarketRegimeOutput(BaseModel):
    market_regime: str = Field(pattern=r"^(BULL|BEAR|SIDEWAYS)$")
    confidence: float = Field(ge=0.0, le=1.0)
    key_factors: list[str] = Field(max_length=3)
    summary: str = Field(max_length=200)

schema = MarketRegimeOutput.to_prompt_constraint()
# "Output your response as a JSON object with exactly these fields:
#  - market_regime: "BULL" | "BEAR" | "SIDEWAYS"
#  - confidence: number between 0.0 and 1.0
#  - key_factors: list of strings, maximum 3 items
#  - summary: string, maximum 200 characters
#  Do not include any text outside the JSON object."
```

### Layer 2: Runtime validation

```python
raw = llm_response_text  # Whatever the LLM returned
try:
    result = MarketRegimeOutput.model_validate_json(raw)
except ValidationError as e:
    # Retry with stronger prompt, or fail gracefully
    ...
```

If the LLM produces malformed JSON, the system stops it at the boundary. The corrupted output never reaches downstream agents or tools.

### Pydantic model as source of truth

The `to_prompt_constraint()` method on each output model generates the prompt text. This prevents drift: you cannot update the model and forget to update the prompt because they are the same definition.

---

## Prompt Versioning

Every prompt file carries a version header. Versions are **monotonically increasing identifiers** (major.minor.patch format, but not strict semver -- prompts don't have traditional "breaking changes" in the API sense). The version serves as traceability: when an agent produces unexpected output, `git log` on the version bump tells you what changed.

```python
# prompts.py -- Market Agent
PROMPT_VERSION = "1.2.0"
# Changelog:
# 1.2.0 - Added SHIBOR rate constraint to market regime output
# 1.1.0 - Added few-shot example for sideways market
# 1.0.0 - Initial prompt
```

Convention:
- Major bump: structural change (new/removed section, new output field)
- Minor bump: content change (rewording, new example, constraint adjustment)
- Patch bump: typo fix, formatting

## Prompt Rollback Strategy

If a prompt change causes degraded agent output, revert by reverting the commit. Old prompt versions are always accessible via git history. For programmatic access (e.g., A/B testing), maintain an `ALL_VERSIONS` dict:

```python
ALL_VERSIONS = {
    "1.0.0": "...",
    "1.1.0": "...",
    "1.2.0": SYSTEM_PROMPT,  # current
}
```

This is optional for V1. Git reversibility is sufficient.

---

## Prompt Testing

Three levels, each testing a different concern:

### Level 1: Schema tests (unit, fast)

Does the output parser accept valid output and reject invalid output?

```python
def test_parses_valid_output():
    raw = '{"market_regime": "BULL", "confidence": 0.85, "key_factors": ["strong PMI"], "summary": "Bullish."}'
    result = MarketRegimeOutput.model_validate_json(raw)
    assert result.market_regime == "BULL"
    assert result.confidence == 0.85

def test_rejects_invalid_regime():
    raw = '{"market_regime": "GRIZZLY", ...}'
    with pytest.raises(ValidationError):
        MarketRegimeOutput.model_validate_json(raw)
```

### Level 2: Template tests (unit, fast)

Does the assembled prompt contain all required sections?

```python
def test_prompt_includes_output_schema():
    prompt = build_market_agent_prompt()
    assert '"market_regime"' in prompt
    assert '"BULL" | "BEAR" | "SIDEWAYS"' in prompt

def test_prompt_includes_tools():
    prompt = build_market_agent_prompt()
    assert 'get_index_data' in prompt
    assert 'assess_market_regime' in prompt
```

### Level 3: Integration tests (slow, uses LLM)

Does the real LLM produce parseable output? **Run these manually or pre-PR only** -- they cost money and time. Not part of the standard `pytest` run.

```python
@pytest.mark.integration
def test_llm_produces_parseable_output():
    response = call_llm(system_prompt=MARKET_AGENT_SYSTEM, user_msg="Assess market regime for SSE Composite")
    parsed = MarketRegimeOutput.model_validate_json(response)
    assert parsed.market_regime in {"BULL", "BEAR", "SIDEWAYS"}
    assert 0.0 <= parsed.confidence <= 1.0
```

Level 3 does NOT test "did the LLM say the right thing" -- that requires human judgment. It only tests structural validity: the output is JSON, the fields are present, the types are correct.

---

## Shared Utilities

`src/prompts/__init__.py` provides (stub in Phase 7, full implementation in Phase 8):

```python
from src.tools.models import Tool

# Build a complete prompt from an agent's template + tools + output model
def build_agent_prompt(
    role: str,
    task: str,
    tools: list[Tool],         # ToolRegistry exports Tool objects, not strings
    output_model: type[BaseModel],
    constraints: list[str],
    examples: list[dict],
) -> str:
    """Assemble the six-section prompt template."""
    ...

# Validate LLM output against its Pydantic model
def validate_agent_output(
    raw: str,
    model: type[BaseModel],
) -> BaseModel:
    """Parse and validate. Raises ValidationError on failure."""
    ...
```

Agents call these, they don't reimplement them.

---

## Full Example: Market Agent Prompt

```python
# src/agents/market/prompts.py

PROMPT_VERSION = "1.0.0"
# Changelog: 1.0.0 - Initial Market Agent prompt

from pydantic import BaseModel, Field
from src.prompts import build_agent_prompt

class MarketRegimeOutput(BaseModel):
    market_regime: str = Field(pattern=r"^(BULL|BEAR|SIDEWAYS)$")
    confidence: float = Field(ge=0.0, le=1.0)
    key_factors: list[str] = Field(max_length=3)
    summary: str = Field(max_length=200)

ROLE = "You are a Market Analysis Agent for the Chinese A-share market."
TASK = "Assess current market conditions using available data tools."
OUTPUT_MODEL = MarketRegimeOutput
CONSTRAINTS = [
    "Never guess a value. If data is unavailable, set the field to null.",
    "Confidence must reflect data quality, not conviction.",
]
EXAMPLES = [
    {"input": "High PMI, rising volumes, broad advance", "output": {
        "market_regime": "BULL", "confidence": 0.85,
        "key_factors": ["PMI above 50", "volume expansion", "broad participation"],
        "summary": "Bullish market supported by macro and technical confirmation."
    }},
]

SYSTEM_PROMPT = build_agent_prompt(ROLE, TASK, [], OUTPUT_MODEL, CONSTRAINTS, EXAMPLES)
```