from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from pipeline.steps.base import PipelineStep


@dataclass(frozen=True)
class StepContext:
    step_index: int          # 0-based index in the steps list
    occurrence: int          # 1 for first time this step.name appears, 2 for second, etc.

@dataclass(frozen=True)
class ExecutionDecision:
    run: bool
    reason: str
    policy: str


class Policy(Protocol):
    """Decides whether a step is eligible to run given current pipeline state."""
    def decide(self, step: PipelineStep, data: dict, ctx: StepContext) -> ExecutionDecision:
        ...

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool: ...


@dataclass(frozen=True)
class DefaultPolicy:
    def decide(self, step: PipelineStep, data: dict, ctx: StepContext) -> ExecutionDecision:
        allowed = step.when(data)
        if not isinstance(allowed, bool):
            raise TypeError(
                f"{step.__class__.__name__}.when() must return bool, got {type(allowed)}"
            )
        return ExecutionDecision(
            run=allowed,
            reason="step.when(data) == True" if allowed else "step.when(data) == False",
            policy=self.__class__.__name__,
        )

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        return self.decide(step, data, ctx).run



@dataclass(frozen=True)
class ReaskPolicy(DefaultPolicy):
    max_reasks: int = 1

    def decide(self, step: PipelineStep, data: dict, ctx: StepContext) -> ExecutionDecision:
        if step.name == "reask":
            if data.get("action") != "reask":
                return ExecutionDecision(
                    run=False,
                    reason="reask blocked; action != 'reask'",
                    policy=self.__class__.__name__,
                )
            count = int(data.get("reask_count", 0))
            if count >= self.max_reasks:
                return ExecutionDecision(
                    run=False,
                    reason=f"reask blocked; max_reasks reached ({count} >= {self.max_reasks})",
                    policy=self.__class__.__name__,
                )
            return ExecutionDecision(
                run=True,
                reason="reask allowed",
                policy=self.__class__.__name__,
            )

        # defer to normal step.when contract
        return super().decide(step, data, ctx)

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        return self.decide(step, data, ctx).run

    
@dataclass(frozen=True)
class SecondPassAfterReaskPolicy(ReaskPolicy):
    """
    Skip the SECOND occurrence of certain steps unless reasked=True.
    This lets you keep a linear step list with duplicates, without Guard wrappers.
    """

    gated_second_pass: frozenset[str] = frozenset({"repair_json", "score", "grade", "decide"})

    def decide(self, step: PipelineStep, data: dict, ctx: StepContext) -> ExecutionDecision:
        if step.name in self.gated_second_pass and ctx.occurrence >= 2:
            reasked = bool(data.get("reasked", False))
            if not reasked:
                return ExecutionDecision(
                    run=False,
                    reason="gated second pass; reasked == False",
                    policy=self.__class__.__name__,
                )
            return ExecutionDecision(
                run=True,
                reason="second pass allowed; reasked == True",
                policy=self.__class__.__name__,
            )

        return super().decide(step, data, ctx)

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        return self.decide(step, data, ctx).run


@dataclass(frozen=True)
class CompositePolicy:
    """
    Evaluates multiple policies in order.
    First policy to return False vetoes execution (short-circuit).
    """

    policies: Sequence[Policy]

    def decide(self, step: PipelineStep, data: dict, ctx: StepContext) -> ExecutionDecision:
        trace_parts: list[str] = []

        def _short(s: str, max_len: int = 80) -> str:
            s = (s or "").strip()
            return s if len(s) <= max_len else s[: max_len - 1] + "…"

        for policy in self.policies:
            d = policy.decide(step, data, ctx)

            if d.run:
                trace_parts.append(f"{d.policy}=allow")
                continue  # IMPORTANT: keep evaluating remaining policies

            # veto
            trace_parts.append(f"{d.policy}✗({_short(d.reason)})")
            return ExecutionDecision(
                run=False,
                policy=self.__class__.__name__,
                reason="trace: " + "> ".join(trace_parts),
            )

        # all allowed
        return ExecutionDecision(
            run=True,
            policy=self.__class__.__name__,
            reason="trace: " + "> ".join(trace_parts) if trace_parts else "trace: <empty>",
        )


    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        return self.decide(step, data, ctx).run

    

@dataclass(frozen=True)
class BlockIfFlaggedPolicy:
    """
    Veto running certain steps if specific failure flags exist in data["failure_flags"].

    flagged_steps: upstream steps that, if flagged, should block downstream steps
    blocked_steps: downstream steps to veto if any flagged upstream step exists
    """

    flagged_steps: frozenset[str]
    blocked_steps: frozenset[str]

    def decide(self, step: PipelineStep, data: dict, ctx: StepContext) -> ExecutionDecision:
        if step.name not in self.blocked_steps:
            return ExecutionDecision(
                run=True,
                reason="step not in blocked_steps",
                policy=self.__class__.__name__,
            )

        flags = data.get("failure_flags", {})
        if not isinstance(flags, dict):
            raise TypeError("failure_flags must be a dict when present")

        blocked_by = [s for s in self.flagged_steps if s in flags]
        if blocked_by:
            return ExecutionDecision(
                run=False,
                reason=f"blocked by failure_flags from: {', '.join(blocked_by)}",
                policy=self.__class__.__name__,
            )

        return ExecutionDecision(
            run=True,
            reason="no blocking failure_flags present",
            policy=self.__class__.__name__,
        )

    def should_run(self, step: PipelineStep, data: dict, ctx: StepContext) -> bool:
        return self.decide(step, data, ctx).run
