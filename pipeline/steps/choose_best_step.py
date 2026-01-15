from __future__ import annotations
from pipeline.steps.base import PipelineStep


class ChooseBestStep(PipelineStep):
    name = "choose_best"

    def run(self, input_data: dict) -> dict:
        # If no reask happened, attempt1 is the only attempt
        if not input_data.get("reasked", False):
            return {
                **input_data,
                "best": {
                    "chosen": "attempt1",
                    "validated": input_data.get("validated"),
                    "score": input_data.get("score"),
                    "action": input_data.get("action"),
                },
            }

        # Pull attempt1 snapshot
        attempt1 = input_data.get("attempt1", {})

        # Grades (primary comparison)
        grade1 = (attempt1.get("grade") or {}).get("grade", -1.0)
        grade2 = (input_data.get("grade") or {}).get("grade", -1.0)

        # Confidence (tie-breaker)
        conf1 = (attempt1.get("score") or {}).get("confidence", -1.0)
        conf2 = (input_data.get("score") or {}).get("confidence", -1.0)

        # Decide winner
        if grade2 > grade1:
            chosen = "attempt2"
        elif grade2 < grade1:
            chosen = "attempt1"
        else:
            # Tie on grade → break by confidence
            chosen = "attempt2" if conf2 >= conf1 else "attempt1"

        # Select best fields
        if chosen == "attempt2":
            best_validated = input_data.get("validated")
            best_score = input_data.get("score")
            best_action = input_data.get("action")
        else:
            best_validated = attempt1.get("validated")
            best_score = attempt1.get("score")
            best_action = attempt1.get("action")

        return {
            **input_data,
            "best": {
                "chosen": chosen,
                "validated": best_validated,
                "score": best_score,
                "action": best_action,
            },
            # Overwrite top-level state with best result
            "validated": best_validated,
            "score": best_score,
            "action": best_action,
        }
