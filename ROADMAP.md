# Roadmap: AI Investment Mentor

16 phases across 5 stages, from mindset to adaptive AI mentor.

---

## Stage 0 — AI Native Mindset

| Phase | Status | Focus |
|-------|--------|-------|
| [Phase 0](docs/architecture/01-product-vision.md) | ? Complete | AI Native thinking — why Agent ≠ ChatGPT |

---

## Stage 1 — Agent Design

| Phase | Status | Focus |
|-------|--------|-------|
| [Phase 1](docs/architecture/03-agent-design.md) | ? Complete | Agent Design — why agents divide responsibilities |
| [Phase 2](tasks/TASK-001-project-bootstrap.md) | ? Implemented | Decision Flow — AI narrows from whole market to final recommendation |
| Phase 3 | [TASK-003](tasks/TASK-003-memory-layer.md) | ? Implemented | Memory Layer — SQLite persistence, three memory types, hybrid strategy |

**Deliverable:** V1 Agent Design Document, complete decision flow.

---

## Stage 2 — Architecture

| Phase | Status | Focus |
|-------|--------|-------|
| Phase 4 | [TASK-004](tasks/TASK-004-orchestrator-scaffold.md) | ? Implemented | System Architecture — DAG orchestrator, dependency injection, severity model — Agent, Memory, Tool, Workflow; V1 architecture diagram |
| Phase 5 | [TASK-005](tasks/TASK-005-data-layer.md) | Implemented | Data Layer Design — AkShare, TuShare, news, announcements, database |
| Phase 6 | ?? Planned | Tool Design — Tool vs Agent vs Memory boundary; why MCP exists |
| Phase 7 | ?? Planned | Project Planning — directory structure, dev standards, prompt standards, git workflow, Codex collaboration |

**Deliverable:** V1 system architecture, data layer design, tool catalog, project standards.

---

## Stage 3 — Agent Engineering

| Phase | Status | Focus |
|-------|--------|-------|
| Phase 8 | ?? Planned | Market Agent — first agent built; all agents depend on data |
| Phase 9 | ?? Planned | Research Agent — prompt engineering, tool calling, news & announcement analysis |
| Phase 10 | ?? Planned | Advisor Agent — synthesize multiple agents into readable investment advice |
| Phase 11 | ?? Planned | Stock Selection Agent — screening with scoring: capital, fundamentals, news, technical |

**Deliverable:** Four working agents: Market, Research, Advisor, Stock Selection.

---

## Stage 4 — LangGraph Orchestration

| Phase | Status | Focus |
|-------|--------|-------|
| Phase 12 | ?? Planned | Why Graph — Python workflow vs LangGraph comparison |
| Phase 13 | ?? Planned | LangGraph Rebuild — State, Node, Edge, Conditional Edge, Parallel, Human-in-the-Loop |
| Phase 14 | ?? Planned | Advanced LangGraph — Reflection, Retry, Checkpoint, Long-running Workflow |

**Deliverable:** Full system rebuilt on LangGraph with production-grade agent capabilities.

---

## Stage 5 — AI Mentor

| Phase | Status | Focus |
|-------|--------|-------|
| Phase 15 | ?? Planned | Investment Mentor — explanations: rationale, risk, evidence, confidence, learning points |
| Phase 16 | ?? Planned | Evolution — feedback loop, evaluation, prompt versioning, continuous optimization |

**Deliverable:** A system that teaches you to invest, not just picks stocks.

---

## Phase Detail

### Phase 0 — AI Native Thinking ?
Foundation: understand why Agent ≠ ChatGPT. Agents maintain state, make decisions, and act autonomously over time.

### Phase 1 — Agent Design ?
Why divide responsibilities across agents. Each agent owns a clear domain, reducing complexity and enabling independent iteration.

### Phase 2 — Decision Flow (Implemented)
The core of the course. Design the step-by-step process AI uses to go from the full market down to a final recommendation. No code — pure decision flow.

### Phase 3 — Memory Layer ?
Hybrid memory strategy with SQLite persistence. Three memory types: Watchlist, Market, Decision. MemoryRepository component (no LLM, no business logic). Deliverables: [ADR-003](adr/ADR-003-memory-strategy.md), [design doc](docs/architecture/05-memory-design.md), [component spec](components/memory-repository.md), [TASK-003](tasks/TASK-003-memory-layer.md).

### Phase 4 — System Architecture
Design the full system: Agent, Memory, Tool, and Workflow layers. Produce the first system architecture diagram.

### Phase 5 — Data Layer Design
Pivoted from TuShare to pure AkShare after rate-limit issues. AkShareClient: stock_zh_a_hist (OHLCV), stock_zh_a_spot (PE/PB/market cap), stock_info_a_code_name (names), plus macro/news/flow. Single DataProvider Component with graceful degradation. TuShareClient kept as optional. 64 unit + 8 integration tests. ADR-005 accepted.

### Phase 6 — Tool Design
Clear boundaries: what is a Tool, what is an Agent, what is Memory. Introduction to MCP — not how to configure it, but why it exists as a protocol.

### Phase 7 — Project Planning
Codex begins. Directory structure, development standards, prompt standards, git workflow. Heavy emphasis on how to collaborate effectively with Codex.

### Phase 8 — Market Agent
First agent implementation. Market Agent comes before Advisor because every agent depends on data access.

### Phase 9 — Research Agent
Prompt engineering, tool calling, news analysis, announcement parsing, structured output generation.

### Phase 10 — Advisor Agent
The most important code phase. Synthesize output from multiple agents into genuinely readable, actionable investment advice.

### Phase 11 — Stock Selection Agent
Real stock screening. Multi-dimensional scoring: capital flow, fundamentals, news sentiment, technical indicators.

### Phase 12 — Why Graph
Compare the existing Python workflow with LangGraph. Understand the problem LangGraph solves before adopting it.

### Phase 13 — LangGraph Rebuild
Rebuild the entire system on LangGraph: State, Node, Edge, Conditional Edge, Parallel execution, Human-in-the-Loop.

### Phase 14 — Advanced LangGraph
Production-grade patterns: Reflection, Retry, Checkpoint, Long-running Workflow. The system becomes truly agentic.

### Phase 15 — Investment Mentor
The system stops just recommending stocks and starts explaining why. Every stock gets: rationale, risk assessment, evidence, confidence score, and learning points.

### Phase 16 — Evolution
The system learns. If a stock-picking pattern underperforms over a month, scores auto-adjust. Feedback loop, evaluation, prompt versioning, continuous optimization — the assistant adapts to your investment style.











