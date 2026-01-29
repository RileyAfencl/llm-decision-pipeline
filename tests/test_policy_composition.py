from __future__ import annotations

from dataclasses import dataclass

from pipeline.policy import CompositePolicy, ExecutionDecision, StepContext
from pipeline.steps.base import PipelineStep
from tests.test_invariants_and_orchestrator import DummyStep


@dataclass(frozen=True)
class AlwaysTruePolicy:
    def decide(self, step: PipelineStep, data: dict, ctx: StepContext) -> ExecutionDecision:
        data["trace"].append("true")
        return ExecutionDecision(run=True, reason="test: true", policy=self.__class__.__name__)

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        return self.decide(step, data, ctx).run

@dataclass(frozen=True)
class AlwaysFalsePolicy:
    def decide(self, step: PipelineStep, data: dict, ctx: StepContext) -> ExecutionDecision:
        data["trace"].append("false")
        return ExecutionDecision(run=False, reason="test: false", policy=self.__class__.__name__)

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        return self.decide(step, data, ctx).run


@dataclass(frozen=True)
class ShouldNotRunPolicy:
    def decide(self, step: PipelineStep, data: dict, ctx: StepContext) -> ExecutionDecision:
        data["trace"].append("should_not_run")
        return ExecutionDecision(run=True, reason="test: should_not_run", policy=self.__class__.__name__)

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        return self.decide(step, data, ctx).run


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
