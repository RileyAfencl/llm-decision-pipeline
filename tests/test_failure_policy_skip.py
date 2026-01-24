from __future__ import annotations

from dataclasses import dataclass

from pipeline.failure_policy import FailureDecision, FailureMode
from pipeline.policy import StepContext
from pipeline.steps.base import PipelineStep


@dataclass(frozen=True)
class BoomStep(PipelineStep):
    name: str = "boom"
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    deletes: tuple[str, ...] = ()

    def run(self, input_data: dict) -> dict:
        raise ValueError("kaboom")


@dataclass(frozen=True)
class AfterStep(PipelineStep):
    name: str = "after"
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ("after_ran",)
    deletes: tuple[str, ...] = ()

    def run(self, input_data: dict) -> dict:
        return {"after_ran": True}


@dataclass(frozen=True)
class SkipFailurePolicy:
    def on_step_failure(
        self,
        step: PipelineStep,
        data: dict,
        ctx: StepContext,
        exc: Exception,
    ) -> FailureDecision:
        return FailureDecision(mode=FailureMode.SKIP, reason="skip it")


def test_failure_policy_skip_continues_pipeline_and_records_failure() -> None:
    from pipeline.orchestrator import run_pipeline  # adjust if your module path differs

    out = run_pipeline(
        steps=[BoomStep(), AfterStep()],
        initial_data={},
        failure_policy=SkipFailurePolicy(),
    )

    assert out.get("action") != "error"
    assert out["after_ran"] is True

    assert "failures" in out
    assert len(out["failures"]) == 1
    f = out["failures"][0]
    assert f["step"] == "boom"
    assert f["failure_mode"] == "skip"
    assert f["failure_reason"] == "skip it"
