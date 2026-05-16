from __future__ import annotations
from pipeline.steps.base import PipelineStep
from pipeline.utils.retry import RetryConfig
from pipeline.clients.llm_client import (
    run_llm,
    SYSTEM_JSON_GRADER,
    parse_json_strict,
    validate_grade_schema,
)
from pipeline.config import get_temperature_profile

class GradeStep(PipelineStep):
    name = "grade"
    reads = {"question", "validated"}
    writes = {"grade"}

    retry_config = RetryConfig(
        attempts=4,
        base_delay_s=0.5,
        max_delay_s=6.0,
        backoff=2.0,
        jitter_s=0.3,
        retry_on=(Exception,),
    )

    def run(self, input_data: dict) -> dict:
        question = input_data["question"]
        answer = input_data["validated"]["answer"]

        profile = get_temperature_profile(input_data.get("temperature_profile"))

        raw = run_llm(
            system_prompt=SYSTEM_JSON_GRADER,
            user_prompt=f"Question:\n{question}\n\nAnswer:\n{answer}",
            temperature=profile.grade,
        )

        parsed = parse_json_strict(raw)
        graded = validate_grade_schema(parsed)

        return {"grade": graded}
