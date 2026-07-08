"""Pipeline -- lightweight DAG executor for the daily morning analysis.

This is a Component, not an Agent. No LLM, no reasoning, no business logic.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable


class StepSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"


@dataclass
class StepResult:
    step_name: str
    status: str
    data: dict | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_ms: int = 0


@dataclass
class PipelineResult:
    status: str
    steps: dict[str, StepResult] = field(default_factory=dict)
    degraded_steps: list[str] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)
    total_duration_ms: int = 0


@dataclass
class _Step:
    name: str
    func: Callable[..., Awaitable[dict]]
    depends_on: list[str]
    severity: StepSeverity
    timeout_seconds: int = 30
    retry_delay_seconds: int = 5


class Pipeline:
    def __init__(self):
        self._steps: dict[str, _Step] = {}

    def add_step(
        self,
        name: str,
        func: Callable,
        depends_on: list[str] | None = None,
        severity: StepSeverity = StepSeverity.WARNING,
        timeout_seconds: int = 30,
    ) -> None:
        if depends_on is None:
            depends_on = []
        if name in self._steps:
            raise ValueError(f"Step '{name}' already exists")
        self._steps[name] = _Step(
            name=name,
            func=func,
            depends_on=depends_on,
            severity=severity,
            timeout_seconds=timeout_seconds,
        )

    def validate(self) -> None:
        for name, step in self._steps.items():
            for dep in step.depends_on:
                if dep not in self._steps:
                    raise ValueError(f"Step '{name}' depends on '{dep}', which does not exist")
        self._check_cycles()

    def _check_cycles(self) -> None:
        visited: set[str] = set()
        path: set[str] = set()

        def dfs(node: str):
            if node in path:
                raise ValueError(f"Cycle detected involving step '{node}'")
            if node in visited:
                return
            path.add(node)
            for dep in self._steps[node].depends_on:
                dfs(dep)
            path.discard(node)
            visited.add(node)

        for name in self._steps:
            dfs(name)

    async def run(self) -> PipelineResult:
        self.validate()
        start_time = time.monotonic()
        results: dict[str, StepResult] = {}
        aborted = False

        dependents: dict[str, list[str]] = {name: [] for name in self._steps}
        pending_deps: dict[str, set[str]] = {name: set(step.depends_on) for name, step in self._steps.items()}

        for name, step in self._steps.items():
            for dep in step.depends_on:
                dependents[dep].append(name)

        ready = asyncio.Queue()
        for name, deps in pending_deps.items():
            if not deps:
                ready.put_nowait(name)

        running_tasks: dict[str, asyncio.Task] = {}

        while not ready.empty() or running_tasks:
            while not ready.empty():
                if aborted:
                    try:
                        ready.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                    continue
                try:
                    name = ready.get_nowait()
                except asyncio.QueueEmpty:
                    break
                if name in running_tasks:
                    continue
                running_tasks[name] = asyncio.create_task(self._run_step(self._steps[name]))

            if not running_tasks:
                break

            done, _ = await asyncio.wait(
                running_tasks.values(),
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                name = None
                for n, t in list(running_tasks.items()):
                    if t is task:
                        name = n
                        break
                if name is None:
                    continue

                del running_tasks[name]
                step_result = task.result()
                results[name] = step_result

                if step_result.status == "failed":
                    step = self._steps[name]
                    if step.severity == StepSeverity.CRITICAL:
                        aborted = True
                        for t in running_tasks.values():
                            t.cancel()

                for dep_name in dependents.get(name, []):
                    if dep_name in pending_deps:
                        pending_deps[dep_name].discard(name)
                        if not pending_deps[dep_name] and not aborted:
                            ready.put_nowait(dep_name)

        status = "complete"
        degraded = []
        failed = []
        for name, sr in results.items():
            if sr.status == "failed":
                step_sev = self._steps[name].severity
                if step_sev == StepSeverity.WARNING:
                    degraded.append(name)
                else:
                    failed.append(name)
            elif sr.status == "degraded":
                degraded.append(name)

        if aborted or (failed and not degraded):
            status = "aborted"
        elif degraded:
            status = "degraded"

        total_ms = int((time.monotonic() - start_time) * 1000)

        return PipelineResult(
            status=status,
            steps=results,
            degraded_steps=degraded,
            failed_steps=failed,
            total_duration_ms=total_ms,
        )

    async def _run_step(self, step: _Step) -> StepResult:
        t0 = time.monotonic()
        try:
            data = await asyncio.wait_for(self._run_with_retry(step), timeout=step.timeout_seconds)
            duration_ms = int((time.monotonic() - t0) * 1000)
            return StepResult(step_name=step.name, status="ok", data=data, duration_ms=duration_ms)
        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - t0) * 1000)
            return StepResult(
                step_name=step.name,
                status="failed",
                errors=[f"Timed out after {step.timeout_seconds}s"],
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - t0) * 1000)
            return StepResult(
                step_name=step.name,
                status="failed",
                errors=[str(e)],
                duration_ms=duration_ms,
            )

    async def _run_with_retry(self, step: _Step) -> dict:
        try:
            return await step.func()
        except Exception:
            await asyncio.sleep(step.retry_delay_seconds)
            return await step.func()
