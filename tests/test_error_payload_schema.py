from __future__ import annotations

from dataclasses import dataclass

from pipeline.orchestrator import run_pipeline
from pipeline.policy import DefaultPolicy
from pipeline.steps.base import PipelineStep


@dataclass(frozen=True)
class BadStep(PipelineStep):
    name: str = "bad"
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ("declared",)
    deletes: tuple[str, ...] = ()

    def run(self, input_data: dict) -> dict:
        # Undeclared key => InvariantViolation (Step returned undeclared keys)
        return {"NOT_DECLARED": True}


def test_invariant_violation_error_includes_step_index_and_occurrence() -> None:
    out = run_pipeline(
        steps=[BadStep()],
        initial_data={},
        policy=DefaultPolicy(),
    )

    assert out.get("action") == "error"
    assert isinstance(out.get("error"), dict)

    err = out["error"]
    assert err["type"] == "invariant_violation"

    # the important assertions
    assert "step_index" in err
    assert "occurrence" in err
    assert isinstance(err["step_index"], int)
    assert isinstance(err["occurrence"], int)

    # sanity: should point at the failing step
    assert err["step"] == "bad"
    assert err["step_index"] == 0
    assert err["occurrence"] == 1

