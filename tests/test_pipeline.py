"""Tests for Pipeline DAG executor."""

import asyncio
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.mark.asyncio
async def test_independent_steps_run_in_parallel():
    """3 independent steps should run in parallel -- total time < sum."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()

    async def step_a():
        await asyncio.sleep(0.1)
        return {"name": "a"}

    async def step_b():
        await asyncio.sleep(0.1)
        return {"name": "b"}

    async def step_c():
        await asyncio.sleep(0.1)
        return {"name": "c"}

    pipeline.add_step("a", step_a, severity=StepSeverity.WARNING)
    pipeline.add_step("b", step_b, severity=StepSeverity.WARNING)
    pipeline.add_step("c", step_c, severity=StepSeverity.WARNING)

    result = await pipeline.run()

    assert result.status == "complete"
    assert result.total_duration_ms < 300  # parallel: ~100ms, not 300ms


@pytest.mark.asyncio
async def test_chain_runs_sequentially():
    """A -> B -> C should run sequentially."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()
    order = []

    async def step_a():
        order.append("a")
        return {}

    async def step_b():
        order.append("b")
        return {}

    async def step_c():
        order.append("c")
        return {}

    pipeline.add_step("a", step_a, severity=StepSeverity.WARNING)
    pipeline.add_step("b", step_b, depends_on=["a"], severity=StepSeverity.WARNING)
    pipeline.add_step("c", step_c, depends_on=["b"], severity=StepSeverity.WARNING)

    result = await pipeline.run()

    assert result.status == "complete"
    assert order == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_critical_step_failure_aborts():
    """Critical failure should abort pipeline, remaining steps skipped."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()

    async def step_ok():
        return {"ok": True}

    async def step_fail():
        raise RuntimeError("broken")

    async def step_never():
        pytest.fail("Should not be reached")

    pipeline.add_step("first", step_ok, severity=StepSeverity.WARNING)
    pipeline.add_step("critical", step_fail, depends_on=["first"], severity=StepSeverity.CRITICAL)
    pipeline.add_step("never", step_never, depends_on=["critical"], severity=StepSeverity.WARNING)

    result = await pipeline.run()

    assert result.status == "aborted"
    assert result.steps["first"].status == "ok"
    assert result.steps["critical"].status == "failed"
    assert "never" not in result.steps  # skipped


@pytest.mark.asyncio
async def test_warning_step_failure_continues_degraded():
    """Warning failure should continue pipeline with degraded status."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()

    async def step_fail():
        raise RuntimeError("minor issue")

    async def step_ok():
        return {"ok": True}

    pipeline.add_step("warn_step", step_fail, severity=StepSeverity.WARNING)
    pipeline.add_step("next", step_ok, depends_on=["warn_step"], severity=StepSeverity.WARNING)

    result = await pipeline.run()

    assert result.status == "degraded"
    assert result.steps["warn_step"].status == "failed"
    assert result.steps["next"].status == "ok"
    assert len(result.degraded_steps) == 1


@pytest.mark.asyncio
async def test_retry_succeeds():
    """Step that fails once then succeeds should be marked ok after retry."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()
    calls = []

    async def flaky():
        calls.append(1)
        if len(calls) < 2:
            raise RuntimeError("first fail")
        return {"recovered": True}

    pipeline.add_step("flaky", flaky, severity=StepSeverity.CRITICAL)

    result = await pipeline.run()

    assert result.status == "complete"
    assert result.steps["flaky"].status == "ok"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_retry_fails_both_times_critical():
    """Critical step failing twice should abort."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()

    async def always_fail():
        raise RuntimeError("persistent failure")

    pipeline.add_step("doomed", always_fail, severity=StepSeverity.CRITICAL)

    result = await pipeline.run()

    assert result.status == "aborted"
    assert result.steps["doomed"].status == "failed"
    assert len(result.failed_steps) == 1


@pytest.mark.asyncio
async def test_retry_fails_both_times_warning():
    """Warning step failing twice should continue degraded."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()

    async def always_fail():
        raise RuntimeError("persistent but minor")

    async def next_step():
        return {"still_runs": True}

    pipeline.add_step("warn", always_fail, severity=StepSeverity.WARNING)
    pipeline.add_step("next", next_step, depends_on=["warn"], severity=StepSeverity.WARNING)

    result = await pipeline.run()

    assert result.status == "degraded"
    assert result.steps["warn"].status == "failed"
    assert result.steps["next"].status == "ok"


@pytest.mark.asyncio
async def test_timeout_kills_step():
    """Step exceeding timeout should be killed and marked failed."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()

    async def slow():
        await asyncio.sleep(0.3)
        return {}

    pipeline.add_step("slow", slow, severity=StepSeverity.WARNING, timeout_seconds=0.1)

    result = await pipeline.run()

    assert result.steps["slow"].status == "failed"


def test_cycle_detection():
    """A depends on B, B depends on A should raise ValueError."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()

    async def noop():
        return {}

    pipeline.add_step("a", noop, depends_on=["b"], severity=StepSeverity.WARNING)
    pipeline.add_step("b", noop, depends_on=["a"], severity=StepSeverity.WARNING)

    with pytest.raises(ValueError):
        pipeline.validate()


def test_missing_dependency():
    """validate() should catch references to nonexistent steps."""
    from pipeline.pipeline import Pipeline, StepSeverity

    pipeline = Pipeline()

    async def noop():
        return {}

    pipeline.add_step("a", noop, depends_on=["nonexistent"], severity=StepSeverity.WARNING)

    with pytest.raises(ValueError):
        pipeline.validate()


def test_pipeline_result_structure():
    """PipelineResult should have all required fields."""
    from pipeline.pipeline import PipelineResult

    pr = PipelineResult(
        status="complete",
        steps={},
        degraded_steps=[],
        failed_steps=[],
        total_duration_ms=100,
    )
    assert pr.status == "complete"
    assert pr.degraded_steps == []
    assert pr.failed_steps == []



