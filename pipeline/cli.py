from __future__ import annotations

import argparse
from pathlib import Path
import json

from pipeline.orchestrator import run_pipeline
from pipeline.steps.prompt_step import PromptStep
from pipeline.steps.repair_json_step import RepairJsonStep
from pipeline.steps.score_step import ScoreStep
from pipeline.steps.decide_step import DecideStep
from pipeline.steps.reask_step import ReaskStep
from pipeline.steps.choose_best_step import ChooseBestStep
from pipeline.steps.explain_decision_step import ExplainDecisionStep
from pipeline.steps.grade_step import GradeStep

from pipeline.utils.persist import persist_run


def build_steps():
    return [
        PromptStep(),
        RepairJsonStep(),
        ScoreStep(),
        DecideStep(),
        ReaskStep(),
        RepairJsonStep(),  # re-validate after possible reask
        ScoreStep(),
        DecideStep(),
        GradeStep(),
        ChooseBestStep(),
        ExplainDecisionStep(),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LLM decision pipeline.")
    parser.add_argument("--question", required=True, help="User question to answer.")
    parser.add_argument("--out", default="runs/pipeline_runs.jsonl", help="JSONL output file path.")
    parser.add_argument("--break-json", action="store_true", help="Force malformed output for testing.")
    args = parser.parse_args()

    steps = build_steps()
    initial_data = {"question": args.question, "break_json": args.break_json}
    result = run_pipeline(steps, initial_data)

    # Print a nice human summary
    validated = result.get("validated") or {}
    answer = validated.get("answer")
    conf = (result.get("score") or {}).get("confidence")
    action = result.get("action")

    print("\n=== RESULT ===")
    print(f"Action: {action}")
    if conf is not None:
        print(f"Confidence: {conf:.2f}")
    if answer:
        print("\nAnswer:\n")
        print(answer)

    # Persist
    persist_run(result, Path(args.out))
    print(f"\nRun persisted to {args.out}")

    print("\n=== JSON ===")
    print(json.dumps({
    "question": result.get("question"),
    "validated": result.get("validated"),
    "score": result.get("score"),
    "grade": result.get("grade"),
    "action": result.get("action"),
    "repaired": result.get("repaired"),
    "reasked": result.get("reasked"),
    "best": result.get("best"),
    "decision_reason": result.get("decision_reason"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
