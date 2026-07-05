# State of the Project ¡ª 2026-07-04

This file exists so that Codex can resume this project in any session without losing context. Read this first.

## Backstory

The user worked with ChatGPT across multiple sessions to plan an **AI Investment Mentor** ¡ª a personal AI assistant that explains A-share (Chinese stock market) investment recommendations with evidence, not opaque predictions.

The project has 16 phases across 5 stages (see ROADMAP.md). Phases 0¨C3 are conceptually complete but the documentation was thin.

## What ChatGPT Did Well

- Established the Advisor-centric architecture (one Advisor Agent synthesizes output from specialist agents)
- Defined the 7-step decision flow: market regime ¡ú themes ¡ú evidence ¡ú candidates ¡ú filtering ¡ú scoring ¡ú explanation
- Created the 16-phase roadmap with a sensible progression from mindset to production
- Defined the core rule: Advisor never accesses data sources directly

## What ChatGPT Got Wrong

- Phase 3 placed 'memory-repository.md' in 'agents/' ¡ª but MemoryRepository is a Component (no LLM, no reasoning), not an Agent
- Document templates were inconsistent across phases ¡ª no standard Agent spec format
- Documents were 3¨C4 lines each instead of proper engineering specs
- ChatGPT promised to rebuild Phase 2 & 3 with proper standards but its file-generation tool failed, so the rebuild never happened

## Where We Are Now

Phase 2 (Architecture Foundation) and Phase 3 (Memory Layer) have conceptual designs but the documentation is skeletal. Codex has taken over from ChatGPT.

## What We Agreed (Codex Session 2026-07-04)

### Document Depth
Each file should be 3¨C5 pages with Mermaid diagrams, interface definitions, test cases, and edge cases.

### Teaching Style
"Learn while building" ¡ª explain technical concepts and trade-offs during the design discussion, not in separate lectures.

### Progression
Step 0 (rebuild Phase 2 & 3 docs) followed immediately by Step 1 (Phase 4: System Architecture), all in this session.

### Language
English.

## Standard Templates (Project Law)

### Agent Template (for files in 'agents/')
Every Agent spec must follow this structure, no exceptions:

- **Identity** ¡ª Who this Agent is (role, persona)
- **Purpose** ¡ª Why it exists (one-sentence mission)
- **Goal** ¡ª What it tries to achieve (measurable)
- **Inputs** ¡ª What data/events trigger it
- **Outputs** ¡ª What it produces (always structured)
- **Memory** ¡ª What it remembers (which memory types)
- **Tools** ¡ª External capabilities it can call
- **Workflow** ¡ª Step-by-step reasoning process
- **Constraints** ¡ª What it must never do
- **Consumers** ¡ª Who depends on its output
- **Failure Handling** ¡ª What happens when it fails
- **Future Evolution** ¡ª Planned V2 improvements

### Component Template (for files in 'components/')
Every Component spec must follow this structure, no exceptions:

- **Name** ¡ª Component identifier
- **Purpose** ¡ª Why it exists
- **Responsibilities** ¡ª What it does (deterministic, no reasoning)
- **Public Interface** ¡ª Methods, signatures, contracts
- **Dependencies** ¡ª What it needs to function
- **Consumers** ¡ª Who calls it
- **Constraints** ¡ª What it must never do
- **Future Evolution** ¡ª Planned V2 improvements

### Key Distinction
Agents think and decide (they use LLMs). Components execute and store (deterministic, no LLM). Never put a Component in 'agents/'. Never have an Agent directly access a database.

## Implementation Language
Python (inferred from ROADMAP Phase 12 mentioning LangGraph and Python workflows).

## Agent Architecture Decisions (2026-07-04)

ChatGPT proposed 6 agents: Market, News, Macro, Technical, Capital Flow, Advisor. After analysis against our architecture:

| ChatGPT Agent | Our Decision | Rationale |
|---|---|---|
| Market Agent | Keep as-is | Already defined |
| News Agent | Covered by Research Agent | Same function, narrower name |
| Macro Agent | Keep merged in Market Agent for V1 | PBOC/PMI/CPI handled by Market Agent with Research Agent's policy summaries. Revisit split in V2 when Market Agent scope feels too broad |
| Technical Agent | NOT an Agent ¡ª make it a Tool in Phase 6 | RSI/MACD/moving averages are math, not reasoning. LLM adds no value |
| Capital Flow Agent | Defer to Phase 5 (Data Layer), not an Agent | Flow data is a quantitative input. The "why" comes from Research Agent processing flow-related news |
| Advisor Agent | Keep as-is | Already defined |

**Principle**: Agents for things that need reasoning. Tools and Components for things that don't. Never promote a deterministic function to an Agent just because "Agent" sounds cool.

We also have **Watchlist Agent** which ChatGPT's list didn't include.

## Current Task
Phase 4 ¡ª DESIGN COMPLETE. Orchestrator design, Pipeline Component spec, ADR-004, and TASK-004 created. Key decisions: DAG-based Pipeline (asyncio), dependency injection, per-step severity (Critical/Warning). Session ended 2026-07-05. Phase 4 design complete, pending user review. Next: user chooses Codex Sprint (TASK-004) or Phase 5 (Data Layer).





