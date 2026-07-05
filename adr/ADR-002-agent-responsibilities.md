# ADR-002: Agent Responsibilities & Data Access Boundaries

## Status
Accepted

## Context

With four specialist Agents and one Advisor, we need clear rules about what each Agent is allowed to do ¡ª and what it is explicitly forbidden from doing. Without boundaries, an Agent will naturally expand its scope, duplicating logic and creating confusion about where truth lives.

Two specific boundary questions emerged during design:

1. **Should the Advisor Agent be allowed to access the Data Layer directly?** It is tempting: if the Advisor wants to double-check a stock price, why force it to ask the Market Agent? The answer is that direct data access erodes traceability ¡ª a recommendation cannot be audited if the Advisor fetched data outside the structured evidence chain.

2. **Should specialist Agents be allowed to call each other?** For example, the Research Agent could call the Market Agent for sector context when classifying news. This is convenient but creates hidden dependencies. If the Market Agent changes its output format, both the Advisor and Research Agent would break.

## Decision

Three hard boundaries are now project law:

1. **The Advisor Agent never accesses the Data Layer directly.** All data reaches the Advisor through structured output from specialist Agents. The Advisor works with evidence, not raw data.

2. **Specialist Agents never call each other.** The Advisor is the sole orchestrator. If the Research Agent needs market context, the Advisor provides it as an input parameter.

3. **Every Agent accesses Memory only through MemoryRepository.** No Agent opens a database connection, writes SQL, or manages file handles. The Component Layer is the only path to persistence.

## Consequences

**What becomes easier:**
- **Auditability.** Open any recommendation: the evidence trail is a straight line from Data Layer ¡ú Tool ¡ú Agent ¡ú Advisor ¡ú Report. No side channels exist
- **Replaceability.** We can swap the Market Agent implementation without touching any other Agent ¡ª the data contract is the only coupling point
- **Parallel development.** Two people (or two Codex sessions) can work on different Agents simultaneously without merge conflicts

**What becomes harder:**
- **Orchestration overhead.** The Advisor must explicitly gather all context before calling a specialist Agent. More boilerplate, more parameters
- **Data duplication.** The Advisor may pass the same Market Context to multiple Agents. In a direct-access model, each Agent would fetch what it needs
- **Latency from serialization.** Inter-Agent data passes through JSON serialization. For large datasets (e.g., all news for 500 stocks), this adds measurable overhead

## Alternatives Considered

### Alternative A: Advisor with direct data access

The Advisor could call `get_stock_price()` directly as a sanity check. Rejected because it creates two paths to the same data and makes it impossible to audit whether a recommendation came from specialist analysis or an undisclosed direct lookup.

### Alternative B: Shared data context object

All Agents read from a shared in-memory context (like a global variable). This is how LangGraph State works, and it is actually the right approach for Phase 13+. But for V1 with a simple Python orchestrator, a shared mutable state introduces debugging nightmares. Rejected for V1 ¡ª revisit as part of LangGraph migration.
