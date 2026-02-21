import json
from pathlib import Path

import pytest

from pipeline.utils.persist import RunRecord, persist_run_record, load_run_record


def test_load_run_record_round_trip(tmp_path: Path) -> None:
    record = RunRecord(
        summary_version="v1",
        run_id="test-run",
        status="success",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:00:01+00:00",
        duration_ms=1000,
        attempted=["prompt#1"],
        ran=["prompt#1"],
        skipped=[],
        failed=[],
        errored=[],
        decision_events=[{"step": "prompt", "occurrence": 1, "run": True}],
        failure_events=[],
        error=None,
        created_at="2026-01-01T00:00:02+00:00",
    )

    out_path = persist_run_record(record, runs_dir=tmp_path)
    loaded = load_run_record(out_path)

    assert loaded.summary_version == "v1"
    assert loaded.run_id == record.run_id
    assert loaded.status == record.status
    assert loaded.duration_ms == record.duration_ms
    assert loaded.attempted == record.attempted
    assert loaded.decision_events == record.decision_events


def test_load_run_record_rejects_unknown_version(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"summary_version": "v999"}), encoding="utf-8")

    with pytest.raises(ValueError) as e:
        load_run_record(p)

    assert "Unsupported run artifact version" in str(e.value)