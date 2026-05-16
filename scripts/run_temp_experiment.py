from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from pipeline.config import CONFIG, get_temperature_profile
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


EXPERIMENT_ID = "temp_stability_variable_eval_v1"

QUESTION_PATH = Path("experiments/temp_stability/questions.jsonl")
RESULTS_PATH = Path("experiments/temp_stability/results.jsonl")

TEMPERATURE_PROFILES = [
    "v1_low_temp",
    "v2_mid_temp",
    "v3_high_temp",
]

def load_questions(path: Path) -> List[Dict[str, str]]:
    questions: List[Dict[str, str]] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            row = json.loads(line)

            if "question_id" not in row or "question" not in row:
                raise ValueError(f"Invalid question row: {row}")

            questions.append(
                {
                    "question_id": str(row["question_id"]),
                    "question": str(row["question"]),
                }
            )

    if not questions:
        raise ValueError(f"No questions found in {path}")

    return questions


def build_steps() -> list:
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


def build_policy() -> CompositePolicy:
    return CompositePolicy(
        policies=[
            DefaultPolicy(),
            SecondPassAfterReaskPolicy(max_reasks=1),
        ]
    )


def run_one_pipeline(question: str, profile_name: str) -> Dict[str, Any]:
    initial_data = {
        "question": question,
        "break_json": False,
        "temperature_profile": profile_name,
    }

    return run_pipeline(
        build_steps(),
        initial_data,
        policy=build_policy(),
    )


def build_experiment_row(
    *,
    question_id: str,
    question: str,
    profile_name: str,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    profile = get_temperature_profile(profile_name)
    metrics = result["run_summary"]

    attempted_steps = metrics.get("attempted_steps") or []
    ran_steps = metrics.get("ran_steps") or []
    skipped_steps = metrics.get("skipped_steps") or []
    failures = metrics.get("failures") or []
    error = metrics.get("error")

    run_rate = len(ran_steps) / len(attempted_steps) if attempted_steps else 0.0
    validated_present = result.get("validated") is not None

    grade_obj = result.get("grade") or {}
    validated_obj = result.get("validated") or {}
    score_obj = result.get("score") or {}

    return {
        "experiment_id": EXPERIMENT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),

        "pipeline_version": CONFIG.pipeline_version,
        "model": CONFIG.default_model,

        "temperature_profile": profile.name,
        "temperature_prompt": profile.prompt,
        "temperature_repair_json": profile.repair_json,
        "temperature_grade": profile.grade,
        "temperature_reask": profile.reask,

        "question_id": question_id,
        "question": question,

        "run_id": metrics.get("run_id"),
        "status": metrics.get("status"),
        "started_at": metrics.get("started_at"),
        "finished_at": metrics.get("finished_at"),
        "duration_ms": metrics.get("duration_ms"),
        "total_time_s": metrics.get("total_time_s"),

        "attempted": len(attempted_steps),
        "ran": len(ran_steps),
        "skipped": len(skipped_steps),

        "failures_total": len(failures),
        "has_error": error is not None,
        "run_rate": run_rate,

        "reasked": bool(result.get("reasked", False)),
        "reask_count": int(result.get("reask_count", 0) or 0),
        "repaired": bool(result.get("repaired", False)),
        "validated_present": validated_present,

        "score_confidence": score_obj.get("confidence"),
        "score_tier": score_obj.get("tier"),
        "action": result.get("action"),

        "grade": grade_obj.get("grade"),
        "grade_rationale": grade_obj.get("rationale"),

        "answer_confidence": validated_obj.get("confidence"),
    }


def append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    questions = load_questions(QUESTION_PATH)

    print(f"Loaded {len(questions)} questions")
    print(f"Writing results to {RESULTS_PATH}")

    for profile_name in TEMPERATURE_PROFILES:
        print(f"\nRunning profile: {profile_name}")

        for q in questions:
            question_id = q["question_id"]
            question = q["question"]

            print(f"  running {profile_name} / {question_id}")

            result = run_one_pipeline(
                question=question,
                profile_name=profile_name,
            )

            row = build_experiment_row(
                question_id=question_id,
                question=question,
                profile_name=profile_name,
                result=result,
            )

            append_jsonl(RESULTS_PATH, row)

    print("\nExperiment complete.")


if __name__ == "__main__":
    main()