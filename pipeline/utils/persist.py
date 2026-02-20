from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


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
            attempted=list(summary.get("attempted", [])),
            ran=list(summary.get("ran", [])),
            skipped=list(summary.get("skipped", [])),
            failed=list(summary.get("failed", [])),
            errored=list(summary.get("errored", [])),
            decision_events=_to_jsonable(summary.get("decision_events", [])),
            failure_events=_to_jsonable(summary.get("failure_events", [])),
            error=_to_jsonable(summary.get("error")) if summary.get("error") else None,
            created_at=_utc_now_iso(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return _to_jsonable(asdict(self))


def persist_run_record(record: RunRecord, runs_dir: str | Path = "runs") -> Path:
    runs_path = Path(runs_dir)
    runs_path.mkdir(parents=True, exist_ok=True)

    out_path = runs_path / f"{record.run_id}.json"
    out_path.write_text(
        json.dumps(record.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return out_path

