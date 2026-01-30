from __future__ import annotations

from dataclasses import dataclass

from pipeline.failure_policy import FailureDecision, FailureMode
from pipeline.policy import DefaultPolicy, StepContext, BlockIfFlaggedPolicy
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
class ContinueWithFlagPolicy:
    def on_step_failure(
        self,
        step: PipelineStep,
        data: dict,
        ctx: StepContext,
        exc: Exception,
    ) -> FailureDecision:
        return FailureDecision(mode=FailureMode.CONTINUE_WITH_FLAG, reason="flag it")


def test_run_summary_degraded_and_step_accounting() -> None:
    from pipeline.orchestrator import run_pipeline  # adjust if module path differs

    policy = [
        DefaultPolicy(),
        BlockIfFlaggedPolicy(
            flagged_steps=frozenset({"boom"}),
            blocked_steps=frozenset({"after"}),
        ),
    ]

    out = run_pipeline(
        steps=[BoomStep(), AfterStep()],
        initial_data={},
        policy=policy,
        failure_policy=ContinueWithFlagPolicy(),
    )

    summary = out["run_summary"]
    assert summary["status"] == "degraded"
    assert summary["attempted_steps"] == ["boom#1"]          # boom attempted (timing may be 0.0 if failed fast; see note below)
    assert summary["skipped_steps"] == ["after#1"]
    assert len(summary["failures"]) == 1
    assert summary["failures"][0]["step"] == "boom"
    assert "boom" in summary["failure_flags"]
