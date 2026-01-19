from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Any, Dict

from pipeline.orchestrator import run_pipeline
from pipeline.steps.prompt_step import PromptStep
from pipeline.steps.repair_json_step import RepairJsonStep
from pipeline.steps.score_step import ScoreStep
from pipeline.steps.decide_step import DecideStep
from pipeline.steps.reask_step import ReaskStep
from pipeline.steps.choose_best_step import ChooseBestStep
from pipeline.steps.explain_decision_step import ExplainDecisionStep
from pipeline.steps.grade_step import GradeStep


app = FastAPI(title="LLM Decision Pipeline", version="0.1.0")


def build_steps():
    return [
        PromptStep(),
        RepairJsonStep(),
        ScoreStep(),
        GradeStep(),
        DecideStep(),
        ReaskStep(),
        RepairJsonStep(),   # only matters if reask overwrote raw_output
        ScoreStep(),
        GradeStep(),
        ChooseBestStep(),
        ExplainDecisionStep(),
    ]


class RunRequest(BaseModel):
    question: str
    break_json: bool = False


class RunResponse(BaseModel):
    question: str
    action: Optional[str] = None
    validated: Optional[Dict[str, Any]] = None
    score: Optional[Dict[str, Any]] = None
    grade: Optional[Dict[str, Any]] = None
    repaired: Optional[bool] = None
    reasked: Optional[bool] = None
    best: Optional[Dict[str, Any]] = None
    decision_reason: Optional[Dict[str, Any]] = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    steps = build_steps()
    initial_data = {"question": req.question, "break_json": req.break_json}
    result = run_pipeline(steps, initial_data)

    # Return a stable, cleaned response (don’t dump every internal field by default)
    return RunResponse(
        question=result.get("question"),
        action=result.get("action"),
        validated=result.get("validated"),
        score=result.get("score"),
        grade=result.get("grade"),
        repaired=result.get("repaired"),
        reasked=result.get("reasked"),
        best=result.get("best"),
        decision_reason=result.get("decision_reason"),
    )
