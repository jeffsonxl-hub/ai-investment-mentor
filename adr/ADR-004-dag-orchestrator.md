# ADR-004: DAG-Based Orchestrator (No Framework)

## Status
Accepted

## Context

The system has four Agents (Market, Research, Watchlist, Advisor) and a 7-step decision flow that must execute every morning. The flow is partially parallel (Steps 1-3 can run simultaneously) and partially sequential (Steps 4-7 depend on earlier output).

We need to decide: how does the system actually execute this flow at runtime? The options range from a simple Python script to adopting a full workflow framework like LangGraph.

Key constraints:
- V1 is a single-user personal tool, not a production service
- Phase 12 of the roadmap is specifically "Why Graph" ！ contrasting a Python workflow with LangGraph
- The user is learning agent architecture, not just building a product
- Parallel execution of Steps 1-3 is important for pipeline latency (target: < 120 seconds total)

## Decision

We will implement a lightweight DAG-based `Pipeline` Component using Python `asyncio`. It supports:
- Explicit step dependencies (steps declare what they wait for)
- Automatic parallel execution of independent steps
- Per-step severity (Critical = abort pipeline on failure, Warning = continue degraded)
- One automatic retry for failed steps
- Step timeouts (30 seconds default)

We will **not** adopt LangGraph, CrewAI, Prefect, or any other workflow framework for V1. The Pipeline is ~60 lines of pure Python with no external dependencies.

## Consequences

**What becomes easier:**
- **Learning gradient.** We build the orchestration ourselves, feel the pain points, and understand *why* LangGraph exists before adopting it in Phase 12
- **Zero framework overhead.** No new dependencies, no new concepts to teach. `asyncio` is in the standard library
- **Full control.** Error handling, retry logic, and parallelism are explicit ！ nothing is hidden behind framework abstractions
- **Testability.** The Pipeline is a pure Component with no LLM access. Every behavior (parallelism, retry, abort) is testable with mock step functions

**What becomes harder:**
- **Manual complexity.** As the pipeline grows beyond ~15 steps, managing dependencies manually becomes tedious. LangGraph's visual graph editor and state management would help
- **No built-in persistence.** LangGraph's Checkpointing (automatic state save/resume) is not available. If the pipeline crashes at Step 6, the entire run is lost ！ no resume
- **No built-in observability.** LangGraph Studio provides visual tracing. Our Pipeline logs to JSON lines, which is functional but not visual
- **Migration cost.** When we adopt LangGraph in Phase 12, we will need to rewire Agents from Pipeline steps to LangGraph nodes. This is acceptable because the Agent code itself (the `run()` method) stays the same ！ only the orchestration wrapper changes

## Alternatives Considered

### Alternative A: Simple Sequential Script
A Python script that calls each Agent in order with no parallelism and no retry logic. Rejected because: (a) Steps 1-3 should run in parallel for performance, (b) error handling must be per-step and systematic, not ad-hoc, (c) a script does not teach anything about orchestration patterns.

### Alternative B: LangGraph from Phase 4
Adopt LangGraph immediately instead of waiting for Phase 12. Rejected because: (a) Phase 12 exists specifically to teach the comparison ！ skipping to LangGraph now eliminates that learning, (b) LangGraph adds ~5 dependencies and a conceptual overhead that is unnecessary for a 7-step pipeline, (c) the user explicitly wants to learn *why* frameworks exist, not just use them.

### Alternative C: Event-Driven (Message Bus)
Agents publish events to a bus. The Advisor subscribes to MarketContextReady, EventsReady, WatchlistReady. Rejected because: (a) event-driven architectures are great for 10+ loosely coupled agents but overkill for 4, (b) traceability suffers ！ reconstructing the causal chain of a recommendation requires replaying event history, (c) adds infrastructure (message broker) that a single-user tool does not need.
