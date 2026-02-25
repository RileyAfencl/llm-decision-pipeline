from __future__ import annotations

from pipeline.utils.persist import RunRecord
from pipeline.utils.run_metrics import derive_run_metrics


def test_derive_run_metrics_basic_counts_and_rates() -> None:
    record = RunRecord(
        summary_version="v1",
        run_id="r1",
        status="success",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:00:01+00:00",
        duration_ms=1000,
        attempted=["a#1", "b#1"],
        ran=["a#1"],
        skipped=["b#1"],
        failed=[],
        errored=[],
        decision_events=[
            {"step": "a", "occurrence": 1, "run": True, "policy": "P", "reason": "ok", "step_index": 0},
            {"step": "b", "occurrence": 1, "run": False, "policy": "P", "reason": "gated", "step_index": 1},
        ],
        failure_events=[],
        error=None,
        created_at="2026-01-01T00:00:02+00:00",
    )

    m = derive_run_metrics(record)
    assert m["counts"]["attempted"] == 2
    assert m["counts"]["ran"] == 1
    assert m["counts"]["skipped"] == 1
    assert m["run_rate"] == 0.5
    assert m["has_error"] is False
    assert ("gated", 1) in m["skip_reasons_top"]
    assert ("b", 1) in m["skipped_steps_top"]


def test_derive_run_metrics_failures_and_modes() -> None:
    record = RunRecord(
        summary_version="v1",
        run_id="r2",
        status="degraded",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:00:01+00:00",
        duration_ms=1000,
        attempted=[],
        ran=[],
        skipped=[],
        failed=[],
        errored=[],
        decision_events=[],
        failure_events=[
            {"step": "score", "occurrence": 1, "failure_mode": "skip", "message": "x"},
            {"step": "score", "occurrence": 2, "failure_mode": "skip", "message": "y"},
            {"step": "repair_json", "occurrence": 1, "failure_mode": "continue_with_flag", "message": "z"},
        ],
        error={"type": "SomeError"},
        created_at="2026-01-01T00:00:02+00:00",
    )

    m = derive_run_metrics(record)
    assert m["failures_total"] == 3
    assert ("score", 2) in m["failures_by_step_top"]
    assert ("skip", 2) in m["failure_modes_top"]
    assert m["has_error"] is True