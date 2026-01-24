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
class ObserveFlagsStep(PipelineStep):
    name: str = "observe_flags"
    reads: tuple[str, ...] = ("failure_flags",)
    writes: tuple[str, ...] = ("saw_boom_flag",)
    deletes: tuple[str, ...] = ()

    def run(self, input_data: dict) -> dict:
        flags = input_data.get("failure_flags", {})
        return {"saw_boom_flag": "boom" in flags}


@dataclass(frozen=True)
class ContinueWithFlagPolicy:
    def on_step_failure(
        self,
        step: PipelineStep,
        data: dict,
        ctx: StepContext,
        exc: Exception,
    ) -> FailureDecision:
        return FailureDecision(mode=FailureMode.CONTINUE_WITH_FLAG, reason="flag it")


def test_continue_with_flag_persists_flag_and_pipeline_continues() -> None:
    from pipeline.orchestrator import run_pipeline  # adjust if your module path differs

    out = run_pipeline(
        steps=[BoomStep(), ObserveFlagsStep()],
        initial_data={"failure_flags": {}},  # ensure preflight has the key for ObserveFlagsStep.reads
        failure_policy=ContinueWithFlagPolicy(),
    )

    assert out.get("action") != "error"
    assert out["saw_boom_flag"] is True

    assert "failures" in out
    assert len(out["failures"]) == 1
    assert out["failures"][0]["step"] == "boom"
    assert out["failures"][0]["failure_mode"] == "continue_with_flag"

    assert "failure_flags" in out
    assert "boom" in out["failure_flags"]
    assert out["failure_flags"]["boom"]["reason"] == "flag it"
