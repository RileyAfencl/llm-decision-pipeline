from __future__ import annotations
from typing import Any, Dict

from pipeline.steps.base import PipelineStep
from pipeline.utils.retry import RetryConfig
from pipeline.clients.llm_client import (
    run_llm,
    SYSTEM_JSON_REPAIR,
    parse_json_strict,
    validate_answer_schema,
)

class RepairJsonStep(PipelineStep):
    name = "repair_json"

    # Repair is another LLM call => transient failures possible
    retry_config = RetryConfig(
        attempts=4,
        base_delay_s=0.5,
        max_delay_s=6.0,
        backoff=2.0,
        jitter_s=0.3,
        retry_on=(Exception,),  # later: narrow
    )

    def run(self, input_data: dict) -> dict:
        raw = input_data["raw_output"]

        # If it's already valid, do nothing (idempotent step)
        try:
            parsed = parse_json_strict(raw)
            validated = validate_answer_schema(parsed)
            return {**input_data, "parsed": parsed, "validated": validated, "repaired": False}
        except Exception:
            pass  # proceed to repair

        repaired_text = run_llm(
            system_prompt=SYSTEM_JSON_REPAIR,
            user_prompt=f"Fix this into valid JSON only:\n\n{raw}",
            temperature=0.0,
        )

        repaired_parsed: Dict[str, Any] = parse_json_strict(repaired_text)
        repaired_validated: Dict[str, Any] = validate_answer_schema(repaired_parsed)

        return {
            **input_data,
            "raw_output_repaired": repaired_text,
            "parsed": repaired_parsed,
            "validated": repaired_validated,
            "repaired": True,
        }
