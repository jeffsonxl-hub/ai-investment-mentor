# ADR-001: Advisor-Centric Architecture

## Status
Accepted

## Context

We need to decide how intelligence is organized in the AI Investment Mentor system. The system must: analyze A-share market conditions, extract and classify news, track user watchlists, score candidate stocks, and generate explainable recommendations.

The core question: should these capabilities be implemented as one monolithic Agent that does everything, or as a coordinator (Advisor) that delegates to specialist Agents?

A monolithic Agent would be simpler to build initially ¡ª fewer interfaces, fewer components, one prompt to manage. But it would mix concerns (market analysis and stock picking and news parsing in one reasoning pass), making it harder to debug why a particular recommendation was made.

## Decision

We will use an **Advisor-centric architecture**: one Advisor Agent that orchestrates specialist Agents (Market, Research, Watchlist), synthesizes their structured output, and produces the final morning report. Specialist Agents never call each other ¡ª all coordination flows through the Advisor.

```
Specialist Agents (produce evidence)
       ©¦
       ¨‹
Advisor Agent (synthesizes + explains)
       ©¦
       ¨‹
     User
```

## Consequences

**What becomes easier:**
- **Debuggability.** Every recommendation traces back to specific evidence from specific Agents. If the Market Agent misclassifies a regime, we fix it without touching the scoring logic
- **Independent iteration.** We can improve the Research Agent news classification without risking the Watchlist Agent
- **Testing.** Each Agent can be tested in isolation with mock inputs. The Advisor can be tested with canned Market Context and Events
- **Codex implementation.** Smaller, focused TASK documents that Codex can implement without understanding the entire system

**What becomes harder:**
- **Interface discipline.** We must define and maintain structured data contracts between Agents. A monolithic Agent would avoid this overhead
- **Latency.** The Advisor must wait for all specialist Agents before proceeding. We mitigate this by running specialists in parallel where possible
- **Initial complexity.** More files, more docs, more setup. The payoff comes at Phase 8+ when we build each Agent independently

## Alternatives Considered

### Alternative A: Monolithic Agent
One Agent reads market data, news, watchlist, and directly produces a morning report. Simpler to build in Phase 1, but every change risks breaking the entire report pipeline. Rejected because the project explicitly aims to teach Agent architecture ¡ª a monolith teaches nothing about Agent design.

### Alternative B: Peer-to-Peer Agents
Agents communicate directly with each other (Market tells Research what to analyze, Research tells Advisor what it found). This creates circular dependencies and makes testing nearly impossible without the full system running. Rejected because it violates the "single responsibility" rule.

### Alternative C: Event-Driven Agents
Agents publish events to a message bus. Others subscribe. Elegant for production systems but massive over-engineering for a single-user Python tool. Rejected for V1 ¡ª this is a natural V3 consideration if the system ever becomes multi-user.
