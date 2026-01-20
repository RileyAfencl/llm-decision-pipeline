from __future__ import annotations

from pipeline.orchestrator import run_pipeline
from pipeline.steps.base import PipelineStep


class BadWriteStep(PipelineStep):
    name = "bad_write"
    reads = set()
    writes = {"ok"}  # does NOT declare "oops"
    deletes = set()
    retry_config = None

    def run(self, data: dict) -> dict:
        return {"ok": 1, "oops": 2}


def test_step_returning_undeclared_keys_fails() -> None:
    result = run_pipeline([BadWriteStep()], initial_data={})
    assert result["action"] == "error"
    assert result["error"]["type"] == "invariant_violation"
    assert result["error"]["step"] == "bad_write"
