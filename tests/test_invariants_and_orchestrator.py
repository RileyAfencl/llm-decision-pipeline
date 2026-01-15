from __future__ import annotations

from pipeline.orchestrator import run_pipeline
from pipeline.steps.base import PipelineStep


class DummyStep(PipelineStep):
    name = "dummy"
    retry_config = None

    def run(self, input_data: dict) -> dict:
        return {**input_data, "dummy_ran": True}


def test_invariant_violation_returns_structured_error() -> None:
    
    # If your REQUIRES_BEFORE map includes "prompt", use an actual Prompt-like dummy:
    class PromptLike(PipelineStep):
        name = "prompt"
        retry_config = None

        def run(self, input_data: dict) -> dict:
            return {**input_data, "raw_output": "x"}

    result = run_pipeline([PromptLike()], initial_data={})

    assert result["action"] == "error"
    assert "error" in result
    assert result["error"]["type"] == "invariant_violation"
    assert result["error"]["step"] == "prompt"
    assert "missing_keys" in result["error"]
    assert "question" in result["error"]["missing_keys"]


def test_pipeline_runs_step_when_invariants_satisfied() -> None:
    class PromptLike(PipelineStep):
        name = "prompt"
        retry_config = None

        def run(self, input_data: dict) -> dict:
            return {**input_data, "raw_output": "ok"}

    result = run_pipeline([PromptLike(), DummyStep()], initial_data={"question": "hi"})

    assert result.get("raw_output") == "ok"
    assert result.get("dummy_ran") is True
    assert "timings" in result
    assert "prompt" in result["timings"]
    assert "dummy" in result["timings"]
