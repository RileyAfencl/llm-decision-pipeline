from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

SUPPORTED_SUMMARY_VERSIONS = {"v1"}

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_jsonable(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}

    try:
        return _to_jsonable(asdict(obj))  # dataclasses
    except Exception:
        pass

    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            return _to_jsonable(to_dict())
        except Exception:
            pass

    return str(obj)


@dataclass(frozen=True)
class RunRecord:
    summary_version: str

    run_id: str
    status: str

    started_at: str
    finished_at: str
    duration_ms: int

    attempted: List[str]
    ran: List[str]
    skipped: List[str]
    failed: List[str]
    errored: List[str]

    decision_events: List[Dict[str, Any]]
    failure_events: List[Dict[str, Any]]
    error: Optional[Dict[str, Any]]

    created_at: str

    inputs: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_execution_summary(
        cls,
        summary: Dict[str, Any],
        *,
        summary_version: str = "v1",
    ) -> "RunRecord":
        return cls(
            summary_version=summary_version,
            run_id=str(summary["run_id"]),
            status=str(summary["status"]),
            started_at=str(summary["started_at"]),
            finished_at=str(summary["finished_at"]),
            duration_ms=int(summary["duration_ms"]),
            attempted=list(summary.get("attempted_steps", [])),
            ran=list(summary.get("ran_steps", [])),
            skipped=list(summary.get("skipped_steps", [])),
            failed=[],
            errored=[],
            decision_events=_to_jsonable(summary.get("decision_events", [])),
            failure_events=_to_jsonable(summary.get("failures", [])),
            error=_to_jsonable(summary.get("error")) if summary.get("error") else None,
            created_at=_utc_now_iso(),
            inputs=None
        )

    def to_dict(self) -> Dict[str, Any]:
        return _to_jsonable(asdict(self))

def run_record_from_dict(payload: Dict[str, Any]) -> RunRecord:
    """
    Strict-ish constructor from a persisted dict.
    Version-gated to avoid silently accepting incompatible artifacts.
    """
    if not isinstance(payload, dict):
        raise TypeError("RunRecord payload must be a dict")
    
    inputs=_to_jsonable(payload.get("inputs")) if payload.get("inputs") is not None else None

    version = payload.get("summary_version")
    if version not in SUPPORTED_SUMMARY_VERSIONS:
        raise ValueError(
            f"Unsupported run artifact version: {version!r}. "
            f"Supported: {sorted(SUPPORTED_SUMMARY_VERSIONS)}"
        )

    attempted = payload.get("attempted")
    if attempted is None:
        attempted = payload.get("attempted_steps", [])

    ran = payload.get("ran")
    if ran is None:
        ran = payload.get("ran_steps", [])

    skipped = payload.get("skipped")
    if skipped is None:
        skipped = payload.get("skipped_steps", [])

    failure_events = payload.get("failure_events")
    if failure_events is None:
        failure_events = payload.get("failures", [])

    # Required core fields (fail loudly if missing)
    return RunRecord(
        summary_version=str(payload["summary_version"]),
        run_id=str(payload["run_id"]),
        status=str(payload["status"]),
        started_at=str(payload["started_at"]),
        finished_at=str(payload["finished_at"]),
        duration_ms=int(payload["duration_ms"]),
        attempted=attempted,
        ran=ran,
        skipped=skipped,
        failed=list(payload.get("failed", [])),
        errored=list(payload.get("errored", [])),
        decision_events=_to_jsonable(payload.get("decision_events", [])),
        failure_events=_to_jsonable(failure_events),
        error=_to_jsonable(payload.get("error")) if payload.get("error") else None,
        created_at=str(payload.get("created_at") or _utc_now_iso()),
        inputs=inputs
    )

def load_run_record(path: Union[str, Path]) -> RunRecord:
    """
    Load a persisted RunRecord JSON artifact from disk.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    raw = p.read_text(encoding="utf-8")
    payload = json.loads(raw)
    return run_record_from_dict(payload)

def _atomic_write_text(path: Path, text: str) -> None:
    """
    Atomic write: write to temp file in same directory then replace.
    Works cross-platform with os.replace.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def update_run_index(
    record: "RunRecord",
    *,
    runs_dir: Union[str, Path] = "runs",
    recent_limit: int = 50,
) -> Path:
    """
    Update runs/index.json with latest run metadata + rolling recent list.
    """
    runs_path = Path(runs_dir)
    index_path = runs_path / "index.json"

    # Best-effort load existing index
    data: Dict[str, Any] = {}
    if index_path.exists():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}

    # Build new entry
    entry = {
        "run_id": record.run_id,
        "path": str((runs_path / f"{record.run_id}.json").as_posix()),
        "started_at": record.started_at,
        "status": record.status,
        "duration_ms": record.duration_ms,
        "created_at": record.created_at,
    }

    # Update latest pointers
    data["latest_run_id"] = record.run_id
    data["latest_path"] = entry["path"]
    data["latest_started_at"] = record.started_at

    # Update rolling recent list (de-dupe by run_id, newest first)
    recent = data.get("recent")
    if not isinstance(recent, list):
        recent = []

    recent = [r for r in recent if isinstance(r, dict) and r.get("run_id") != record.run_id]
    recent.insert(0, entry)
    recent = recent[: max(0, int(recent_limit))]

    data["recent"] = recent
    data["index_version"] = "v1"
    data["updated_at"] = _utc_now_iso()

    _atomic_write_text(index_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return index_path

def load_run_index(runs_dir: Union[str, Path] = "runs") -> Dict[str, Any]:
    index_path = Path(runs_dir) / "index.json"
    if not index_path.exists():
        raise FileNotFoundError("Run index not found")

    data = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid run index format")

    return data

def persist_run_record(record: RunRecord, runs_dir: str | Path = "runs") -> Path:
    runs_path = Path(runs_dir)
    runs_path.mkdir(parents=True, exist_ok=True)

    out_path = runs_path / f"{record.run_id}.json"
    out_path.write_text(
        json.dumps(record.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    update_run_index(record, runs_dir=runs_dir)
    
    return out_path
