from __future__ import annotations

import pytest

from pipeline.orchestrator import run_pipeline
from pipeline.steps.base import PipelineStep
from pipeline.utils.invariants import InvariantViolation
from pipeline.policy import DefaultPolicy


class DummyStep(PipelineStep):
    name = "dummy"
    retry_config = None
    writes = {"dummy_ran"}

    def run(self, input_data: dict) -> dict:
        return {"dummy_ran": True}


def test_invariant_violation_returns_structured_error() -> None:
    
    # If your REQUIRES_BEFORE map includes "prompt", use an actual Prompt-like dummy:
    class PromptLike(PipelineStep):
        name = "prompt"
        retry_config = None
        writes = {"raw_output"}
        reads = {"question"}

        def run(self, input_data: dict) -> dict:
            return {"raw_output": "x"}

    with pytest.raises(InvariantViolation) as excinfo:
        run_pipeline([PromptLike()], initial_data={})

    err = excinfo.value
    assert err.step == "prompt"
    assert "question" in err.missing_keys


def test_pipeline_runs_step_when_invariants_satisfied() -> None:
    class PromptLike(PipelineStep):
        name = "prompt"
        retry_config = None
        writes = {"raw_output"}
        reads = {"question"}

        def run(self, input_data: dict) -> dict:
            return {"raw_output": "ok"}

    result = run_pipeline([PromptLike(), DummyStep()], initial_data={"question": "hi"}, policy=DefaultPolicy())

    assert result.get("raw_output") == "ok"
    assert result.get("dummy_ran") is True
    assert "timings" in result
    assert "prompt" in result["timings"]
    assert "dummy" in result["timings"]
