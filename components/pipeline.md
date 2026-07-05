# Pipeline

## Name
Pipeline

## Purpose
A lightweight Directed Acyclic Graph (DAG) executor that runs the daily morning analysis pipeline. It manages step dependencies, parallel execution, error handling, and produces the morning report.

## Responsibilities

- Accept a set of named steps, each with a function and optional dependency list
- Build a dependency graph and validate it is acyclic (reject cycles on construction)
- Execute steps with no dependencies in parallel (via `asyncio.gather`)
- Execute dependent steps only after their upstream steps complete
- Enforce per-step severity: Critical step failure ¡ú abort pipeline; Warning step failure ¡ú continue with degradation flag
- Retry failed steps once (3-5 second delay) before applying severity rules
- Collect results from all steps into a `PipelineResult`
- Log every step's status, duration, and errors as structured JSON
- Time out stalled steps (default: 30 seconds per step)

This component does NOT:
- Know about Agents specifically ¡ª it operates on generic async functions
- Contain business logic (it does not know what Step 1 vs Step 7 means)
- Schedule itself (triggered externally: CLI command or OS scheduler)
- Format the final report (that is the Advisor Agent's job)

## Why a DAG, Not a Script

A simple sequential script would work for 4 Agents and 7 steps. But as we add phases (Phase 8: Market Agent implementation with real data, Phase 9: Research Agent with news analysis, Phase 10: Advisor with multi-source synthesis), the pipeline will grow more steps and more parallel opportunities.

A DAG-based Pipeline:
- Makes dependencies explicit: you can see at a glance that "Score Candidates" needs Market, Candidate List, and Watchlist
- Enables parallelism automatically: steps with no dependencies run simultaneously
- Is testable: mock each step function independently, verify the graph executes correctly
- Survives growth: adding a new Agent in Phase 8 means adding one step + one dependency declaration

## Public Interface

```python
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Any
import asyncio

@dataclass
class StepResult:
    """Result from a single pipeline step."""
    step_name: str
    status: str          # "ok" | "degraded" | "failed"
    data: dict | None    # Step output data
    errors: list[str]    # Error messages
    warnings: list[str]  # Non-fatal warnings
    duration_ms: int     # Execution time

@dataclass
class PipelineResult:
    """Result from the entire pipeline run."""
    status: str                          # "complete" | "degraded" | "aborted"
    steps: dict[str, StepResult]         # Results keyed by step name
    degraded_steps: list[str]            # Step names that ran degraded
    failed_steps: list[str]              # Step names that failed
    total_duration_ms: int               # Wall clock time

class StepSeverity(Enum):
    CRITICAL = "critical"   # Pipeline aborts on failure
    WARNING = "warning"     # Pipeline continues degraded on failure

@dataclass
class Step:
    name: str
    func: Callable[..., Awaitable[dict]]
    depends_on: list[str]        # Step names this step waits for
    severity: StepSeverity
    timeout_seconds: int = 30
    retry_delay_seconds: int = 5


class Pipeline:
    def __init__(self):
        """Create an empty pipeline."""

    def add_step(self, name: str, func: Callable,
                 depends_on: list[str] | None = None,
                 severity: StepSeverity = StepSeverity.WARNING,
                 timeout_seconds: int = 30) -> None:
        """Add a step to the pipeline.
        
        Args:
            name: Unique step identifier
            func: Async callable that returns a dict of step output
            depends_on: Step names this step waits for. None or empty = run at start.
            severity: CRITICAL or WARNING
            timeout_seconds: Max execution time before step is killed
        
        Raises:
            ValueError: If name is not unique or depends_on creates a cycle.
        """

    def validate(self) -> None:
        """Check the graph is valid: no cycles, all dependencies exist.
        Raises ValueError if invalid."""

    async def run(self) -> PipelineResult:
        """Execute the pipeline.
        
        Steps with no dependencies run first, in parallel.
        Each subsequent step runs when its dependencies complete.
        On Critical failure: pipeline stops, remaining steps skipped.
        On Warning failure: pipeline continues, step marked degraded.
        
        Returns PipelineResult with status and all step results.
        """
```

### Usage Example

```python
pipeline = Pipeline()

pipeline.add_step("market", market_agent.run, severity=CRITICAL)
pipeline.add_step("research_market", research_agent.run_market_wide, severity=WARNING)
pipeline.add_step("watchlist", watchlist_agent.run, severity=WARNING)

# Runs after market, research_market, AND watchlist complete
pipeline.add_step("build_candidates", build_candidates,
                  depends_on=["market", "research_market", "watchlist"],
                  severity=CRITICAL)

# Runs after build_candidates
pipeline.add_step("research_stocks", research_agent.run_for_stocks,
                  depends_on=["build_candidates"],
                  severity=WARNING)

# Runs after build_candidates, market, AND watchlist
pipeline.add_step("score", score_candidates,
                  depends_on=["build_candidates", "market", "watchlist"],
                  severity=CRITICAL)

# Runs after score
pipeline.add_step("advisor", advisor_agent.run,
                  depends_on=["score"],
                  severity=CRITICAL)

result = await pipeline.run()
print(f"Pipeline {result.status} in {result.total_duration_ms}ms")
```

## Dependencies

- **Python standard library**: `asyncio`, `dataclasses`, `enum`, `logging`
- **No external dependencies** ¡ª the Pipeline is pure Python
- **No LLM access** ¡ª Pipeline is a Component, not an Agent

## Consumers

| Consumer | How It Uses Pipeline |
|---|---|
| `src/main.py` | Creates and runs the Pipeline when triggered (CLI or cron) |
| Tests | Creates Pipeline with mock step functions to verify DAG execution, error handling, and parallelism |

## Constraints

- **No LLM.** Pipeline is a Component ¡ª deterministic execution, no reasoning
- **No business logic.** Pipeline runs steps; it does not know what each step does
- **Must reject cycles.** A step that depends on itself (directly or transitively) must raise `ValueError` on `add_step`
- **Must handle missing dependencies.** If `depends_on` references a step name not yet added, `validate()` must catch it
- **Timeout enforcement.** A step that runs longer than `timeout_seconds` is killed and treated as failed
- **Thread safety.** Pipeline is single-threaded for V1. The internal DAG traversal does not need locking
- **Immutable after validation.** Once `validate()` passes, the step graph does not change during `run()`

## Failure Handling

| Scenario | Behavior |
|---|---|
| Step raises an exception | Caught, wrapped in StepResult with status="failed" |
| Step exceeds timeout | `asyncio.wait_for` cancels the task. Status="failed" |
| Critical step fails | Remaining steps are skipped. Pipeline status = "aborted" |
| Warning step fails | Step marked degraded. Pipeline continues. Status = "degraded" if any step degraded |
| Retry succeeds | Step runs twice total (original + 1 retry). If retry succeeds, status = "ok" |
| Retry also fails | After one retry, severity rules apply (abort or degrade) |
| All steps succeed | Pipeline status = "complete" |

## Future Evolution

- **V2: Cancellation propagation.** When a Critical step fails, cancel in-flight parallel steps gracefully (currently they run to completion or timeout)
- **V2: Pipeline history.** Store PipelineResult in Decision Memory for trend analysis (pipeline duration over time, step failure frequency)
- **V2: Dynamic step injection.** Allow Agents to add steps mid-pipeline (e.g., "this stock requires deeper analysis ¡ú add a dedicated research sub-step")
- **Phase 12: LangGraph migration.** Replace Pipeline with LangGraph StateGraph when we adopt the framework. The interface should be similar enough that Agent code changes minimally
