from pipeline.orchestrator import preflight_validate
from pipeline.steps.base import PipelineStep
import pytest
from pipeline.utils.invariants import InvariantViolation


class StepA(PipelineStep):
    name = "a"
    reads = {"question"}
    writes = {"raw_output"}

    def run(self, data: dict) -> dict:
        return {}

class StepB(PipelineStep):
    name = "b"
    reads = {"raw_output"}
    writes = {"validated"}

    def run(self, data: dict) -> dict:
        return {}

def test_preflight_passes_for_valid_order():
    steps = [StepA(), StepB()]
    initial = {"question": "hi"}
    preflight_validate(steps, initial)


def test_preflight_fails_for_bad_order():
    steps = [StepB(), StepA()]  # wrong: B needs raw_output, but A hasn't run
    initial = {"question": "hi"}

    with pytest.raises(InvariantViolation) as exc:
        preflight_validate(steps, initial)

    assert exc.value.step == "b"
    assert "raw_output" in exc.value.missing_keys