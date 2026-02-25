from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Tuple

from pipeline.utils.persist import RunRecord


def _step_ref(step: str | None, occurrence: Any) -> str:
    if step and occurrence is not None:
        return f"{step}#{occurrence}"
    return str(step or "unknown")


def derive_run_metrics(record: RunRecord) -> Dict[str, Any]:
    """
    Deterministic metrics derived from a single RunRecord artifact.
    Pure function: no I/O, no mutation.
    """
    attempted_n = len(record.attempted)
    ran_n = len(record.ran)
    skipped_n = len(record.skipped)
    failed_n = len(record.failed)
    errored_n = len(record.errored)

    run_rate = (ran_n / attempted_n) if attempted_n > 0 else 0.0

    # Skip reasons from decision events where run == False
    skip_reasons = Counter()
    skipped_steps = Counter()
    for ev in record.decision_events:
        if ev.get("run") is False:
            reason = ev.get("reason") or "unknown_reason"
            skip_reasons[str(reason)] += 1
            skipped_steps[str(ev.get("step") or "unknown_step")] += 1

    # Failure counts by step from failure_events
    failures_by_step = Counter()
    failure_modes = Counter()
    for ev in record.failure_events:
        step = str(ev.get("step") or "unknown_step")
        failures_by_step[step] += 1
        mode = ev.get("failure_mode")
        if mode is not None:
            failure_modes[str(mode)] += 1

    # “Top” helpers (stable ordering)
    def top(counter: Counter, n: int = 5) -> List[Tuple[str, int]]:
        # sort by count desc, then key asc for determinism
        return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:n]

    return {
        "run_id": record.run_id,
        "status": record.status,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "duration_ms": record.duration_ms,

        "counts": {
            "attempted": attempted_n,
            "ran": ran_n,
            "skipped": skipped_n,
            "failed": failed_n,
            "errored": errored_n,
        },
        "run_rate": run_rate,

        "skip_reasons_top": top(skip_reasons, 10),
        "skipped_steps_top": top(skipped_steps, 10),

        "failures_by_step_top": top(failures_by_step, 10),
        "failure_modes_top": top(failure_modes, 10),
        "failures_total": sum(failures_by_step.values()),

        "has_error": record.error is not None,
    }