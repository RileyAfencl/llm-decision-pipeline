from openai import OpenAI
from dotenv import load_dotenv
from typing import Any, Dict, Optional
import json
from pipeline.utils.paths import project_root
from pipeline.config import CONFIG

_ENV_LOADED = False
_CLIENT: Optional[OpenAI] = None

def _load_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = project_root() / ".env"
    load_dotenv(dotenv_path=env_path)
    _ENV_LOADED = True

def get_client() -> OpenAI:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    _load_env()
    _CLIENT = OpenAI()
    return _CLIENT


def run_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = CONFIG.default_model,
    temperature: float = 0.2
) -> str:
    """
    Generic LLM runner.
    """
    client=get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature
    )

    return response.choices[0].message.content

SYSTEM_JSON_ANALYST = """
You are a precise analytical assistant.

You MUST respond in valid JSON only.
No markdown.
No commentary.
No extra text.

The response must follow this schema exactly:

{
  "answer": string,
  "confidence": number
}
"""
SYSTEM_JSON_REPAIR = """
You are a strict JSON repair tool.

You will be given a model output that was supposed to be valid JSON matching this schema:

{
  "answer": string,
  "confidence": number
}

Your job:
- Output ONLY valid JSON (no markdown, no commentary, no extra text).
- Ensure keys are exactly: "answer", "confidence".
- Ensure "answer" is a string.
- Ensure "confidence" is a number between 0 and 1.
- If confidence is missing or not a number, set it to 0.5.
- If answer is missing, set it to an empty string.

Return JSON only.
"""
SYSTEM_JSON_ANALYST_REASK = """
You are a precise analytical assistant.

You MUST respond in valid JSON only.
No markdown. No commentary. No extra text.

Schema:
{
  "answer": string,
  "confidence": number
}

The user’s question may be underspecified. If needed, make reasonable assumptions,
but keep the answer concise and directly address the question.

Return JSON only.
"""
SYSTEM_JSON_GRADER = """
You are a strict grader.

You will receive:
- a user question
- a proposed answer

Grade the answer on correctness + completeness + clarity for the question.

Return ONLY valid JSON (no markdown, no extra text) with this schema:

{
  "grade": number,          // between 0 and 1
  "rationale": string       // 1-2 short sentences
}
"""

def parse_json_strict(raw_output: str) -> Dict[str, Any]:
    """
    Parse a JSON string into a dict.
    Raises json.JSONDecodeError if invalid JSON.
    Raises ValueError if JSON is not an object (dict).
    """
    data = json.loads(raw_output)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object (dict) at the top level.")
    return data

def validate_grade_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    if "grade" not in data or "rationale" not in data:
        raise ValueError("Missing required keys: 'grade' and/or 'rationale'.")

    if not isinstance(data["grade"], (int, float)):
        raise ValueError("'grade' must be a number.")

    if not isinstance(data["rationale"], str):
        raise ValueError("'rationale' must be a string.")

    g = float(data["grade"])
    if g < 0.0 or g > 1.0:
        raise ValueError("'grade' must be between 0 and 1.")

    data["grade"] = g
    return data

def validate_answer_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce the schema:
      - answer: string
      - confidence: number in [0, 1]
    Returns a normalized dict if valid, otherwise raises ValueError.
    """
    # Required keys
    if "answer" not in data or "confidence" not in data:
        raise ValueError("Missing required keys: 'answer' and/or 'confidence'.")

    # Type checks
    if not isinstance(data["answer"], str):
        raise ValueError("'answer' must be a string.")

    if not isinstance(data["confidence"], (int, float)):
        raise ValueError("'confidence' must be a number.")

    # Range check + normalization
    conf = float(data["confidence"])
    if conf < 0.0 or conf > 1.0:
        raise ValueError("'confidence' must be between 0 and 1.")

    data["confidence"] = conf
    return data


if __name__ == "__main__":
    question = "Explain supervised vs unsupervised learning."

    raw_output = run_llm(
        system_prompt=SYSTEM_JSON_ANALYST,
        user_prompt=question
    )

    print("RAW OUTPUT:")
    print(raw_output)

    data = parse_json_strict(raw_output)        # must be dict
    validated = validate_answer_schema(data)    # must match schema

    print("\nVALIDATED OUTPUT:")
    print(validated)
