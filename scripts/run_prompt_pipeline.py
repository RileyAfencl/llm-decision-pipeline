from pipeline.orchestrator import run_pipeline
from pipeline.steps.choose_best_step import ChooseBestStep
from pipeline.steps.explain_decision_step import ExplainDecisionStep
from pipeline.steps.grade_step import GradeStep
from pipeline.steps.prompt_step import PromptStep
from pipeline.steps.reask_step import ReaskStep
from pipeline.steps.repair_json_step import RepairJsonStep
from pipeline.steps.score_step import ScoreStep
from pipeline.steps.decide_step import DecideStep
from pathlib import Path
from pipeline.utils.persist import persist_run

def main() -> None:
    question = input("What would you like to ask? ").strip()
    if not question:
        raise ValueError("Please enter a non-empty question.")

    # break_json = input("Force malformed output? (y/N): ").strip().lower() == "y"
    break_json = False

    initial_data = {"question": question, "break_json": break_json}
    steps = [
    PromptStep(),
    RepairJsonStep(),
    ScoreStep(),
    GradeStep(),
    DecideStep(),

    ReaskStep(),          # may overwrite raw_output and clear derived fields

    RepairJsonStep(),     # recompute from overwritten raw_output
    ScoreStep(),
    GradeStep(),
    DecideStep(),
    ChooseBestStep(),
    ExplainDecisionStep(),
    GradeStep(),
]
    result = run_pipeline(steps, initial_data)

    print("\nVALIDATED OUTPUT:\n")
    print(result["validated"])
    print("\nRepaired?:", result["repaired"])
    print("\nACTION:", result["action"])
    print("TIER:", result["score"]["tier"], "CONF:", result["score"]["confidence"])
    print("\nACTION:", result["action"], "| SCORE:", result["score"])
    print("REASKED?:", result.get("reasked", False))
    print("\nBEST CHOSEN:", result["best"]["chosen"])
    print("BEST ACTION:", result["action"])
    print("BEST SCORE:", result["score"])
    print("\nDECISION REASON:", result["decision_reason"])
    print("\nGRADE:", result["grade"])
    print("REASK COUNT:", result.get("reask_count", 0))

    if result["repaired"]:
        print("\nRAW OUTPUT (repaired):\n")
        print(result["raw_output_repaired"])
    if result.get("reasked"):
        print("ORIGINAL RAW (trunc):", (result.get("original_raw_output") or "")[:200])
    if result.get("reask_blocked"):
        print("REASK BLOCKED: max attempts reached")
        
    log_path = Path("runs") / "pipeline_runs.jsonl"
    persist_run(result, log_path)

    print(f"\nRun persisted to {log_path}")

if __name__ == "__main__":
    main()
