from __future__ import annotations
from pipeline.steps.base import PipelineStep

class DecideStep(PipelineStep):
    name = "decide"

    def run(self, input_data: dict) -> dict:
        tier = input_data["score"]["tier"]

        if tier == "high":
            action = "accept"
        elif tier == "medium":
            action = "review"
        else:
            action = "reask"

        return {
            "action": action,
        }
