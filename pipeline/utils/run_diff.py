from __future__ import annotations
from typing import Any, Dict
from pipeline.utils.persist import RunRecord


def _count_fields(record: RunRecord) -> Dict[str, int]:
    return {
        "attempted": len(record.attempted),
        "ran": len(record.ran),
        "skipped": len(record.skipped),
        "failed": len(record.failed),
        "errored": len(record.errored),
        "decision_events": len(record.decision_events),
        "failure_events": len(record.failure_events),
    }


def diff_runs(a: RunRecord, b: RunRecord) -> Dict[str, Any]:
    """
    Pure structural diff between two persisted run artifacts.

    'a' is the baseline.
    'b' is the comparison run.
    """
    a_counts = _count_fields(a)
    b_counts = _count_fields(b)

    a_validated = a.validated if isinstance(a.validated, dict) else {}
    b_validated = b.validated if isinstance(b.validated, dict) else {}

    a_answer = a_validated.get("answer")
    b_answer = b_validated.get("answer")

    a_confidence = a_validated.get("confidence")
    b_confidence = b_validated.get("confidence")

    return {
        "run_a_id": a.run_id,
        "run_b_id": b.run_id,

        "status": {
            "a": a.status,
            "b": b.status,
            "match": a.status == b.status,
        },

        "duration_ms": {
            "a": a.duration_ms,
            "b": b.duration_ms,
            "delta": b.duration_ms - a.duration_ms,
            "match": a.duration_ms == b.duration_ms,
        },

        "counts": {
            key: {
                "a": a_counts[key],
                "b": b_counts[key],
                "delta": b_counts[key] - a_counts[key],
                "match": a_counts[key] == b_counts[key],
            }
            for key in a_counts.keys()
        },

        "validated": {
            "answer": {
                "a": a_answer,
                "b": b_answer,
                "match": a_answer == b_answer,
            },
            "confidence": {
                "a": a_confidence,
                "b": b_confidence,
                "match": a_confidence == b_confidence,
            },
        },

        "summary_version": {
            "a": a.summary_version,
            "b": b.summary_version,
            "match": a.summary_version == b.summary_version,
        },

        "inputs_present": {
            "a": a.inputs is not None,
            "b": b.inputs is not None,
            "match": (a.inputs is not None) == (b.inputs is not None),
        },

        "validated_present": {
            "a": a.validated is not None,
            "b": b.validated is not None,
            "match": (a.validated is not None) == (b.validated is not None),
        },
        
        "created_at": {
            "a": a.created_at,
            "b": b.created_at,
            "match": a.created_at == b.created_at,
        }
    }