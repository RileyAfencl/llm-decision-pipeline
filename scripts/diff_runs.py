from __future__ import annotations
import argparse
from pathlib import Path
from pipeline.utils.persist import load_run_index, load_run_record
from pipeline.utils.run_diff import diff_runs
from pipeline.diff_verdict import DiffVerdict

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
    parser.add_argument("--latest-2",action="store_true",help="Compare the two most recent runs from the run index",)
    parser.add_argument("--json",action="store_true",help="Output diff result as JSON",)
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)

    if args.latest_2:
        idx = load_run_index(runs_dir)
        recent = idx.get("recent", [])
        if len(recent) < 2:
            raise SystemExit("Need at least two indexed runs for --latest-2")
        path_a = Path(recent[0]["path"])
        path_b = Path(recent[1]["path"])
    elif args.latest:
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

    mismatches = []

    if not diff["status"]["match"]:
        mismatches.append("status")

    if not diff["duration_ms"]["match"]:
        mismatches.append("duration_ms")

    for key, payload in diff["counts"].items():
        if not payload["match"]:
            mismatches.append(f"counts.{key}")

    if not diff["validated"]["answer"]["match"]:
        mismatches.append("validated.answer")

    if not diff["validated"]["confidence"]["match"]:
        mismatches.append("validated.confidence")
    
    if not diff["summary_version"]["match"]:
        mismatches.append("summary_version")

    if not diff["inputs_present"]["match"]:
        mismatches.append("inputs_present")

    if not diff["validated_present"]["match"]:
        mismatches.append("validated_present")

    print("RUN DIFF")
    print(f"run_a: {diff['run_a_id']}")
    print(f"run_b: {diff['run_b_id']}")
    print()

    summary_version = diff["summary_version"]
    print("SCHEMA")
    print(f"summary_version_a: {summary_version['a']}")
    print(f"summary_version_b: {summary_version['b']}")
    print(f"summary_version_match: {summary_version['match']}")

    inputs_present = diff["inputs_present"]
    print(f"inputs_present_a: {inputs_present['a']}")
    print(f"inputs_present_b: {inputs_present['b']}")
    print(f"inputs_presence_match: {inputs_present['match']}")

    validated_present = diff["validated_present"]
    print(f"validated_present_a: {validated_present['a']}")
    print(f"validated_present_b: {validated_present['b']}")
    print(f"validated_presence_match: {validated_present['match']}")
    print()

    print("DIFF HIGHLIGHTS")
    if mismatches:
        for item in mismatches:
            print(f"- {item}")
    else:
        print("- no mismatches")
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

    print("COUNT MISMATCHES")
    count_mismatches = {
        key: payload
        for key, payload in diff["counts"].items()
        if not payload["match"]
    }

    if count_mismatches:
        for key, payload in count_mismatches.items():
            print(
                f"{key}: "
                f"a={payload['a']} "
                f"b={payload['b']} "
                f"delta={payload['delta']}"
            )
    else:
        print("- none")
    print()

    print("ALL COUNTS")
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

    schema_match = (
        diff["summary_version"]["match"]
        and diff["inputs_present"]["match"]
        and diff["validated_present"]["match"]
    )

    status_match = diff["status"]["match"]
    duration_match = diff["duration_ms"]["match"]
    all_count_matches = all(v["match"] for v in diff["counts"].values())
    validated_answer_match = diff["validated"]["answer"]["match"]
    validated_confidence_match = diff["validated"]["confidence"]["match"]

    if schema_match and status_match and all_count_matches and validated_answer_match and validated_confidence_match and duration_match:
        diff_verdict = DiffVerdict.FULL_MATCH
    elif schema_match and status_match and all_count_matches:
        diff_verdict = DiffVerdict.STRUCTURAL_MATCH_ONLY
    elif not schema_match:
        diff_verdict = DiffVerdict.SCHEMA_MISMATCH
    else:
        diff_verdict = DiffVerdict.RUN_MISMATCH
    
    if diff_verdict == DiffVerdict.FULL_MATCH:
        diff_health = "healthy"
    elif diff_verdict == DiffVerdict.STRUCTURAL_MATCH_ONLY:
        diff_health = "content_drift"
    elif diff_verdict == DiffVerdict.SCHEMA_MISMATCH:
        diff_health = "schema_mismatch"
    else:
        diff_health = "needs_attention"

    diff_result = {
        "verdict": diff_verdict.value,
        "health": {
        "status": diff_health,
        },
        "status": {
            "a": diff["status"]["a"],
            "b": diff["status"]["b"],
            "match": diff["status"]["match"],
        },
        "duration": {
            "a_ms": diff["duration_ms"]["a"],
            "b_ms": diff["duration_ms"]["b"],
            "delta_ms": diff["duration_ms"]["delta"],
            "match": diff["duration_ms"]["match"],
        },
        "counts": diff["counts"],
        "validated": {
            "answer_match": diff["validated"]["answer"]["match"],
            "confidence_match": diff["validated"]["confidence"]["match"],
        },
        "schema": {
            "summary_version_match": diff["summary_version"]["match"],
            "inputs_match": diff["inputs_present"]["match"],
            "validated_match": diff["validated_present"]["match"],
        },
   }

    print("DIFF SUMMARY")
    print(f"all_checks_passed: {schema_match and status_match and duration_match and all_count_matches and validated_answer_match and validated_confidence_match}")
    print(f"verdict: {diff_verdict.value}")
    print(f"health: {diff_health}")

    created_at = diff["created_at"]
    print(f"created_at_a: {created_at['a']}")
    print(f"created_at_b: {created_at['b']}")
    print()

    if not summary_version["match"]:
        print("SCHEMA VERSION MISMATCH")
        print("These runs were produced under different artifact versions.")
        print("Comparison may still run, but results should be interpreted carefully.")
        print()

    if args.json:
        import json
        print(json.dumps(diff_result, indent=2))

if __name__ == "__main__":
    main()