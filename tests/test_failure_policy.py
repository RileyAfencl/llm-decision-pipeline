from __future__ import annotations

from dataclasses import dataclass

from pipeline.failure_policy import FailureDecision, FailureMode
from pipeline.steps.base import PipelineStep
from pipeline.policy import StepContext


@dataclass(frozen=True)
class BoomStep(PipelineStep):
    name: str = "boom"
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    deletes: tuple[str, ...] = ()

    def run(self, input_data: dict) -> dict:
        raise ValueError("kaboom")


@dataclass(frozen=True)
class SpyFailurePolicy:

    def on_step_failure(self, step: PipelineStep, data: dict, ctx: StepContext, exc: Exception) -> FailureDecision:
        # We can't mutate a frozen dataclass counter; instead, mark in data.
        data["__failure_policy_called__"] = True
        return FailureDecision(mode=FailureMode.ABORT, reason="spy abort")


def test_failure_policy_is_called_and_abort_sets_metadata() -> None:
    from pipeline.orchestrator import run_pipeline  # adjust if your module path differs

    steps = [BoomStep()]
    out = run_pipeline(
        steps=steps,
        initial_data={},
        failure_policy=SpyFailurePolicy(),
    )

    assert out["action"] == "error"
    assert out["__failure_policy_called__"] is True
    assert out["error"]["step"] == "boom"
    assert out["error"]["failure_mode"] == "abort"
    assert out["error"]["failure_reason"] == "spy abort"
    assert out["error"]["message"] == "spy abort"
    summary = out["run_summary"]
    assert "error" in summary
    assert (summary["error"] is None) or isinstance(summary["error"], dict)
    assert summary["status"] == "error"
    assert isinstance(summary["error"], dict)
    assert summary["error"]["step"] == "boom"
    assert summary["error"]["failure_mode"] == "abort"
    assert summary["error"]["step_index"] == 0
    assert summary["error"]["occurrence"] == 1  