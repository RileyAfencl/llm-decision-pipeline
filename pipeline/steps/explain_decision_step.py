from __future__ import annotations
from pipeline.steps.base import PipelineStep

class ExplainDecisionStep(PipelineStep):
    name = "explain_decision"

    def run(self, input_data: dict) -> dict:
        reasked = input_data.get("reasked", False)

        if not reasked:
            conf1 = (input_data.get("score") or {}).get("confidence")
            conf2 = None
            chosen = "attempt1"
        else:
            attempt1 = input_data.get("attempt1", {})
            conf1 = (attempt1.get("score") or {}).get("confidence")
            conf2 = (input_data.get("score") or {}).get("confidence")
            chosen = input_data.get("best", {}).get("chosen")

        reason = {
            "rule": "max_confidence",
            "chosen": chosen,
            "confidence_attempt1": conf1,
            "confidence_attempt2": conf2,
        }

        # Add a human-readable explanation too
        if conf1 is None or conf2 is None:
            reason["note"] = "One or more confidence values missing; used defaults."
        elif conf2 > conf1:
            reason["note"] = "Attempt 2 chosen because confidence increased."
        elif conf2 < conf1:
            reason["note"] = "Attempt 1 chosen because confidence was higher."
        else:
            reason["note"] = "Tie on confidence; kept attempt 2 by tie-break rule."

        return {"decision_reason": reason}
