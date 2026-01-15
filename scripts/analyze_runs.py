from pathlib import Path
import json

LOG_PATH = Path("runs") / "pipeline_runs.jsonl"

def load_runs(path: Path) -> list[dict]:
    runs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            runs.append(json.loads(line))
    return runs

def main() -> None:
    runs = load_runs(LOG_PATH)

    print(f"Total runs: {len(runs)}")

    reasked = sum(1 for r in runs if r.get("reasked"))
    print(f"Reasked: {reasked} ({reasked / len(runs):.1%})")

    accepted = sum(1 for r in runs if r.get("final", {}).get("action") == "accept")
    reviewed = sum(1 for r in runs if r.get("final", {}).get("action") == "review")
    reask_final = sum(1 for r in runs if r.get("final", {}).get("action") == "reask")

    print("\nFinal actions:")
    print(f"  accept: {accepted}")
    print(f"  review: {reviewed}")
    print(f"  reask:  {reask_final}")

        # --- Reask delta analysis ---
    reask_runs = [
        r for r in runs
        if r.get("reasked") and r.get("attempt1") and r.get("final")
    ]

    if not reask_runs:
        print("\nNo reask runs to analyze.")
        return

    grade_before = []
    grade_after = []

    for r in reask_runs:
        g1 = (r["attempt1"].get("grade") or {}).get("grade")
        g2 = (r["final"].get("grade") or {}).get("grade")

        if g1 is not None and g2 is not None:
            grade_before.append(g1)
            grade_after.append(g2)

    if grade_before and grade_after:
        avg_before = sum(grade_before) / len(grade_before)
        avg_after = sum(grade_after) / len(grade_after)
        delta = avg_after - avg_before

        print("\nReask quality delta:")
        print(f"  avg grade before reask: {avg_before:.3f}")
        print(f"  avg grade after reask:  {avg_after:.3f}")
        print(f"  delta:                 {delta:+.3f}")
    else:
        print("\nReask runs exist but grades were missing.")


    # --- Confidence vs Grade analysis ---
    pairs = []
    for r in runs:
        final = r.get("final", {})
        conf = (final.get("score") or {}).get("confidence")
        grade = (final.get("grade") or {}).get("grade")
        if isinstance(conf, (int, float)) and isinstance(grade, (int, float)):
            pairs.append((float(conf), float(grade), r.get("question")))

    if not pairs:
        print("\nNo runs with both confidence and grade to analyze.")
        return

    n = len(pairs)
    confs = [c for c, g, q in pairs]
    grades = [g for c, g, q in pairs]

    avg_conf = sum(confs) / n
    avg_grade = sum(grades) / n

    # Pearson correlation (simple implementation)
    cov = sum((c - avg_conf) * (g - avg_grade) for c, g, _ in pairs)
    var_c = sum((c - avg_conf) ** 2 for c in confs)
    var_g = sum((g - avg_grade) ** 2 for g in grades)
    corr = cov / ((var_c ** 0.5) * (var_g ** 0.5)) if var_c > 0 and var_g > 0 else 0.0

    print("\nConfidence vs Grade:")
    print(f"  runs with both: {n}")
    print(f"  avg confidence: {avg_conf:.3f}")
    print(f"  avg grade:      {avg_grade:.3f}")
    print(f"  corr(conf,grade): {corr:+.3f}")

    # Define mismatch buckets
    # Overconfident: high confidence but low grade
    # Underconfident: low confidence but high grade
    over = [(c, g, q) for c, g, q in pairs if c >= 0.85 and g <= 0.50]
    under = [(c, g, q) for c, g, q in pairs if c <= 0.50 and g >= 0.85]

    print("\nMismatch buckets:")
    print(f"  overconfident (conf>=0.85 & grade<=0.50): {len(over)} ({len(over)/n:.1%})")
    print(f"  underconfident (conf<=0.50 & grade>=0.85): {len(under)} ({len(under)/n:.1%})")

    # Show worst offenders: largest (confidence - grade)
    worst = sorted(pairs, key=lambda t: (t[0] - t[1]), reverse=True)[:5]
    print("\nTop 5 overconfidence cases (conf - grade):")
    for c, g, q in worst:
        print(f"  diff={c-g:+.3f} conf={c:.2f} grade={g:.2f} | {q}")

    # --- Policy tuning suggestions ---
    print("\nPolicy tuning suggestions:")

    # Examine accepted answers that had low grades (bad accepts)
    bad_accepts = [
        r for r in runs
        if r.get("final", {}).get("action") == "accept"
        and (r.get("final", {}).get("grade") or {}).get("grade", 1.0) < 0.75
    ]

    # Examine reasks that did not improve grade
    failed_reasks = [
        r for r in runs
        if r.get("reasked")
        and r.get("attempt1")
        and (r.get("final", {}).get("grade") or {}).get("grade")
        <= (r.get("attempt1", {}).get("grade") or {}).get("grade", 0.0)
    ]

    print(f"  accepts with grade < 0.75: {len(bad_accepts)}")
    print(f"  reasks with no grade improvement: {len(failed_reasks)}")

    # Simple heuristic suggestions
    if bad_accepts:
        print("  ⚠ Consider raising ACCEPT threshold or requiring minimum grade.")
    else:
        print("  ✓ ACCEPT threshold appears safe.")

    if failed_reasks:
        print("  ⚠ Reask prompt may need improvement or tighter trigger conditions.")
    else:
        print("  ✓ Reask appears to improve quality consistently.")


if __name__ == "__main__":
    main()
