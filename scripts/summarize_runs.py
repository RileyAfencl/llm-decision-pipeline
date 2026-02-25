from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pipeline.utils.persist import load_run_index, load_run_record
from pipeline.utils.run_metrics import derive_run_metrics


def _safe_started_at(metrics: Dict[str, Any]) -> str:
    # ISO timestamps sort lexicographically when consistent
    v = metrics.get("started_at")
    return str(v) if v is not None else ""


def _collect_run_paths(runs_dir: Path) -> List[Path]:
    return sorted([p for p in runs_dir.glob("*.json") if p.is_file()])


def _load_metrics_for_path(path: Path) -> Tuple[Dict[str, Any], float]:
    """
    Returns (metrics, fallback_mtime).
    """
    record = load_run_record(path)
    metrics = derive_run_metrics(record)
    return metrics, path.stat().st_mtime


def _fmt(s: Any, width: int) -> str:
    txt = "" if s is None else str(s)
    if len(txt) > width:
        return txt[: width - 1] + "…"
    return txt.ljust(width)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize run artifacts in a directory.")
    parser.add_argument("--runs-dir", default="runs", help="Directory containing run artifacts (default: runs)")
    parser.add_argument("--limit", type=int, default=25, help="Max rows to print (default: 25)")
    parser.add_argument("--latest", type=int, help="Summarize last N runs from run index (fallback to directory scan)")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        raise FileNotFoundError(str(runs_dir))

    rows: List[Tuple[Dict[str, Any], float]] = []
    if args.latest:
        try:
            idx = load_run_index(runs_dir)
            recent = idx.get("recent", [])[: args.latest]
            for entry in recent:
                rows.append(_load_metrics_for_path(Path(entry["path"])))
        except Exception:
            rows = [
                _load_metrics_for_path(p)
                for p in _collect_run_paths(runs_dir)
            ]
    else:
        rows = [
        _load_metrics_for_path(p)
        for p in _collect_run_paths(runs_dir)
        ]

    # Sort newest first
    def sort_key(item: Tuple[Dict[str, Any], float]) -> Tuple[str, float]:
        m, mtime = item
        started = _safe_started_at(m)
        return (started, mtime)

    rows.sort(key=sort_key, reverse=True)
    rows = rows[: max(0, args.limit)]

    # Header
    print(
        "  ".join(
            [
                _fmt("run_id", 10),
                _fmt("status", 12),
                _fmt("dur_ms", 8),
                _fmt("att", 4),
                _fmt("ran", 4),
                _fmt("skp", 4),
                _fmt("fail", 5),
                _fmt("err", 3),
                _fmt("run_rate", 8),
                _fmt("started_at", 20),
            ]
        )
    )
    print("-" * 92)

    for m, _mtime in rows:
        counts = m.get("counts", {}) or {}
        run_id = str(m.get("run_id", ""))[:10]
        status = m.get("status", "")
        dur = m.get("duration_ms", "")
        att = counts.get("attempted", 0)
        ran = counts.get("ran", 0)
        skp = counts.get("skipped", 0)
        fail_total = m.get("failures_total", 0)
        has_err = "Y" if m.get("has_error") else "N"
        rate = m.get("run_rate", 0.0)

        print(
            "  ".join(
                [
                    _fmt(run_id, 10),
                    _fmt(status, 12),
                    _fmt(dur, 8),
                    _fmt(att, 4),
                    _fmt(ran, 4),
                    _fmt(skp, 4),
                    _fmt(fail_total, 5),
                    _fmt(has_err, 3),
                    _fmt(f"{rate:.2f}", 8),
                    _fmt(m.get("started_at", ""), 20),
                ]
            )
        )


if __name__ == "__main__":
    main()