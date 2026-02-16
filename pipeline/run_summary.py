# pipeline/run_summary.py
from dataclasses import asdict, dataclass
from typing import List, Dict, Any, Optional

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
class FailureEvent:
    type: str
    step: str
    message: str
    failure_mode: str
    failure_reason: str | None
    step_index: int
    occurrence: int

@dataclass(frozen=True)
class ErrorEvent:
    type: str
    step: str
    message: str
    failure_mode: str | None
    failure_reason: str | None
    step_index: int | None
    occurrence: int | None
    missing_keys: list[str] | None

@dataclass(frozen=True)
class RunSummary:
    status: str
    attempted_steps: List[str]
    ran_steps: List[str]
    skipped_steps: List[str]
    failures: list[FailureEvent]
    error: ErrorEvent | None
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
    error: Optional[dict] = None,
    total_time_s: float,
    decision_events_raw: list[dict],
) -> dict:
    
    error_obj: ErrorEvent | None = None
    if error is not None:
        if not isinstance(error, dict):
            raise TypeError("run_summary error must be a dict when present")

        error_obj = ErrorEvent(
        type=error["type"],
        step=error["step"],
        message=error["message"],
        failure_mode=error["failure_mode"],
        failure_reason=error.get("failure_reason"),
        step_index=error["step_index"],
        occurrence=error["occurrence"],
        missing_keys=error.get("missing_keys", []),
    )

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

    failure_objs = [
        FailureEvent(
            type=ev["type"],
            step=ev["step"],
            message=ev["message"],
            failure_mode=ev["failure_mode"],
            failure_reason=ev.get("failure_reason"),
            step_index=ev["step_index"],
            occurrence=ev["occurrence"],
        )
        for ev in failures
    ]

    summary = RunSummary(
        status=status,
        attempted_steps=attempted,
        ran_steps=ran,
        skipped_steps=skipped,
        failures=failure_objs,
        error=error_obj,
        failure_flags=flags,
        total_time_s=total_time_s,
        decision_events=decision_objs,
        decision_narrative=decision_narrative,
    )

    return asdict(summary)