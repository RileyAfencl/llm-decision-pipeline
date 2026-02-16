from __future__ import annotations

from dataclasses import dataclass

from pipeline.orchestrator import run_pipeline
from pipeline.policy import DefaultPolicy
from pipeline.steps.base import PipelineStep


@dataclass(frozen=True)
class StepA(PipelineStep):
    name: str = "a"
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ("a_out",)
    deletes: tuple[str, ...] = ()

    def run(self, input_data: dict) -> dict:
        return {"a_out": True}


def test_run_summary_schema_contains_decisions_and_narrative() -> None:
    out = run_pipeline(
        steps=[StepA()],
        initial_data={},
        policy=DefaultPolicy(),
    )

    summary = out["run_summary"]

    # Top-level keys we care about as an interface
    for key in (
        "status",
        "attempted_steps",
        "ran_steps",
        "skipped_steps",
        "failures",
        "failure_flags",
        "total_time_s",
        "decision_events",
        "decision_narrative",
    ):
        assert key in summary, f"missing run_summary['{key}']"

    assert isinstance(summary["decision_events"], list)
    assert isinstance(summary["decision_narrative"], list)

    # decision_narrative should be strings
    assert all(isinstance(s, str) for s in summary["decision_narrative"])

    # decision_events should be dicts with required fields
    required_event_keys = {
        "step",
        "occurrence",
        "run",
        "policy",
        "reason",
        "step_index",
    }

    required_failure_keys = {
        "type",
        "step",
        "message",
        "failure_mode",
        "failure_reason",
        "step_index",
        "occurrence",
    }

    for ev in summary["decision_events"]:
        assert isinstance(ev, dict)
        missing = required_event_keys - set(ev.keys())
        assert not missing, f"decision_event missing keys: {sorted(missing)}"
    
    for f in summary["failures"]:
        assert isinstance(f, dict)
        missing = required_failure_keys - set(f.keys())
        assert not missing, f"failure missing keys: {sorted(missing)}"

    # narrative should correspond 1:1 with events (same count)
    assert len(summary["decision_events"]) == len(summary["decision_narrative"])

    


