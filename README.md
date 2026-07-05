# AI Investment Mentor

An AI-powered personal investment mentor for A-share (Chinese stock market) investors. The system analyzes market conditions, extracts structured evidence from news and data, and generates a daily morning report with 5-10 explainable stock candidates ¡ª teaching the user to think like an investor, not just pick stocks.

## Mission
Build a personal AI investment mentor that explains recommendations with evidence rather than making opaque predictions. The human always makes the final decision.

## Architecture
Advisor-centric: one Advisor Agent orchestrates three specialist Agents (Market, Research, Watchlist). Specialist Agents produce structured evidence. The Advisor synthesizes and explains. No Agent accesses data sources directly.

```
Market Agent ©¤©¤©´
Research Agent ©¤©È
Watchlist Agent ©¤©à©¤©¤? Advisor Agent ©¤©¤? User (Morning Report)
```

## Principles
- Architecture first, code second
- Evidence-based recommendations with traceable source chains
- Human makes the final decision ¡ª the system recommends, never executes
- Specialist Agents with single responsibilities
- Deterministic logic before LLM reasoning
- Degrade gracefully ¡ª partial output is better than no output

## Project Status

**Current Phase**: Step 0 complete ¡ª Phase 2 & 3 documentation rebuilt to engineering standard. Ready for Phase 4 (System Architecture).

| Stage | Phases | Status |
|---|---|---|
| Stage 0 ¡ª AI Native Mindset | Phase 0 | Complete |
| Stage 1 ¡ª Agent Design | Phases 1-3 | Complete (docs rebuilt 2026-07-04) |
| Stage 2 ¡ª Architecture | Phases 4-7 | Phase 4 next |
| Stage 3 ¡ª Agent Engineering | Phases 8-11 | Planned |
| Stage 4 ¡ª LangGraph Orchestration | Phases 12-14 | Planned |
| Stage 5 ¡ª AI Mentor | Phases 15-16 | Planned |

## Documentation

### Project Standards
- `PROJECT_RULES.md` ¡ª All engineering standards, templates, and rules
- `ROADMAP.md` ¡ª Full 16-phase roadmap
- `AGENTS.md` ¡ª Codex collaboration instructions
- `docs/STATE-OF-THE-PROJECT.md` ¡ª Project backstory and current state (read first)

### Architecture Docs
- `docs/architecture/01-product-vision.md` ¡ª Who this is for and what success looks like
- `docs/architecture/02-system-overview.md` ¡ª Architecture layers, data flow, Mermaid diagrams
- `docs/architecture/03-agent-design.md` ¡ª All four Agent specifications using the standard template
- `docs/architecture/04-decision-flow.md` ¡ª 7-step decision flow with Mermaid diagrams
- `docs/05-memory-design.md` ¡ª Memory architecture: three types, SQLite schema, access patterns

### Decisions
- `adr/ADR-001-system-philosophy.md` ¡ª Why Advisor-centric architecture
- `adr/ADR-002-agent-responsibilities.md` ¡ª Agent data access boundaries
- `adr/ADR-003-memory-strategy.md` ¡ª Hybrid memory strategy (SQLite, no RAG)

### Components
- `components/memory-repository.md` ¡ª MemoryRepository Component specification

### Tasks
- `tasks/TASK-001-project-bootstrap.md` ¡ª Project skeleton setup
- `tasks/TASK-003-memory-layer.md` ¡ª MemoryRepository implementation

## Getting Started (for Codex)
Read these in order:
1. `docs/STATE-OF-THE-PROJECT.md`
2. `PROJECT_RULES.md`
3. `ROADMAP.md`
4. All files in `docs/architecture/`
5. Then proceed with the current TASK

## Technology (V1)
- Python 3.11+
- SQLite for all persistence
- OpenAI-compatible API for LLM calls
- AkShare / TuShare for A-share market data
- LangGraph in Phase 12+ (not yet)
