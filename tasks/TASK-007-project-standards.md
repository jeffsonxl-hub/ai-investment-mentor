# TASK-007: Project Engineering Standards

## Goal
Establish the engineering standards defined in ADR-007 before agent implementation begins in Phase 8.

## Prerequisites
- ADR-007 accepted
- All existing tests pass (baseline)

## Implementation Steps

### Step 1: Create DEVELOPMENT.md
Create root-level DEVELOPMENT.md covering:
- Type hints policy (all public signatures must be typed)
- Docstring standard (Google-style, public interfaces only)
- Import ordering (stdlib, third-party, local; absolute imports only)
- Line length (100 characters)
- Linting (ruff)
- Type checking (mypy, informational for V1)
- Testing structure (unit/, integration/, prompts/)
- Pre-commit checklist

### Step 2: Create PROMPTS.md
Create root-level PROMPTS.md covering:
- Where prompts live (src/prompts/ shared, src/agents/X/ agent-specific)
- System prompt template (Role, Task, Tools, Output Format, Constraints, Examples)
- Two-layer output validation (prompt constraint + Pydantic model)
- Prompt versioning (monotonically increasing identifiers; every prompt file carries a version header)
- Prompt rollback strategy (old versions kept in git history; ALL_VERSIONS dict for programmatic access)
- Prompt testing (schema tests, template tests, integration tests -- LLM integration tests run manually or pre-PR only)
- Shared utilities specification (build_prompt, validate_output -- implementation deferred to Phase 8 alongside first agent)

### Step 3: Create docs/architecture/09-project-standards.md
Architecture-level summary pulling together decisions from ADR-007:
- Directory layout diagram (Mermaid)
- Development standards summary table
- Prompt lifecycle (author -> version -> validate -> test -> deploy)
- Git workflow diagram
- Codex collaboration cycle

### Step 4: Add toolchain configuration
- Add [tool.ruff] section to pyproject.toml (config defined in DEVELOPMENT.md)
- Add [tool.mypy] section to pyproject.toml
- Create .editorconfig at project root
- Run `ruff check src/` and fix any existing violations, or add `# noqa` for intentional deviations
- Add `.ruff_cache/` and `.mypy_cache/` to `.gitignore`

### Step 5: Create src/prompts/ package
- src/prompts/__init__.py with stub implementations
- Shared utility signatures (build_agent_prompt, validate_agent_output) defined but full implementation ships in Phase 8 alongside the first agent

### Step 6: Update living documents
- ROADMAP.md: mark Phase 7 as Complete
- STATE-OF-THE-PROJECT.md: update Current Task to Phase 8
- LEARNINGS.md: add entry if Phase 7 taught anything not already captured

### Step 7: Acceptance
- All existing tests pass
- ruff check src/ -- no errors
- DEVELOPMENT.md and PROMPTS.md exist and are referenced from AGENTS.md
- Phase Validation Checklist passes