from __future__ import annotations
from pipeline.steps.base import PipelineStep

class ScoreStep(PipelineStep):
    name = "score"
    reads = {"validated"}
    writes = {"score"}

    def run(self, input_data: dict) -> dict:
        validated = input_data["validated"]
        conf = float(validated["confidence"])

        if conf >= 0.85:
            tier = "high"
        elif conf >= 0.60:
            tier = "medium"
        else:
            tier = "low"

        return {
            "score": {
                "confidence": conf,
                "tier": tier,
            }
        }
