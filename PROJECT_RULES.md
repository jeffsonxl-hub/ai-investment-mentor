# Project Rules ¡ª AI Investment Mentor

This file defines the standards every Agent, Component, and document in this project must follow. No exceptions.

---

## 1. Architecture Rules

1. **Single responsibility per Agent.** Each Agent does one thing and does it well. If an Agent purpose statement needs an "and," it should probably be two Agents.
2. **Advisor Agent never accesses data sources directly.** It only consumes structured output from specialist Agents. This keeps recommendations auditable and the data layer swappable.
3. **All inter-Agent communication uses structured data.** JSON internally. No Agent passes raw text to another Agent expecting it to figure things out.
4. **Every recommendation must include evidence, confidence, and risks.** No opaque predictions. The user always sees why something was recommended.
5. **Prefer deterministic logic before LLM reasoning.** If a rule, threshold, or heuristic can make the decision, use it. Reserve LLM calls for tasks that genuinely require language understanding.

---

## 2. Document Standards

Every document in this project answers exactly one question:

| Document Type | Question It Answers | Location |
|---|---|---|
| Product Vision | Who is this for and what does success look like? | `docs/architecture/` |
| System Design | How do the pieces fit together? | `docs/architecture/` |
| Agent Spec | What does this Agent do? | `agents/` |
| Component Spec | What does this software component do? | `components/` |
| ADR | Why did we make this decision? | `adr/` |
| TASK | What should Codex implement? | `tasks/` |

No mixing responsibilities. A TASK document does not debate architecture. An ADR does not include implementation instructions.

---

## 3. Agent Specification Template

Every Agent file must follow this exact structure. No sections may be omitted.

```
# [Agent Name]

## Identity
[Who this Agent is. Role and persona. One paragraph.]

## Purpose
[Why it exists. One sentence.]

## Goal
[What it tries to achieve. Measurable if possible.]

## Inputs
[What data or events trigger this Agent. List each input with its source.]

## Outputs
[What this Agent produces. Always structured. Define the schema or format.]

## Memory
[What this Agent remembers across invocations. Reference specific memory types: Watchlist, Market, Decision.]

## Tools
[External capabilities this Agent can call. List each tool and what it provides.]

## Workflow
[Step-by-step reasoning process. What does this Agent do from input to output?]

## Constraints
[What this Agent must never do. Hard boundaries.]

## Consumers
[Who depends on this Agent output. Be specific about which Agent or component.]

## Failure Handling
[What happens when a tool fails, an LLM call times out, or input is malformed.]

## Future Evolution
[Planned V2 improvements. What we will add later but are intentionally skipping now.]
```

### Characteristics of an Agent
- Uses an LLM for reasoning
- Makes decisions based on evidence
- Produces structured outputs
- May call Tools
- May read from or write to Memory (via Components, never directly)

---

## 4. Component Specification Template

Every Component file must follow this exact structure. No sections may be omitted.

```
# [Component Name]

## Name
[Component identifier. Used in code and configuration.]

## Purpose
[Why this component exists. One sentence.]

## Responsibilities
[What this component does. Deterministic operations only. No reasoning, no LLM.]

## Public Interface
[Methods, signatures, contracts. What callers can invoke.]

## Dependencies
[What this component needs to function. Libraries, other components, external services.]

## Consumers
[Who calls this component. Agents or other components.]

## Constraints
[What this component must never do. Hard boundaries.]

## Future Evolution
[Planned V2 improvements.]
```

### Characteristics of a Component
- No LLM. No reasoning. No decision-making.
- Deterministic: same input always produces same output.
- Infrastructure or utility code: storage, data fetching, configuration, logging.
- Examples: MemoryRepository, AkShare Client, SQLite Storage, Configuration Loader.

---

## 5. ADR (Architecture Decision Record) Standard

Every ADR answers: "What did we decide, and why?"

```
# ADR-[NNN]: [Title]

## Status
[Proposed / Accepted / Deprecated / Superseded]

## Context
[What problem are we solving? What constraints exist?]

## Decision
[What we decided. One clear statement.]

## Consequences
[What becomes easier? What becomes harder? Trade-offs.]

## Alternatives Considered
[What else we considered and why we rejected it.]
```

ADR numbering: start at 001, increment by 1. Never reuse numbers. If a decision is reversed, mark the old ADR as Superseded and reference the new one.

---

## 6. Task (TASK) Standard

Every TASK is written for Codex to implement without guessing.

```
# TASK-[NNN]: [Title]

## Context
[What Phase does this belong to? What documents should Codex read first?]

## Objective
[What to build. One clear statement.]

## Requirements
[Specific, verifiable requirements. Use checkboxes.]

## Acceptance Criteria
[How we know it is done. Testable statements.]

## Out of Scope
[What Codex must NOT build. Prevent scope creep.]

## References
[Links to relevant ADRs, design docs, and agent/component specs.]
```

If Codex would need to make an assumption to proceed, the TASK is not specific enough.

---

## 7. Directory Structure

```
ai-investment-mentor/
©À©¤©¤ README.md
©À©¤©¤ PROJECT_RULES.md          # This file
©À©¤©¤ ROADMAP.md
©À©¤©¤ AGENTS.md                 # Codex collaboration instructions
©À©¤©¤ .gitignore
©À©¤©¤ docs/
©¦   ©À©¤©¤ STATE-OF-THE-PROJECT.md
©¦   ©À©¤©¤ architecture/
©¦   ©¦   ©À©¤©¤ 01-product-vision.md
©¦   ©¦   ©À©¤©¤ 02-system-overview.md
©¦   ©¦   ©À©¤©¤ 03-agent-design.md
©¦   ©¦   ©¸©¤©¤ 04-decision-flow.md
©¦   ©¸©¤©¤ 05-memory-design.md
©À©¤©¤ agents/                   # Agent specs only
©À©¤©¤ components/               # Component specs only
©À©¤©¤ adr/                      # Architecture Decision Records
©À©¤©¤ tasks/                    # Codex implementation tasks
©À©¤©¤ backlog/                  # Original ChatGPT-generated files (archive)
©À©¤©¤ src/                      # Source code (to be created)
©¸©¤©¤ tests/                    # Tests (to be created)
```
