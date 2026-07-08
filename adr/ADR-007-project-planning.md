# ADR-007: Project Engineering Standards

## Status
Accepted

## Context

Phases 0-6 established the architecture: Agents, Components, Tools, Memory, Data, Orchestrator. Phase 7 is the last phase before agent implementation begins (Phase 8: Market Agent). The codebase now spans 4 source packages, 106 tests, 34 tools, and 6 ADRs. Before adding agent code -- which is inherently harder to test and debug than deterministic components -- we need shared engineering standards.

Without explicit standards, each agent will develop its own conventions for prompts, testing, imports, and code style. Debugging cross-agent issues becomes a convention-guessing exercise.

The decisions below cover: directory layout, development standards, prompt engineering standards, git workflow, and Codex collaboration patterns.

## Decision

### 1. Directory layout

```
src/
  agents/              # Agent implementations (Phase 8+)
    market/            # prompts.py, agent.py, tests
    research/
    advisor/
    stock_selection/
    watchlist/
  data/                # DataProvider, AkShareClient (existing)
  memory/              # MemoryRepository (existing)
  pipeline/            # Orchestrator DAG (existing)
  tools/               # Tool, ToolRegistry (existing)
  prompts/             # Shared: base templates, format helpers, versioning
agents/                # Agent spec documents (existing, unchanged)
components/            # Component spec documents (existing, unchanged)
```

`src/agents/` isolates agent code from deterministic components. Each agent is a subpackage with its own prompts, implementation, and tests. `src/prompts/` holds shared infrastructure: base template builder, Pydantic output models, version tracker.

### 2. Development standards

| Rule | Detail |
|---|---|
| Type hints | All public function signatures must be typed. Internal helpers may relax. |
| Docstrings | Google-style for public interfaces. Args/Returns/Raises required. No docstrings on trivial private helpers. |
| Imports | Three blocks: stdlib, third-party, local (`src.` prefix). Absolute imports only -- no relative `..` across package boundaries. |
| Line length | 100 characters (prompt strings are long). |
| Linting | `ruff` for both linting and formatting. Config in `pyproject.toml`. |
| Type checking | `mypy` on CI (not blocking for V1, informational). |
| Testing | `tests/unit/` mirrors `src/`. `tests/integration/` for external dependencies. `tests/prompts/` for prompt output schema validation. |

### 3. Prompt standards

Every agent prompt follows a fixed template with six sections: Role, Task, Tools (auto-generated from ToolRegistry), Output Format, Constraints, Few-shot Examples.

Output schemas use two-layer validation: a prompt-level format constraint ("You must respond with valid JSON matching this schema") AND a Pydantic model that validates at runtime. The Pydantic model is the source of truth; the prompt schema is derived from it.

Every prompt file carries a version header:
```python
PROMPT_VERSION = "1.0.0"
# Changelog: 1.0.0 - Initial prompt
```

Prompt tests cover three levels: schema validation (does the parser reject bad JSON?), template completeness (does the assembled prompt contain all required sections?), and lightweight integration (does the LLM produce parseable output for a known input?).

### 4. Git workflow

| Rule | Detail |
|---|---|
| Branch naming | `codex/phase-N-short-description` (matches existing prefix) |
| Commit format | Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:` |
| Merging | PR-based for feature branches. Squash merge to keep history clean. |
| No force push | To shared branches. Local feature branches are fine. |
| Before commit | Full test suite must pass. `requirements.txt` must be current. |

### 5. Codex collaboration

Every phase follows: concept discussion -> architecture decisions -> document generation -> plan-eng-review -> implementation -> review.

Tasks for Codex must be specific enough to implement without guessing. This means: exact file paths, expected function signatures, test cases. The TASK file format (established in Phase 2) remains the standard.

The Phase Validation Checklist in AGENTS.md runs before every phase's document generation. The Pre-Delivery Smoke Test runs before declaring any phase complete.

## Consequences

**What becomes easier:**
- Onboarding a new session: read LEARNINGS.md, DEVELOPMENT.md, PROMPTS.md -- you know how the project works.
- Agent debugging: prompt version header tells you if the prompt changed. Pydantic validator tells you if the output is malformed. Schema test tells you if the parser is broken.
- Cross-agent consistency: every agent prompt follows the same template. Every agent output goes through the same validation pipeline.

**What becomes harder:**
- Quick hacks are more visible. Skipping type hints or prompt versioning will be caught by review.
- Initial agent development has more boilerplate (prompt template, Pydantic model, schema test). This pays off by Phase 9 when we have 4 agents and can't afford ad-hoc conventions.

## Alternatives Considered

### Alternative A: No formal prompt standards
Let each agent developer write prompts however they want. Rejected because debugging a 4-agent system where each agent has different output formats and no validation is a nightmare.

### Alternative B: LangChain prompt templates from the start
Use LangChain's `ChatPromptTemplate` and output parsers. Rejected because it adds a dependency before we need it, and LangGraph (Phase 12) has its own prompt system that would conflict.

### Alternative C: pytest only, no ruff/mypy
Skip static analysis, rely on tests alone. Rejected because agent code has failure modes (malformed LLM output, prompt drift) that tests can't catch at the unit level. `ruff` catches import ordering issues and unused variables that cause subtle runtime bugs in async agent code.