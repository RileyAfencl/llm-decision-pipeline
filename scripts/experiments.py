from pathlib import Path
import json
from collections import defaultdict

LOG_PATH = Path("runs") / "pipeline_runs.jsonl"

def load_runs(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def summarize(runs: list[dict]) -> dict:
    summary = defaultdict(int)

    for r in runs:
        action = r.get("final", {}).get("action")
        summary["total"] += 1

        if r.get("reasked"):
            summary["reasked"] += 1

        if action:
            summary[f"action_{action}"] += 1

    return summary

def print_summary(label: str, summary: dict):
    total = summary["total"]
    print(f"\n=== {label} ===")
    print(f"Total runs: {total}")
    print(f"Reasked: {summary['reasked']} ({summary['reasked']/total:.1%})")

    for action in ("accept", "review", "reask"):
        count = summary.get(f"action_{action}", 0)
        print(f"{action:>7}: {count} ({count/total:.1%})")

def summarize_strict_accept(runs: list[dict]) -> dict:
    summary = defaultdict(int)

    for r in runs:
        summary["total"] += 1

        conf = (r.get("final", {}).get("score") or {}).get("confidence", 0.0)

        if conf >= 0.90:
            action = "accept"
        elif conf >= 0.70:
            action = "review"
        else:
            action = "reask"

        summary[f"action_{action}"] += 1

        if action == "reask":
            summary["reasked"] += 1

    return summary

def summarize_loose_reask(runs: list[dict]) -> dict:
    summary = defaultdict(int)

    for r in runs:
        summary["total"] += 1

        conf = (r.get("final", {}).get("score") or {}).get("confidence", 0.0)

        if conf >= 0.85:
            action = "accept"
        elif conf >= 0.50:   # loosened reask trigger
            action = "review"
        else:
            action = "reask"

        summary[f"action_{action}"] += 1

        if action == "reask":
            summary["reasked"] += 1

    return summary

def print_reask_cases(runs: list[dict]):
    print("\nQuestions consistently triggering reask:\n")

    for r in runs:
        if r.get("reasked"):
            q = r.get("question")
            conf = (r.get("final", {}).get("score") or {}).get("confidence")
            print(f"- conf={conf:.2f} | {q}")



def main():
    runs = load_runs(LOG_PATH)

    # Baseline = current policy
    baseline = summarize(runs)
    print_summary("Baseline policy", baseline)

    # Strict Accept = only accept if confidence >= 0.90
    strict = summarize_strict_accept(runs)
    print_summary("Variant A: stricter accept (>=0.90)", strict)

    # Loose Reask = reask only if confidence < 0.50
    loose = summarize_loose_reask(runs)
    print_summary("Variant B: looser reask (>=0.50 review)", loose)

    print_reask_cases(runs)


if __name__ == "__main__":
    main()
