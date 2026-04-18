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

def _aggregate_rows(rows: List[Tuple[Dict[str, Any], float]]) -> Dict[str, Any]:
    total_runs = len(rows)
    success = 0
    degraded = 0
    error = 0
    total_duration_ms = 0
    total_run_rate = 0.0
    total_failures = 0
    validated_present = 0
    validated_missing = 0

    for metrics, _mtime in rows:
        status = metrics.get("status")
        if status == "success":
            success += 1
        elif status == "degraded":
            degraded += 1
        elif status == "error":
            error += 1

        total_duration_ms += int(metrics.get("duration_ms", 0) or 0)
        total_run_rate += float(metrics.get("run_rate", 0.0) or 0.0)
        total_failures += int(metrics.get("failures_total", 0) or 0)
        validated_present_flag = metrics.get("validated_present")
        if validated_present_flag is True:
            validated_present += 1
        else:
            validated_missing += 1

    avg_duration_ms = (total_duration_ms / total_runs) if total_runs else 0.0
    avg_run_rate = (total_run_rate / total_runs) if total_runs else 0.0

    validated_success_rate = (validated_present / total_runs if total_runs else 0.0)

    return {
        "total_runs": total_runs,
        "success": success,
        "degraded": degraded,
        "error": error,
        "avg_duration_ms": avg_duration_ms,
        "avg_run_rate": avg_run_rate,
        "total_failures": total_failures,
        "validated_present": validated_present,
        "validated_missing": validated_missing,
        "validated_success_rate": validated_success_rate    
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize run artifacts in a directory.")
    parser.add_argument("--runs-dir", default="runs", help="Directory containing run artifacts (default: runs)")
    parser.add_argument("--limit", type=int, default=25, help="Max rows to print (default: 25)")
    parser.add_argument("--latest", type=int, help="Summarize last N runs from run index (fallback to directory scan)")
    parser.add_argument("--latest-2",action="store_true",help="Summarize the two most recent indexed runs")
    parser.add_argument("--json",action="store_true",help="Output summary as JSON")
    args = parser.parse_args()


    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        raise FileNotFoundError(str(runs_dir))

    rows: List[Tuple[Dict[str, Any], float]] = []

    if args.latest_2:
        idx = load_run_index(runs_dir)
        recent = idx.get("recent", [])[:2]
        rows = []
        for entry in recent:
            rows.append(_load_metrics_for_path(Path(entry["path"])))
    elif args.latest:
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


    print()

    agg = _aggregate_rows(rows)

    validated_success_rate = agg["validated_success_rate"]

    if agg["error"] > 0:
        health = "needs_attention"
    elif agg["degraded"] > 0:
        health = "degraded"
    elif validated_success_rate < 0.8:
        health = "schema_mixed_or_incomplete"
    else:
        health = "healthy"
    if health == "healthy":
        summary_verdict = "stable"
    elif health == "schema_mixed_or_incomplete":
        summary_verdict = "mixed"
    else:
        summary_verdict = "attention_required"

    summary = {
        "verdict": summary_verdict,
        "health": {
            "status": health,
        },
        "runs": {
            "total": agg["total_runs"],
            "success": agg["success"],
            "degraded": agg["degraded"],
            "error": agg["error"],
        },
        "performance": {
            "avg_duration_ms": agg["avg_duration_ms"],
            "avg_run_rate": agg["avg_run_rate"],
        },
        "failures": {
            "total": agg["total_failures"],
        },
        "validation": {
            "present": agg["validated_present"],
            "missing": agg["validated_missing"],
            "success_rate": agg["validated_success_rate"],
        },
    }

    print("RUNS SUMMARY")
    print(f"total_runs:       {agg['total_runs']}")
    print(f"success:          {agg['success']}")
    print(f"degraded:         {agg['degraded']}")
    print(f"error:            {agg['error']}")
    print(f"avg_duration_ms:  {agg['avg_duration_ms']:.2f}")
    print(f"avg_run_rate:     {agg['avg_run_rate']:.2f}")
    print(f"total_failures:   {agg['total_failures']}")
    print(f"health:           {health}")

    print()
    print("VALIDATION SUMMARY")
    print(f"validated_present: {agg['validated_present']}")
    print(f"validated_missing: {agg['validated_missing']}")
    print(f"validated_success_rate: {agg['validated_success_rate']:.2%}")

    if args.json:
        import json
        print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()