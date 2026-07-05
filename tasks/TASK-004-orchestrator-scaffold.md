# TASK-004: Orchestrator Scaffold (Pipeline)

## Context
This task implements the Pipeline Component that orchestrates the daily morning analysis. It belongs to Phase 4 (System Architecture). This is the third Codex implementation task, following TASK-001 (Project Bootstrap) and TASK-003 (Memory Layer).

**Required reading (in order):**
1. `docs/architecture/06-orchestrator-design.md` ¡ª Pipeline design, severity model, scheduling
2. `components/pipeline.md` ¡ª Pipeline Component spec with full public interface
3. `adr/ADR-004-dag-orchestrator.md` ¡ª Why DAG, why not LangGraph
4. `docs/architecture/04-decision-flow.md` ¡ª The 7-step flow the Pipeline executes
5. `PROJECT_RULES.md` ¡ª Section 4 (Component Template)

## Objective
Implement the `Pipeline` class exactly as specified in `components/pipeline.md`. Create a working `src/main.py` entry point that wires the Pipeline with mock Agent stubs and validates the DAG executes correctly on `--run-morning-report`. **No real Agent implementation, no real LLM calls, no real data fetching.**

## Requirements

### Pipeline Class
- [ ] Create `src/pipeline/` package with `__init__.py`
- [ ] Implement `src/pipeline/pipeline.py` with the `Pipeline` class
- [ ] Implement `Step`, `StepResult`, `PipelineResult`, `StepSeverity` dataclasses/enums
- [ ] `add_step()` validates unique step names
- [ ] `add_step()` rejects cycles (step A depends on B which depends on A)
- [ ] `validate()` checks all `depends_on` references exist as step names
- [ ] `validate()` raises `ValueError` with a clear message on invalid graph
- [ ] `run()` executes steps with no dependencies in parallel via `asyncio.gather`
- [ ] `run()` executes dependent steps only after their upstream steps complete
- [ ] `run()` enforces per-step timeout via `asyncio.wait_for`
- [ ] `run()` retries failed steps once (3-5 second delay before retry)
- [ ] `run()` aborts on Critical step failure (remaining steps skipped)
- [ ] `run()` continues on Warning step failure (step marked degraded)
- [ ] `run()` captures step duration in milliseconds
- [ ] `run()` returns `PipelineResult` with status and all step results

### Entry Point
- [ ] Update `src/main.py` from TASK-001 to support `--run-morning-report` flag
- [ ] `main.py` loads Config, initializes MemoryRepository
- [ ] `main.py` creates mock Agent stubs (dummy async functions that return placeholder data)
- [ ] `main.py` wires 7 steps into the Pipeline with correct dependencies and severities
- [ ] `main.py` calls `pipeline.run()` and prints the result status + duration

### Mock Agent Stubs
For V1, create placeholder Agent stubs that return hardcoded but realistic data:

- [ ] `src/agents/__init__.py` ¡ª package init
- [ ] `src/agents/market_agent.py` ¡ª returns mock Market Context dict
- [ ] `src/agents/research_agent.py` ¡ª returns mock Events dict
- [ ] `src/agents/watchlist_agent.py` ¡ª returns mock Watchlist Status dict
- [ ] `src/agents/advisor_agent.py` ¡ª returns mock Morning Report dict
- [ ] Each mock Agent has an `async def run(**kwargs)` method that returns a dict
- [ ] Build Candidate List and Score Candidates are implemented as plain async functions in `src/pipeline/steps.py`

### Configuration
- [ ] Add `PIPELINE_STEP_TIMEOUT_SECONDS=30` to `.env.example` and `Config`
- [ ] Add `PIPELINE_RETRY_DELAY_SECONDS=5` to `.env.example` and `Config`

### Logging
- [ ] Pipeline logs each step result as structured JSON (step name, status, duration_ms, errors)
- [ ] Log the final PipelineResult status and total duration

## Acceptance Criteria

1. `python src/main.py --run-morning-report` completes without errors, prints pipeline status and duration
2. Steps 1-3 (Market, Research, Watchlist) run in parallel (verify: step durations are concurrent, not sequential ¡ª total time ¡Ö max of the three, not sum)
3. A Critical step failure aborts the pipeline (remaining steps skipped, status = "aborted")
4. A Warning step failure allows the pipeline to continue (status = "degraded")
5. `validate()` raises `ValueError` when given a cycle (A depends on B, B depends on A)
6. `validate()` raises `ValueError` when a dependency references a nonexistent step
7. A step exceeding its timeout is killed and marked as failed
8. `pytest tests/test_pipeline.py` ¡ª all pipeline tests pass

### Test Scenarios
- [ ] Test DAG with 3 independent steps ¡ú all run in parallel (verify total time < sum of step times)
- [ ] Test DAG with chain A ¡ú B ¡ú C ¡ú steps run sequentially
- [ ] Test DAG with mix: parallel start, sequential finish
- [ ] Test Critical step failure ¡ú pipeline aborts, remaining skipped
- [ ] Test Warning step failure ¡ú pipeline continues, status = "degraded"
- [ ] Test retry: step fails first time, succeeds on retry ¡ú status = "ok"
- [ ] Test retry: step fails both times on Critical ¡ú abort
- [ ] Test retry: step fails both times on Warning ¡ú continue degraded
- [ ] Test timeout: step exceeds `timeout_seconds` ¡ú killed, marked failed
- [ ] Test cycle detection: A ¡ú B ¡ú A ¡ú `ValueError` raised
- [ ] Test missing dependency: validate() catches it
- [ ] Test PipelineResult structure: all fields populated correctly

## Out of Scope

- Real Agent implementation (LLM calls, tool usage) ¡ª Phase 8+
- Real data fetching (AkShare, news APIs) ¡ª Phase 5
- LangGraph or any workflow framework
- Pipeline persistence (save/resume from checkpoint)
- Scheduling infrastructure (cron, Task Scheduler setup)
- Trading day detection
- Report formatting (the Advisor mock returns raw data, not formatted markdown)
- Error report generation for the user

## References
- `docs/architecture/06-orchestrator-design.md` ¡ª Full orchestrator design
- `components/pipeline.md` ¡ª Pipeline public interface and constraints
- `adr/ADR-004-dag-orchestrator.md` ¡ª Why DAG, not LangGraph
- `PROJECT_RULES.md` ¡ª Section 4 (Component Template) and Section 6 (TASK Standard)
