# Learnings -- AI Investment Mentor

This document captures what we discover the hard way across all 16 phases. Each entry is a lesson that changed how we build. Read it alongside ROADMAP.md (where we're going) and STATE-OF-THE-PROJECT.md (where we are now).

No template, no quota -- just dated entries. If you'd want to remember it two phases from now, it belongs here.

---

## 2026-07-08 -- Agent != Component (Phase 3)

**What happened:** Phase 3 placed `MemoryRepository` in `agents/`. MemoryRepository stores and retrieves data -- it has zero LLM calls, zero reasoning, zero decisions.

**The lesson:** Agents think and decide (they use LLMs). Components execute and store (deterministic, no LLM). The boundary is not cosmetic -- putting a Component in `agents/` tells future readers "this thing reasons," and they'll build Agent-style tests and error handling for a database wrapper.

**Rule:** If you can write a unit test for it without mocking an LLM, it's a Component. Put it in `components/` or `src/`. Never in `agents/`.

**Meta-lesson:** This was bad enough that we created the Phase Validation Checklist in AGENTS.md. Architectural rules encoded in memory fail. Rules encoded in a checklist run before every phase don't.

---

## 2026-07-08 -- DAG over ad-hoc orchestration (Phase 4)

**What happened:** The orchestrator was designed as an explicit DAG with dependency edges, not a linear script.

**The lesson:** In a system where agents depend on agents, "run step 1, then step 2" breaks the moment step 2 doesn't actually need step 1's output. A DAG makes dependencies explicit: the orchestrator knows market_data and news can run in parallel, and only advisor waits for both. Fewer idle cycles, clearer failure boundaries.

**Rule:** Any multi-step workflow with partial ordering should be a DAG. If two steps can run simultaneously, the graph should express that -- don't serialize them just because it's easier to write.

---

## 2026-07-08 -- Don't marry a single data API (Phase 5)

**What happened:** The original design was TuShare-only. TuShare's free tier had aggressive rate limits. We pivoted to a dual-source strategy (AkShare primary for macro/news/flow, TuShare for fundamentals), then later pivoted again to AkShare-only after TuShare registration issues.

**The lesson:** Free-tier APIs break. Rate limits tighten. Registration portals close. Designing the DataProvider as a single interface with swappable backends meant these pivots touched one file, not every agent that consumed data.

**Rule:** Every external API gets wrapped in its own Client class. The Component that agents call never exposes which client is underneath. Graceful degradation (partial data > no data) is not a nice-to-have -- it's the difference between a pipeline that completes with warnings and one that crashes.

---

## 2026-07-08 -- Tool is a distinct abstraction (Phase 6)

**What happened:** The system had Components (deterministic code) and Agents (LLM-powered reasoning), but no bridge between them. The question was: should a Tool just be "a Component method you can call," or something more?

**The lesson:** A Tool is a distinct abstraction with its own contract: a name, a natural-language description the LLM reads to decide when to call it, typed parameters with descriptions, and internal orchestration of one or more Component calls. Three rules emerged:

1. **Description quality > code quality.** A poorly written Tool description causes the LLM to call the wrong Tool or skip a needed call. Unlike a Python docstring, a Tool description is a runtime interface -- it directly impacts system behavior.
2. **Orchestration Tools reduce LLM round-trips.** When four DataProvider calls always happen together (e.g., market regime assessment), wrap them in one Tool. The LLM makes one call, the Tool does the orchestration internally. Fewer round-trips = lower latency and cost.
3. **Tool authorization is a security boundary.** Each Agent receives only the Tools it needs via ToolRegistry at schema-export time. The Market Agent physically cannot call `fetch_news` because it's not in its tool list. This enforces architectural boundaries at the infrastructure level, not just in documentation.

**Rule:** Never expose a Component method directly to an LLM. Always wrap it in a Tool. If the LLM needs to call it, it gets a description.

---

## 2026-07-08 -- "Not an Agent" is an architectural decision (Phase 6)

**What happened:** ChatGPT's original design had a "Technical Agent" for RSI, MACD, and moving averages. We demoted it to 6 Analysis Tools.

**The lesson:** RSI = 100 - (100 / (1 + avg_gain / avg_loss)). That's pure math. Adding an LLM call adds latency, cost, and a failure mode for zero value. The temptation to make everything an Agent -- because "Agent" sounds cooler -- is real and must be resisted.

**Rule:** If the function is deterministic math with no judgment call, it's a Tool, not an Agent. The LLM decides _when_ to call it; the Tool executes _how_. Never promote a deterministic function to an Agent just because the word sounds good.

---

## 2026-07-08 -- Two-layer LLM output validation (Phase 7)

**What happened:** While designing prompt standards, we discussed how to ensure agents produce valid structured output.

**The lesson:** A single approach is insufficient. Prompt-level format constraints ("You must respond with valid JSON matching this schema") reduce the probability of malformed output. Code-level validation (Pydantic models that parse and reject) makes it impossible to proceed with bad output. Neither layer alone is sufficient:

- Prompt-only: the LLM will occasionally produce malformed JSON, and the system silently corrupts.
- Validator-only: you'll burn tokens on retries because you gave the LLM no guidance on what shape you want.

**Rule:** Every agent output schema gets both: a prompt-level format spec AND a Pydantic validator. This applies to all Phase 8+ agents.

---

## 2026-07-08 -- Three documents, three time perspectives (Phase 7)

**What happened:** We realized the project had documents for the future (ROADMAP.md) and present (STATE-OF-THE-PROJECT.md) but nothing for the past -- the accumulated wisdom from building.

**The lesson:** A project that spans 16 phases needs three living documents, each answering a different question:

| Document | Axis | Question |
|---|---|---|
| ROADMAP.md | Future | "Where are we going?" |
| STATE-OF-THE-PROJECT.md | Present | "Where are we right now?" |
| LEARNINGS.md | Past | "What have we learned?" |

Together they form persistent memory. When you come back after a month, reading all three catches you up -- not just on what and where, but on _why_ choices were made and what broke along the way.

**Rule:** After every phase, update all three. A stale LEARNINGS is worse than no LEARNINGS -- it teaches old lessons as if they're still true.