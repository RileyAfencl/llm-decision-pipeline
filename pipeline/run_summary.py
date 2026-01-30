# pipeline/run_summary.py
from dataclasses import asdict, dataclass
from typing import List, Dict, Any

from pipeline.utils.invariants import InvariantViolation


@dataclass(frozen=True)
class DecisionEvent:
    step: str
    occurrence: int
    run: bool
    policy: str
    reason: str
    step_index: int


@dataclass(frozen=True)
class RunSummary:
    status: str
    attempted_steps: List[str]
    ran_steps: List[str]
    skipped_steps: List[str]
    failures: List[Dict[str, Any]]
    failure_flags: Dict[str, Any]
    total_time_s: float
    decision_events: List[DecisionEvent]
    decision_narrative: List[str]


def serialize_run_summary(
    *,
    status: str,
    attempted: list[str],
    ran: list[str],
    skipped: list[str],
    failures: list[dict],
    flags: dict,
    total_time_s: float,
    decision_events_raw: list[dict],
) -> dict:
    
    decision_narrative = []
    for ev in decision_events_raw:
        step = ev["step"]
        occ = ev["occurrence"]
        decision_status = "ran" if ev["run"] else "skipped"
        reason = ev["reason"]
        pol = ev["policy"]
        decision_narrative.append(
        f"{step}#{occ} {decision_status} — {reason} ({pol})"
    )

    if len(decision_events_raw) != len(decision_narrative):
        raise InvariantViolation(
            step="run_summary",
            missing_keys=(),
            message=(
            "Decision narrative/event mismatch: "
            f"{len(decision_events_raw)} events vs "
            f"{len(decision_narrative)} narrative lines. "
            "Each decision must produce exactly one narrative entry."
            ),
        )

    decision_objs = [
        DecisionEvent(
            step=ev["step"],
            occurrence=ev["occurrence"],
            run=ev["run"],
            policy=ev["policy"],
            reason=ev["reason"],
            step_index=ev["step_index"],
        )
        for ev in decision_events_raw
    ]

    summary = RunSummary(
        status=status,
        attempted_steps=attempted,
        ran_steps=ran,
        skipped_steps=skipped,
        failures=failures,
        failure_flags=flags,
        total_time_s=total_time_s,
        decision_events=decision_objs,
        decision_narrative=decision_narrative,
    )

    return asdict(summary)