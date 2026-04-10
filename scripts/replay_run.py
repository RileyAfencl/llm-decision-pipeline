from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.orchestrator import run_pipeline
from pipeline.policy import CompositePolicy, DefaultPolicy, SecondPassAfterReaskPolicy
from pipeline.steps.choose_best_step import ChooseBestStep
from pipeline.steps.decide_step import DecideStep
from pipeline.steps.explain_decision_step import ExplainDecisionStep
from pipeline.steps.grade_step import GradeStep
from pipeline.steps.prompt_step import PromptStep
from pipeline.steps.reask_step import ReaskStep
from pipeline.steps.repair_json_step import RepairJsonStep
from pipeline.steps.score_step import ScoreStep
from pipeline.utils.persist import load_run_index, load_run_record
from pipeline.utils.replay import reconstruct_initial_data


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


def _build_steps():
    return [
        PromptStep(),
        RepairJsonStep(),
        ScoreStep(),
        GradeStep(),
        DecideStep(),
        ReaskStep(),
        RepairJsonStep(),
        ScoreStep(),
        GradeStep(),
        DecideStep(),
        ChooseBestStep(),
        ExplainDecisionStep(),
    ]


def _build_policy():
    return CompositePolicy(
        policies=[
            DefaultPolicy(),
            SecondPassAfterReaskPolicy(max_reasks=1),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a persisted pipeline run.")
    parser.add_argument("run", nargs="?", help="Run ID (UUID) or path to runs/<run_id>.json")
    parser.add_argument("--runs-dir", default="runs", help="Directory containing run artifacts (default: runs)")
    parser.add_argument("--latest", action="store_true", help="Use latest run from runs/index.json")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)

    if args.latest:
        idx = load_run_index(runs_dir)
        run_path = Path(idx["latest_path"])
    else:
        if not args.run:
            raise SystemExit("Provide RUN_ID/PATH or use --latest")
        run_path = _resolve_run_path(args.run, runs_dir)

    original_record = load_run_record(run_path)
    initial_data = reconstruct_initial_data(original_record)

    print("RECONSTRUCTED INITIAL_DATA")
    print(initial_data)
    print()

    replay_result = run_pipeline(
        _build_steps(),
        initial_data,
        policy=_build_policy(),
    )
    replay_summary = replay_result["run_summary"]

    print("REPLAY COMPARISON")
    print(f"original_status: {original_record.status}")
    print(f"replay_status:   {replay_summary['status']}")
    print()

    original_decision_count = len(original_record.decision_events)
    replay_decision_count = len(replay_summary.get("decision_events", []))

    print(f"original_decision_events: {original_decision_count}")
    print(f"replay_decision_events:   {replay_decision_count}")
    print()

    original_attempted = len(original_record.attempted)
    replay_attempted = len(replay_summary.get('attempted_steps', []))

    print(f"original_attempted: {original_attempted}")
    print(f"replay_attempted:   {replay_attempted}")
    print()

    original_skipped = len(original_record.skipped)
    replay_skipped = len(replay_summary.get("skipped_steps", []))

    print(f"original_skipped: {original_skipped}")
    print(f"replay_skipped:   {replay_skipped}")
    print()

    status_match = original_record.status == replay_summary["status"]
    decision_count_match = original_decision_count == replay_decision_count
    attempted_match = original_attempted == replay_attempted
    skipped_match = original_skipped == replay_skipped

    print("REPLAY MATCH FLAGS")
    print(f"status_match:         {status_match}")
    print(f"decision_count_match: {decision_count_match}")
    print(f"attempted_match:      {attempted_match}")
    print(f"skipped_match:        {skipped_match}")
    print()

    original_duration_ms = original_record.duration_ms
    replay_duration_ms = replay_summary["duration_ms"]

    print("REPLAY DURATION")
    print(f"original_duration_ms: {original_duration_ms}")
    print(f"replay_duration_ms:   {replay_duration_ms}")
    print(f"duration_delta_ms:    {replay_duration_ms - original_duration_ms}")
    print()

    if not status_match:
        print("STATUS MISMATCH")
        print(f"original: {original_record.status}")
        print(f"replay:   {replay_summary['status']}")
        print()

    if not decision_count_match:
        print("DECISION COUNT MISMATCH")
        print(f"original: {original_decision_count}")
        print(f"replay:   {replay_decision_count}")
        print()

    if not attempted_match:
        print("ATTEMPTED MISMATCH")
        print(f"original: {original_attempted}")
        print(f"replay:   {replay_attempted}")
        print()

    if not skipped_match:
        print("SKIPPED MISMATCH")
        print(f"original: {original_skipped}")
        print(f"replay:   {replay_skipped}")
        print()

    all_match = (
    status_match
    and decision_count_match
    and attempted_match
    and skipped_match
    )

    print("REPLAY SUMMARY")
    print(f"all_checks_passed: {all_match}")
    print()

    print("REPLAY VALIDATED OUTPUT")
    print(replay_result.get("validated"))


if __name__ == "__main__":
    main()