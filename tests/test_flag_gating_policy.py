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


def test_flag_blocks_downstream_step_via_policy() -> None:
    from pipeline.orchestrator import run_pipeline  # adjust if your module path differs

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

    assert out.get("action") != "error"

    # failure flag created by CONTINUE_WITH_FLAG
    assert "failure_flags" in out
    assert "boom" in out["failure_flags"]

    # AfterStep should have been vetoed by policy
    assert "after_ran" not in out
    assert out["timings"]["after"] == 0.0

    # failure event recorded
    assert "failures" in out
    assert len(out["failures"]) == 1
    assert out["failures"][0]["step"] == "boom"
