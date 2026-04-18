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
  The pipeline can be executed via a command-line interface or through a FastAPI service.

## Use Cases

- Building reliable LLM-backed systems
- Enforcing structured outputs from language models
- Auditable AI decision-making pipelines
- Experimentation with prompt repair and re-asking strategies

## Architecture Overview

The pipeline is implemented as a sequence of composable steps, each with clearly defined inputs and outputs. This design enables easy extension, testing, and reuse across different applications.

## Status

Actively evolving with ongoing improvements in evaluation, observability, and system robustness.

The current implementation demonstrates a complete pipeline and continues to expand in depth and coverage.