import json
from pathlib import Path

from pipeline.utils.persist import RunRecord, persist_run_record


def _mk_record(run_id: str, started_at: str) -> RunRecord:
    return RunRecord(
        summary_version="v1",
        run_id=run_id,
        status="success",
        started_at=started_at,
        finished_at=started_at,
        duration_ms=1,
        attempted=[],
        ran=[],
        skipped=[],
        failed=[],
        errored=[],
        decision_events=[],
        failure_events=[],
        error=None,
        created_at=started_at,
    )


def test_index_created_and_latest_updated(tmp_path: Path) -> None:
    r1 = _mk_record("r1", "2026-01-01T00:00:00+00:00")
    p1 = persist_run_record(r1, runs_dir=tmp_path)
    assert p1.exists()

    index_path = tmp_path / "index.json"
    assert index_path.exists()

    idx = json.loads(index_path.read_text(encoding="utf-8"))
    assert idx["latest_run_id"] == "r1"
    assert idx["recent"][0]["run_id"] == "r1"

    r2 = _mk_record("r2", "2026-01-02T00:00:00+00:00")
    persist_run_record(r2, runs_dir=tmp_path)

    idx2 = json.loads(index_path.read_text(encoding="utf-8"))
    assert idx2["latest_run_id"] == "r2"
    assert idx2["recent"][0]["run_id"] == "r2"
    assert idx2["recent"][1]["run_id"] == "r1"


def test_index_recent_dedupes(tmp_path: Path) -> None:
    r1 = _mk_record("r1", "2026-01-01T00:00:00+00:00")
    persist_run_record(r1, runs_dir=tmp_path)
    persist_run_record(r1, runs_dir=tmp_path)  # same id again

    idx = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert idx["latest_run_id"] == "r1"
    recent_ids = [r["run_id"] for r in idx["recent"]]
    assert recent_ids.count("r1") == 1