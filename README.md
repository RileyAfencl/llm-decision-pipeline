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

## Status

This project is under active development and intended as a learning-focused but production-quality reference for building robust LLM pipelines.
