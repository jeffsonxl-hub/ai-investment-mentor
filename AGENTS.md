# AGENTS.md \u2014 Project Workflow Instructions

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
3. Every phase follows: concept discussion \u2192 architecture decisions \u2192 document generation \u2192 Codex Sprint \u2192 review.
4. After document generation in each phase, run the `plan-eng-review` skill on all newly generated documents before proceeding to the Codex Sprint. This catches architecture issues, missing edge cases, and spec gaps before implementation begins.

---

## Pre-Delivery Smoke Test (MANDATORY)

Before declaring any phase complete, run this end-to-end sequence in a clean state:

```powershell
# 1. Start from a clean virtual environment
python -m venv .venv --clear
.\.venv\Scripts\Activate.ps1

# 2. Install all dependencies fresh
pip install -r requirements.txt

# 3. Clear any stale .pyc cache
Get-ChildItem -Path src -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# 4. Run the full test suite
python -m pytest tests/ -q

# 5. If integration tests exist, run them too (requires API tokens in .env)
python -m pytest tests/test_integration.py -v
```

If any step fails, fix it before marking the phase complete. The user's environment is the ground truth.

---

## Dependencies Rule (MANDATORY)

Every time a new Python package is imported in any source file, `requirements.txt` must be updated and `pip install -r requirements.txt` must run successfully before the work is considered done. Tests depend on these packages. Never assume a package is already installed in the user's environment.

---

## Pre-Commit Checklist (MANDATORY)

Before committing and pushing any code, run the full test suite:

```bash
pip install -r requirements.txt
pytest
```

All tests must pass. If a dependency was added during development, update `requirements.txt` before running tests.

## Always-Update Rule

Whenever the project status changes or the roadmap advances, update these three files immediately:

- `docs/STATE-OF-THE-PROJECT.md` \u2014 update the "Current Task" line and any relevant context
- `ROADMAP.md` ¡ª update phase statuses and fix any stale file references
- `docs/LEARNINGS.md` ¡ª add new entries when a phase teaches something worth remembering

These are my persistent memory. If they go stale, I lose context between sessions. Treat them as live documents.

## Document Standards

All documents follow the templates defined in `PROJECT_RULES.md`:

- Agent specs use the Agent Template (Identity, Purpose, Goal, Inputs, Outputs, Memory, Tools, Workflow, Constraints, Consumers, Failure Handling, Future Evolution)
- Component specs use the Component Template (Name, Purpose, Responsibilities, Public Interface, Dependencies, Consumers, Constraints, Future Evolution)
- ADRs follow the ADR standard (Status, Context, Decision, Consequences, Alternatives Considered)
- TASK files must be specific enough for Codex to implement without guessing

## Key Distinction

Agents think and decide (they use LLMs). Components execute and store (deterministic, no LLM). Never confuse them. Never put a Component in `agents/`.
