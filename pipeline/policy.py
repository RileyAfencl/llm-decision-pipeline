from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from pipeline.steps.base import PipelineStep


@dataclass(frozen=True)
class StepContext:
    step_index: int          # 0-based index in the steps list
    occurrence: int          # 1 for first time this step.name appears, 2 for second, etc.


class Policy(Protocol):
    """Decides whether a step is eligible to run given current pipeline state."""

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool: ...


@dataclass(frozen=True)
class DefaultPolicy:
    """
    Default behavior: defer to step.when(data).
    This preserves current behavior while moving the decision point out of the orchestrator.
    """

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        allowed = step.when(data)
        if not isinstance(allowed, bool):
            raise TypeError(
                f"{step.__class__.__name__}.when() must return bool, got {type(allowed)}"
            )
        return allowed

@dataclass(frozen=True)
class ReaskPolicy(DefaultPolicy):
    max_reasks: int = 1

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        if step.name == "reask":
            if data.get("action") != "reask":
                return False
            return int(data.get("reask_count", 0)) < self.max_reasks

        return super().should_run(step, data, ctx)
    
@dataclass(frozen=True)
class SecondPassAfterReaskPolicy(ReaskPolicy):
    """
    Skip the SECOND occurrence of certain steps unless reasked=True.
    This lets you keep a linear step list with duplicates, without Guard wrappers.
    """

    gated_second_pass: frozenset[str] = frozenset({"repair_json", "score", "grade", "decide"})

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        # Gate only the *second* occurrence of these step names
        if step.name in self.gated_second_pass and ctx.occurrence >= 2:
            return bool(data.get("reasked", False))

        return super().should_run(step, data, ctx)

@dataclass(frozen=True)
class CompositePolicy:
    """
    Evaluates multiple policies in order.
    First policy to return False vetoes execution (short-circuit).
    """

    policies: Sequence[Policy]

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        for policy in self.policies:
            if not policy.should_run(step, data, ctx):
                return False
        return True
    

@dataclass(frozen=True)
class BlockIfFlaggedPolicy:
    """
    Veto running certain steps if specific failure flags exist in data["failure_flags"].

    flagged_steps: upstream steps that, if flagged, should block downstream steps
    blocked_steps: downstream steps to veto if any flagged upstream step exists
    """

    flagged_steps: frozenset[str]
    blocked_steps: frozenset[str]

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        if step.name not in self.blocked_steps:
            return True

        flags = data.get("failure_flags", {})
        if not isinstance(flags, dict):
            raise TypeError("failure_flags must be a dict when present")

        return not any(upstream in flags for upstream in self.flagged_steps)