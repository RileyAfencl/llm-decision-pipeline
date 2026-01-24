from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from pipeline.steps.base import PipelineStep
from pipeline.policy import StepContext


class FailureMode(str, Enum):
    ABORT = "abort"
    SKIP = "skip"
    CONTINUE_WITH_FLAG = "continue_with_flag"


@dataclass(frozen=True)
class FailureDecision:
    mode: FailureMode
    reason: str | None = None


class FailurePolicy(Protocol):
    def on_step_failure(
        self,
        step: PipelineStep,
        data: dict,
        ctx: StepContext,
        exc: Exception,
    ) -> FailureDecision: ...

@dataclass(frozen=True)
class DefaultFailurePolicy:
    def on_step_failure(
        self,
        step: PipelineStep,
        data: dict,
        ctx: StepContext,
        exc: Exception,
    ) -> FailureDecision:
        return FailureDecision(
            mode=FailureMode.ABORT,
            reason=f"{step.name} failed: {exc.__class__.__name__}",
        )