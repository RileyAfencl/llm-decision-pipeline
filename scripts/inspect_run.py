from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.utils.persist import load_run_record, load_run_index



def _resolve_path(arg: str, runs_dir: Path) -> Path:
    p = Path(arg)

    # If they passed an existing path (file), use it.
    if p.exists() and p.is_file():
        return p

    # Otherwise treat it as a run_id and resolve runs/<run_id>.json
    candidate = runs_dir / f"{arg}.json"
    if candidate.exists() and candidate.is_file():
        return candidate

    raise FileNotFoundError(
        f"Could not resolve run artifact from '{arg}'. "
        f"Tried file path and '{candidate}'."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a persisted pipeline run artifact.")
    parser.add_argument("run", nargs="?", help="Run ID (UUID) or path to runs/<run_id>.json")
    parser.add_argument("--latest", action="store_true", help="Inspect latest run from run index")
    parser.add_argument("--runs-dir", default="runs", help="Directory containing run artifacts (default: runs)")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)

    if args.latest:
        idx = load_run_index(runs_dir)
        path = Path(idx["latest_path"])
    else:
        if not args.run:
            raise SystemExit("Provide RUN_ID/PATH or use --latest")
        path = _resolve_path(args.run, runs_dir)

    record = load_run_record(path)

    print(f"Run: {record.run_id}")
    print(f"Version: {record.summary_version}")
    print(f"Status: {record.status}")
    print(f"Started: {record.started_at}")
    print(f"Finished: {record.finished_at}")
    print(f"Duration: {record.duration_ms} ms")
    print()

    print("Counts")
    print(f"  attempted: {len(record.attempted)}")
    print(f"  ran:       {len(record.ran)}")
    print(f"  skipped:   {len(record.skipped)}")
    print(f"  failed:    {len(record.failed)}")
    print(f"  errored:   {len(record.errored)}")
    print()

    if record.error:
        print("Error")
        # Keep it simple: print the structured dict
        for k, v in record.error.items():
            print(f"  {k}: {v}")
        print()

    if record.failure_events:
        print(f"Failures ({len(record.failure_events)})")
        for ev in record.failure_events:
            step = ev.get("step")
            occ = ev.get("occurrence")
            mode = ev.get("failure_mode")
            reason = ev.get("failure_reason") or ev.get("message")
            print(f"  - {step}#{occ} mode={mode} reason={reason}")
        print()

    print(f"Decision events ({len(record.decision_events)})")
    for ev in record.decision_events:
        step = ev.get("step")
        occ = ev.get("occurrence")
        ran = ev.get("run")
        pol = ev.get("policy")
        reason = ev.get("reason")
        status = "ran" if ran else "skipped"
        print(f"  {step}#{occ} {status} — {reason} ({pol})")


if __name__ == "__main__":
    main()