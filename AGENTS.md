# AGENTS.md ¡ª Project Workflow Instructions

## Phase Validation Checklist

Before generating any documents in a new phase, run this checklist. If any answer is "No," fix it first.

- [ ] Does every new Agent use the standard Agent template?
- [ ] Are Components separated from Agents?
- [ ] Does every document answer one specific question?
- [ ] Does this phase stay within scope?
- [ ] Can Codex implement this without guessing?

This checklist was established after Phase 3 placed `MemoryRepository` in `agents/` instead of `components/`. It exists to prevent that class of error from recurring.

---

## How We Work

1. Codex is the active collaborator on this project, not ChatGPT. Do not assume any ChatGPT output is authoritative.
2. The user will specify which phase is active. Do not assume.
3. Every phase follows: concept discussion ¡ú architecture decisions ¡ú document generation ¡ú Codex Sprint ¡ú review.

## Always-Update Rule

Whenever the project status changes or the roadmap advances, update these two files immediately:

- `docs/STATE-OF-THE-PROJECT.md` ¡ª update the "Current Task" line and any relevant context
- `ROADMAP.md` ¡ª update phase statuses and fix any stale file references

These are my persistent memory. If they go stale, I lose context between sessions. Treat them as live documents.

## Document Standards

All documents follow the templates defined in `PROJECT_RULES.md`:

- Agent specs use the Agent Template (Identity, Purpose, Goal, Inputs, Outputs, Memory, Tools, Workflow, Constraints, Consumers, Failure Handling, Future Evolution)
- Component specs use the Component Template (Name, Purpose, Responsibilities, Public Interface, Dependencies, Consumers, Constraints, Future Evolution)
- ADRs follow the ADR standard (Status, Context, Decision, Consequences, Alternatives Considered)
- TASK files must be specific enough for Codex to implement without guessing

## Key Distinction

Agents think and decide (they use LLMs). Components execute and store (deterministic, no LLM). Never confuse them. Never put a Component in `agents/`.

## Backlog Folder

The `backlog/` directory contains original ChatGPT-generated files from Phase 3. These are archival only. Do not treat them as current specifications. The definitive documents live in `docs/`, `adr/`, `components/`, and `tasks/`.


