from __future__ import annotations
from pipeline.steps.base import PipelineStep
from pipeline.utils.retry import RetryConfig
from pipeline.clients.llm_client import run_llm, SYSTEM_JSON_ANALYST_REASK

class ReaskStep(PipelineStep):
    name = "reask"
    reads = {"question", "action", "raw_output", "repaired", "validated", "score", "grade"}  # it checks action and reads question
    writes = {"reasked", "reask_count", "attempt1", "original_raw_output", "raw_output"}
    deletes = {"parsed", "validated", "score", "action", "grade", "repaired", "raw_output_repaired"}

    retry_config = RetryConfig(
        attempts=4,
        base_delay_s=0.5,
        max_delay_s=6.0,
        backoff=2.0,
        jitter_s=0.3,
        retry_on=(Exception,),
    )

    def when(self, data: dict) -> bool:
        # Only run if policy says reask AND we're not past max
        if data.get("action") != "reask":
            return False
        return data.get("reask_count", 0) < 1

    def run(self, input_data: dict) -> dict:
        # Only re-ask if policy says so
        reask_count = input_data.get("reask_count", 0) 
        question = input_data["question"]

        raw2 = run_llm(
            system_prompt=SYSTEM_JSON_ANALYST_REASK,
            user_prompt=question,
            temperature=0.2,
        )

        attempt1 = {
            "raw_output": input_data.get("raw_output"),
            "raw_output_repaired": input_data.get("raw_output_repaired"),
            "repaired": input_data.get("repaired", False),
            "validated": input_data.get("validated"),
            "score": input_data.get("score"),
            "grade": input_data.get("grade"),
            "action": input_data.get("action"),
        }

        updates = {
            "reasked": True,
            "attempt1": attempt1,
            "reask_count": reask_count + 1,
            "original_raw_output": input_data.get("raw_output"),
            "raw_output": raw2,
            "__delete__": [
                "parsed",
                "validated",
                "score",
                "action",
                "grade",
                "repaired",
                "raw_output_repaired",
            ],
        }

        return updates