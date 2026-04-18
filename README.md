![check](../../actions/workflows/check.yml/badge.svg)
# LLM Decision Pipeline

This project is an LLM decision pipeline designed to produce reliable, auditable, and consistent outputs from large language models.

The pipeline accepts a user prompt, sends it to an LLM with a controlled system prompt, and enforces a strict output schema. If the output is malformed or invalid, the pipeline can automatically repair it. Each response is scored, graded, and evaluated to determine whether it should be accepted, reviewed, or re-asked using a specialized system prompt designed to improve reliability.

When a re-ask occurs, the pipeline compares the original and re-asked outputs, selects the best result based on confidence and grading signals, and provides a clear rationale for the decision.

## Specific Features

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
  The pipeline can be executed via a command-line interface or through a FastAPI service.

## Use Cases

- Building reliable LLM-backed systems
- Enforcing structured outputs from language models
- Auditable AI decision-making pipelines
- Experimentation with prompt repair and re-asking strategies

## Architecture Overview

The pipeline is implemented as a sequence of composable steps, each with clearly defined inputs and outputs. This design enables easy extension, testing, and reuse across different applications.

<<<<<<< Updated upstream
=======
4. **Analyze results**  
   Runs can be replayed, diffed, and summarized to detect inconsistencies, measure reliability, and inspect system behavior.


## Quick Start

### 1. Run the Pipeline
```bash
python -m scripts.run_prompt_pipeline --question "What is the capital of France?" 
```
### 2. Compare the Replay
```bash
python -m scripts.replay_run --latest --json
```
### 3. Check the diff with another run.
```bash
python -m scripts.run_prompt_pipeline --question "What is the capital of Spain?" 

python -m scripts.diff_runs --latest-2 --json
```
### 4. Check the Summary of Recent Runs
```bash
python -m scripts.summarize_runs --latest 2 --json
```
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
>>>>>>> Stashed changes
## Status

This project is under active development and intended as a learning-focused but production-quality reference for building robust LLM pipelines.
