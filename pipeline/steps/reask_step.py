from __future__ import annotations
from pipeline.steps.base import PipelineStep
from pipeline.utils.retry import RetryConfig
from pipeline.clients.llm_client import run_llm, SYSTEM_JSON_ANALYST_REASK

class ReaskStep(PipelineStep):
    name = "reask"

    retry_config = RetryConfig(
        attempts=4,
        base_delay_s=0.5,
        max_delay_s=6.0,
        backoff=2.0,
        jitter_s=0.3,
        retry_on=(Exception,),
    )

    def run(self, input_data: dict) -> dict:
        # Only re-ask if policy says so
        max_reasks = 1
        reask_count = input_data.get("reask_count", 0)

        # Hard stop: too many reasks
        if reask_count >= max_reasks:
            return {
            **input_data,
            "reasked": False,
            "reask_blocked": True,
        }
        
        if input_data.get("action") != "reask":
            return {
            **input_data,
            "reasked": False,
            "reask_count": reask_count,
            }
        
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

        out = {
        **input_data,
        "reasked": True,
        "attempt1": attempt1,
        "reask_count": reask_count + 1,
        "original_raw_output": input_data.get("raw_output"),
        "raw_output": raw2,
        }

        # clear anything derived from the old raw_output
        for k in ("parsed", "validated", "score", "action", "grade", "repaired", "raw_output_repaired"):
            out.pop(k, None)

        return out