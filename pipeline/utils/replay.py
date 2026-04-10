from __future__ import annotations

from typing import Any, Dict

from pipeline.utils.persist import RunRecord


def reconstruct_initial_data(record: RunRecord) -> Dict[str, Any]:
    """
    Convert a persisted RunRecord into the minimal initial_data needed to replay
    the prompt pipeline.

    Contract:
      - question: str (required)
      - break_json: bool (optional; default False)

    NOTE: Requires record.inputs to be persisted in the run artifact.
    """
    if record.inputs is None:
        raise ValueError(
            "Run artifact has no 'inputs'. Replay requires persisted inputs "
            "(at least 'question'). Generate a new run with inputs persisted."
        )

    question = record.inputs.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Replay inputs missing required non-empty 'question'.")

    break_json = record.inputs.get("break_json", False)
    if not isinstance(break_json, bool):
        raise ValueError("Replay input 'break_json' must be a bool when present.")

    return {"question": question.strip(), "break_json": break_json}