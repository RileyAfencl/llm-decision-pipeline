from __future__ import annotations

from dataclasses import dataclass

from pipeline.orchestrator import run_pipeline
from pipeline.policy import DefaultPolicy, StepContext
from pipeline.steps.base import PipelineStep
from pipeline.failure_policy import FailureDecision, FailureMode


@dataclass(frozen=True)
class BoomStep(PipelineStep):
    name: str = "boom"
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    deletes: tuple[str, ...] = ()

    def run(self, input_data: dict) -> dict:
        raise ValueError("kaboom")


@dataclass(frozen=True)
class AlwaysAbortFailurePolicy:
    def on_step_failure(
        self,
        step: PipelineStep,
        data: dict,
        ctx: StepContext,
        exc: Exception,
    ) -> FailureDecision:
        return FailureDecision(mode=FailureMode.ABORT, reason="abort it")


def test_abort_error_includes_step_index_and_occurrence() -> None:
    out = run_pipeline(
        steps=[BoomStep()],
        initial_data={},
        policy=DefaultPolicy(),
        failure_policy=AlwaysAbortFailurePolicy(),
    )

    assert out.get("action") == "error"
    assert isinstance(out.get("error"), dict)

    err = out["error"]

    # ABORT payload shape
    assert err["type"] == "ValueError"
    assert err["step"] == "boom"
    assert err["failure_mode"] == "abort"
    assert err["failure_reason"] == "abort it"
    assert err["message"] == "abort it"  # your orchestrator uses decision.reason or str(e)

    # the important fields
    assert "step_index" in err
    assert "occurrence" in err
    assert err["step_index"] == 0
    assert err["occurrence"] == 1

def test_abort_run_summary_counts_aborted_step_as_attempted_not_ran() -> None:
    out = run_pipeline(
        steps=[BoomStep()],
        initial_data={},
        policy=DefaultPolicy(),
        failure_policy=AlwaysAbortFailurePolicy(),
    )

    summary = out["run_summary"]

    assert summary["status"] == "error"
    assert summary["attempted_steps"] == ["boom#1"]
    assert summary["ran_steps"] == []
    assert summary["skipped_steps"] == []