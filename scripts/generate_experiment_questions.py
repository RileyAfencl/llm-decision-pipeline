from __future__ import annotations

import json
from pathlib import Path

from pipeline.clients.llm_client import run_llm, parse_json_strict


SYSTEM_PROMPT = "You generate clean experiment fixtures. Return valid JSON only."

USER_PROMPT = """
Generate exactly 50 challenging analytical questions for testing an LLM pipeline's stability under different temperature settings.

The questions should create room for variation in reasoning, prioritization, tradeoffs, and interpretation.

Requirements:
- Do NOT ask simple textbook-definition questions.
- Do NOT ask questions with one obvious canonical answer.
- Do NOT require current events, internet access, private data, medical advice, legal advice, or financial advice.
- Prefer ambiguous but answerable scenarios.
- Include tradeoff analysis, prioritization, debugging, system design, policy design, risk analysis, and decision-making.
- Questions should be concise but specific enough to answer.
- Each question should be 1-3 sentences.
- Return ONLY valid JSON.
- Each question should be a single concise scenario followed by one decision or analytical prompt.
- Prefer one sentence; at most two short sentences.
- Avoid multi-part questions with several separate sub-questions.

Target question types:
- "Given this scenario, what would you prioritize and why?"
- "Compare two plausible approaches and recommend one."
- "Identify risks and mitigations."
- "Diagnose likely causes from incomplete evidence."
- "Design a lightweight system or process under constraints."
- "Explain what could go wrong and how to monitor it."

Schema:
{
  "questions": [
    {
      "question_id": "q001",
      "question": "..."
    }
  ]
}
"""
def main() -> None:
    out_path = Path("experiments/temp_stability/questions.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    raw = run_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        temperature=0.2,
    )

    data = parse_json_strict(raw)
    questions = data["questions"]

    if len(questions) != 50:
        raise ValueError(f"Expected 50 questions, got {len(questions)}")

    with out_path.open("w", encoding="utf-8") as f:
        for i, item in enumerate(questions, start=1):
            row = {
                "question_id": f"q{i:03d}",
                "question": item["question"],
            }
            f.write(json.dumps(row) + "\n")

    print(f"Wrote {len(questions)} questions to {out_path}")


if __name__ == "__main__":
    main()