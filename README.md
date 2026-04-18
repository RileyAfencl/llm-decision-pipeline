[check](../../actions/workflows/check.yml/badge.svg)
![check](../../actions/workflows/check.yml/badge.svg)
# AI Pipeline with Evaluation and Observability

This project implements a production-style LLM pipeline with built-in evaluation and observability. It can replay runs, diff outputs, and summarize system behavior to detect drift, enforce structure, and make AI outputs testable.

The system is designed to reflect real-world AI engineering patterns, including structured orchestration, failure handling, and run-level diagnostics.

## Core Capabilities

- **Schema-enforced LLM outputs**  
  Ensures all model responses conform to a predefined JSON structure.

- **Automatic repair and retry logic**  
  Idempotent repair steps handle malformed responses without unnecessary retries.

- **Scoring and grading**  
  Outputs are evaluated using confidence-based scoring and LLM-assisted grading.

- **Decision and re-ask workflow**  
  Low-quality outputs can trigger a controlled re-ask using an alternative system prompt.

- **Invariant enforcement**  
  Pipeline steps declare required inputs and fail early with structured errors if violated.

- **Run tracking and logging**  
  Each pipeline execution is assigned a unique run ID, logs step-level timing, and persists results as JSON lines.

- **CLI and API interfaces**  
   Supports execution via command line and FastAPI service.

## How It Works

1. **Run the pipeline**  
   A question is processed through a sequence of steps that generate, validate, and evaluate an LLM response.

2. **Validate and repair outputs**  
   Outputs are checked against a schema and automatically repaired if malformed.

3. **Evaluate and decide**  
   Outputs are scored and graded to assess quality and determine whether they meet predetermined standards.

4. **Analyze results**  
   Runs can be replayed, diffed, and summarized to detect inconsistencies, measure reliability, and inspect system behavior.


## Quick Start

### 1. Run the Pipeline

python -m scripts.run_prompt_pipeline --question "What is the capital of France?" 

### 2. Compare the Replay

python -m scripts.replay_run --latest --json

### 3. Check the diff with another run.

python -m scripts.run_prompt_pipeline --question "What is the capital of Spain?" 
python -m scripts.diff_runs --latest-2 --json

### 4. Check the Summary of Recent Runs

python -m scripts.summarize_runs --latest 2 --json

## Example Output

Representative outputs from replay, diff, and summary tools: 

### Summary JSON

```json
{
  "verdict": "stable",
  "health": {
    "status": "healthy"
  },
  "runs": {
    "total": 2,
    "success": 2,
    "degraded": 0,
    "error": 0
  },
  "performance": {
    "avg_duration_ms": 2510.5,
    "avg_run_rate": 1.0
  },
  "failures": {
    "total": 0
  },
  "validation": {
    "present": 2,
    "missing": 0,
    "success_rate": 1.0
  }
}
``` 

### Diff JSON

```json
{
  "verdict": "structural_match_only",
  "health": {
    "status": "content_drift"
  },
  "status": {
    "a": "success",
    "b": "success",
    "match": true
  },
  "duration": {
    "a_ms": 2117,
    "b_ms": 2904,
    "delta_ms": 787,
    "match": false
  },
}
```

### Replay JSON

```json
{
  "verdict": "full_match",
  "health": {
    "status": "healthy"
  },
  "diagnostics": {
    "structural_match": true,
    "content_match": true
  },
  "validated": {
    "answer_match": true,
    "confidence_match": true
  }
}
```

## Repository Structure

The project is organized into core pipeline logic, CLI tooling, tests, and persisted run artifacts:

```text
pipeline/
  orchestrator.py        # Core execution engine
  steps/                 # Pipeline steps (prompt, repair, score, etc.)
  policy/                # Execution and retry policies
  utils/                 # Persistence, metrics, invariants, helpers
  clients/               # LLM client abstraction

scripts/
  run_prompt_pipeline.py # Run the pipeline (CLI or interactive)
  replay_run.py          # Replay a run and compare outputs
  diff_runs.py           # Compare two runs
  summarize_runs.py      # Aggregate and summarize run metrics

tests/
  test_*.py              # Unit + contract tests (invariants, policies, API, persistence)

runs/
  *.json                 # Persisted run artifacts
  index.json             # Rolling index of recent runs

config/
  .env / settings        # Environment configuration (not committed)
```
## Status

Actively evolving with ongoing improvements in evaluation, observability, and system robustness.

The current implementation demonstrates a complete pipeline and continues to expand in depth and coverage.