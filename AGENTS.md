# AGENTS.md �� Project Workflow Instructions

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
3. Every phase follows: concept discussion �� architecture decisions �� document generation �� Codex Sprint �� review.




## Pre-Delivery Smoke Test (MANDATORY)

Before declaring any phase complete, run this end-to-end sequence in a clean state — do not rely on pre-installed packages or cached bytecode:

`powershell
# 1. Start from a clean virtual environment
python -m venv .venv --clear
.\.venv\Scripts\Activate.ps1

# 2. Install all dependencies fresh — this catches missing requirements.txt entries
pip install -r requirements.txt

# 3. Clear any stale .pyc cache that could mask code changes
Get-ChildItem -Path src -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# 4. Run the full test suite — zero failures is the only acceptance bar
python -m pytest tests/ -q

# 5. If integration tests exist, run them too (requires API tokens in .env)
python -m pytest tests/test_integration.py -v
`

If any step fails, fix it before marking the phase complete. The user's environment is the ground truth — never assume your environment matches theirs.



Every time a new Python package is imported in any source file, equirements.txt must be updated and pip install -r requirements.txt must run successfully before the work is considered done. Tests depend on these packages — a passing test suite after pip install -r requirements.txt is the only acceptance criterion. Never assume a package is already installed in the user's environment.

 (MANDATORY)

Before committing and pushing any code, run the full test suite:

```bash
pip install -r requirements.txt
pytest
```

All tests must pass. If a dependency was added during development, update `requirements.txt` before running tests. Never assume the user's environment matches yours.

## Always-Update Rule

Whenever the project status changes or the roadmap advances, update these two files immediately:

- `docs/STATE-OF-THE-PROJECT.md` �� update the "Current Task" line and any relevant context
- `ROADMAP.md` �� update phase statuses and fix any stale file references

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





