from __future__ import annotations
import argparse
from pathlib import Path
from pprint import pprint
from pipeline.utils.persist import load_run_index, load_run_record
from pipeline.utils.run_diff import diff_runs


def _resolve_run_path(arg: str, runs_dir: Path) -> Path:
    p = Path(arg)
    if p.exists() and p.is_file():
        return p

    candidate = runs_dir / f"{arg}.json"
    if candidate.exists() and candidate.is_file():
        return candidate

    raise FileNotFoundError(
        f"Could not resolve run artifact from '{arg}'. "
        f"Tried file path and '{candidate}'."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Diff two persisted pipeline runs.")
    parser.add_argument("run_a", nargs="?", help="Baseline run id/path")
    parser.add_argument("run_b", nargs="?", help="Comparison run id/path")
    parser.add_argument("--runs-dir", default="runs", help="Directory containing run artifacts (default: runs)")
    parser.add_argument("--latest", action="store_true", help="Use latest run from index as run_a")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)

    if args.latest:
        idx = load_run_index(runs_dir)
        path_a = Path(idx["latest_path"])
        if not args.run_b:
            raise SystemExit("Provide run_b when using --latest")
        path_b = _resolve_run_path(args.run_b, runs_dir)
    else:
        if not args.run_a or not args.run_b:
            raise SystemExit("Provide run_a and run_b, or use --latest with run_b")
        path_a = _resolve_run_path(args.run_a, runs_dir)
        path_b = _resolve_run_path(args.run_b, runs_dir)

    record_a = load_run_record(path_a)
    record_b = load_run_record(path_b)

    diff = diff_runs(record_a, record_b)
    print("RUN DIFF")
    print(f"run_a: {diff['run_a_id']}")
    print(f"run_b: {diff['run_b_id']}")
    print()

    status = diff["status"]
    print("STATUS")
    print(f"a: {status['a']}")
    print(f"b: {status['b']}")
    print(f"match: {status['match']}")
    print()

    duration = diff["duration_ms"]
    print("DURATION")
    print(f"a_ms: {duration['a']}")
    print(f"b_ms: {duration['b']}")
    print(f"delta_ms: {duration['delta']}")
    print(f"match: {duration['match']}")
    print()

    print("COUNTS")
    for key, payload in diff["counts"].items():
        print(
            f"{key}: "
            f"a={payload['a']} "
            f"b={payload['b']} "
            f"delta={payload['delta']} "
            f"match={payload['match']}"
        )
    print()

    validated = diff["validated"]

    answer = validated["answer"]
    print("VALIDATED ANSWER")
    print(f"match: {answer['match']}")
    if not answer["match"]:
        print("a:")
        print(answer["a"])
        print("b:")
        print(answer["b"])
    print()

    confidence = validated["confidence"]
    print("VALIDATED CONFIDENCE")
    print(f"a: {confidence['a']}")
    print(f"b: {confidence['b']}")
    print(f"match: {confidence['match']}")
    print()

    all_count_matches = all(v["match"] for v in diff["counts"].values())
    all_checks_passed = (
        diff["status"]["match"]
        and diff["duration_ms"]["match"]
        and all_count_matches
        and diff["validated"]["answer"]["match"]
        and diff["validated"]["confidence"]["match"]
    )

    print("DIFF SUMMARY")
    print(f"all_checks_passed: {all_checks_passed}")


if __name__ == "__main__":
    main()