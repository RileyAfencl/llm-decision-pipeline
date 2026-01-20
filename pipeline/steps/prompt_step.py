from __future__ import annotations
from pipeline.steps.base import PipelineStep
from pipeline.utils.retry import RetryConfig
from pipeline.clients.llm_client import run_llm, SYSTEM_JSON_ANALYST


class PromptStep(PipelineStep):
    name = "prompt"
    reads = {"question"}
    writes = {"raw_output"}


    # LLM calls are network-bound → retries make sense
    retry_config = RetryConfig(
        attempts=5,
        base_delay_s=0.5,
        max_delay_s=6.0,
        backoff=2.0,
        jitter_s=0.3,
        retry_on=(Exception,),  # later: narrow to timeouts / rate limits
    )

    def run(self, input_data: dict) -> dict:
        question = input_data["question"]
        break_json = bool(input_data.get("break_json", False))
                
        raw_output = run_llm(
            system_prompt=SYSTEM_JSON_ANALYST,
            user_prompt=question,
        )
        if break_json:
         raw_output = f"Here is the answer:\n\n{raw_output}\n\nHope that helps!"
         print("[debug] breaking JSON output")


        return {
            "raw_output": raw_output,
        }
