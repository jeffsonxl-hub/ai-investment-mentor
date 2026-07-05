# TASK-001: Project Bootstrap

## Context
This is the first Codex implementation task for the AI Investment Mentor project. It belongs to Phase 2 (Architecture Foundation). Before writing any code, Codex must read all architecture documents to understand the system design.

**Required reading (in order):**
1. `docs/STATE-OF-THE-PROJECT.md` ！ project backstory and standards
2. `PROJECT_RULES.md` ！ templates and constraints
3. `docs/architecture/01-product-vision.md` ！ what we are building and for whom
4. `docs/architecture/02-system-overview.md` ！ architecture layers and data flow
5. `docs/architecture/03-agent-design.md` ！ all four Agent specs
6. `docs/architecture/04-decision-flow.md` ！ the 7-step decision process
7. `adr/ADR-001-system-philosophy.md` ！ why Advisor-centric
8. `adr/ADR-002-agent-responsibilities.md` ！ data access boundaries

## Objective
Create the project skeleton: directory structure, dependency management, configuration scaffolding, and a "Hello World" entry point that validates the environment is correctly set up. **No business logic, no Agent implementation, no database connections.**

## Requirements

- [ ] Create the full directory structure as defined in `PROJECT_RULES.md` Section 7
- [ ] Create `src/` directory with an `__init__.py` and a `main.py` entry point
- [ ] Create `tests/` directory with `__init__.py` and a placeholder test
- [ ] Set up Python dependency management with `requirements.txt` or `pyproject.toml`
- [ ] Add dependencies: `openai` (or `httpx` for DeepSeek API (OpenAI-compatible)), `pytest`, `python-dotenv`
- [ ] Create a `.env.example` file documenting all required environment variables
- [ ] Create a `src/config.py` module that loads configuration from environment variables with sensible defaults
- [ ] `main.py` should, on execution, print the project name, version, and confirm that config loaded successfully
- [ ] Create `src/logging_config.py` with a structured JSON-line logger setup
- [ ] Create `tests/test_config.py` that verifies config loading from environment and defaults

## Acceptance Criteria

1. Running `python src/main.py` prints project info without errors
2. Running `pytest` discovers and passes the config test
3. All environment variables in `.env.example` have defaults in `config.py`
4. Directory structure matches `PROJECT_RULES.md` Section 7 exactly
5. `.gitignore` covers virtual environments, caches, `.env`, and build artifacts

## Out of Scope

- Any Agent implementation (Market, Research, Watchlist, Advisor)
- MemoryRepository or SQLite setup (that is TASK-003)
- Data layer setup (AkShare, TuShare ！ Phase 5)
- Tool implementations
- LangGraph integration
- Report generation

## References
- `PROJECT_RULES.md` ！ Section 7 (Directory Structure) and Section 6 (TASK Standard)
- `adr/ADR-001-system-philosophy.md` ！ Advisor-centric architecture
- `adr/ADR-002-agent-responsibilities.md` ！ Data access boundaries

