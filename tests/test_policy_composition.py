from __future__ import annotations

from dataclasses import dataclass

from pipeline.policy import CompositePolicy, StepContext
from pipeline.steps.base import PipelineStep
from tests.test_invariants_and_orchestrator import DummyStep


@dataclass(frozen=True)
class AlwaysTruePolicy:
    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        data["trace"].append("true")
        return True


@dataclass(frozen=True)
class AlwaysFalsePolicy:
    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        data["trace"].append("false")
        return False


@dataclass(frozen=True)
class ShouldNotRunPolicy:
    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        data["trace"].append("should_not_run")
        return True


def test_composite_policy_short_circuits_on_first_false() -> None:
    data = {"trace": []}
    ctx = StepContext(step_index=0, occurrence=1)
    step = DummyStep()

    policy = CompositePolicy(
        policies=[AlwaysTruePolicy(), AlwaysFalsePolicy(), ShouldNotRunPolicy()]
    )

    allowed = policy.should_run(step, data, ctx)
    assert allowed is False
    assert data["trace"] == ["true", "false"]
