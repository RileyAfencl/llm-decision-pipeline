from __future__ import annotations
import time
from typing import Iterable, Set
import uuid
from pipeline.steps.base import PipelineStep
from pipeline.utils.logger import get_logger
from pipeline.utils.retry import retry_call
from pipeline.version import PIPELINE_VERSION
from pipeline.config import CONFIG
from pipeline.utils.invariants import require_keys, InvariantViolation

logger = get_logger("pipeline.orchestrator")

REQUIRES_BEFORE: dict[str, tuple[str, ...]] = {
    "prompt": ("question",),
    "repair_json": ("raw_output",),      # RepairJsonStep expects raw_output exists
    "score": ("validated",),
    "grade": ("validated",),
    "decide": ("score",),
    "reask": ("action", "question"),     # reask needs decision + original question
    "choose_best": (),                   # should handle both cases with .get
    "explain_decision": ("best",),       # if your step depends on best
}

def preflight_validate(steps: Iterable[PipelineStep], initial_data: dict) -> None:
    available: Set[str] = set(initial_data.keys())

    # Orchestrator injects these before the first step runs
    available.update({"run_id", "pipeline_version", "env", "model"})

    for step in steps:
        missing = set(step.reads) - available
        if missing:
            raise InvariantViolation(
                step=step.name,
                missing_keys=tuple(sorted(missing)),
                message="Preflight failed: step requires keys not available yet.",
            )

        # apply declared deletes/writes to the available-key set
        available -= set(step.deletes)
        available |= set(step.writes)

def run_pipeline(steps: Iterable[PipelineStep], initial_data: dict) -> dict:
    run_id = str(uuid.uuid4())
    data = {
        **initial_data,
        "run_id": run_id,
        "pipeline_version": CONFIG.pipeline_version,
        "env": CONFIG.env,
        "model": CONFIG.default_model,
        }
    logger.info(f"Starting pipeline run_id={run_id} version={PIPELINE_VERSION} env={CONFIG.env}")
    preflight_validate(steps, data)
    
    for step in steps:
        try:
            required = REQUIRES_BEFORE.get(step.name, ())
            if required:
             require_keys(
                step.name,
                data,
                required,
                message="Pipeline state invalid before running this step.",
                )

            # Skip step if predicate says so (Day 18)
            if not step.when(data):
                logger.info(f"Skipping step: {step.name}")
                # still record something in timings so debugging is easy
                timings = dict(data.get("timings", {}))
                timings[step.name] = 0.0
                data = {**data, "timings": timings}
                continue

            logger.info(f"Running step: {step.name}")
            start = time.perf_counter()

            def _run_step(step=step, data=data):
                return step.run(data)
            
            if step.retry_config is None:
                updates = _run_step()
            else:
                updates = retry_call(
                 _run_step,
                cfg=step.retry_config,
                on_retry=lambda attempt, err, sleep_s, step=step: print(
                f"[retry] step={step.name} attempt={attempt} err={err} sleep={sleep_s:.2f}s"
            ),
        )

            if not isinstance(updates, dict):
                raise TypeError(
                f"{step.__class__.__name__}.run() must return dict, got {type(updates)}"
                )           

            # Heuristic: discourage returning full state snapshots
            if set(updates.keys()) >= set(data.keys()):
                logger.warning(
                    f"Step {step.name} appears to be returning full state; "
                    "steps should return updates only."
                )

            allowed_keys = set(step.writes) | {"__delete__"}
            extra_keys = set(updates.keys()) - allowed_keys
            if extra_keys:
                raise InvariantViolation(
                    step=step.name,
                    missing_keys=(),
                    message=f"Step returned undeclared keys: {sorted(extra_keys)}. "
                    f"Declare them in writes or remove them.",
                )

            delete_keys = updates.pop("__delete__", [])
            if delete_keys:
                if not isinstance(delete_keys, (list, tuple)):
                    raise TypeError(
                        f"{step.__class__.__name__} __delete__ must be list[str]"
                        )
                if not all(isinstance(k, str) for k in delete_keys):
                    raise TypeError(
                        f"{step.__class__.__name__} __delete__ entries must be str"
                        )
                
            undeclared_deletes = set(delete_keys) - set(step.deletes)
            if undeclared_deletes:
                raise InvariantViolation(
                    step=step.name,
                    missing_keys=(),
                    message=f"Step requested undeclared deletes: {sorted(undeclared_deletes)}. "
                            f"Declare them in deletes or stop deleting them.",
                )
            
            for k in delete_keys:
                    data.pop(k, None)
            
            data = {**data, **updates}
                
            elapsed = time.perf_counter() - start
            logger.info(f"Finished step={step.name} run_id={run_id} elapsed={elapsed:.3f}s")
            timings = dict(data.get("timings", {}))
            timings[step.name] = elapsed
            data = {**data, "timings": timings}

        except InvariantViolation as e:
        # structured failure payload
            data = {
            **data,
            "error": {
                "type": "invariant_violation",
                "step": e.step,
                "missing_keys": list(e.missing_keys),
                "message": str(e),
            },
            "action": "error",
        }
            logger.error(f"Invariant violation: {e}")
            return data  # stop pipeline immediately 

        except Exception as e:
        # generic structured failure payload
            data = {
                **data,
                "error": {
                "type": type(e).__name__,
                "step": step.name,
                "message": str(e),
                },
            "action": "error",
        }
            logger.exception(f"Step failed: {step.name}")
            return data
   
    return data
