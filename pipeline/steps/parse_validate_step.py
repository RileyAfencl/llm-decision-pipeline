from __future__ import annotations
from typing import Dict, Any

from pipeline.steps.base import PipelineStep
from pipeline.clients.llm_client import parse_json_strict, validate_answer_schema


class ParseValidateStep(PipelineStep):
    name = "parse_validate"
    retry_config = None  # parsing/validation errors are not transient

    def run(self, input_data: dict) -> dict:
        raw = input_data["raw_output"]  # produced by PromptStep

        parsed: Dict[str, Any] = parse_json_strict(raw)
        validated: Dict[str, Any] = validate_answer_schema(parsed)

        return {
            **input_data,
            "parsed": parsed,
            "validated": validated,
        }
