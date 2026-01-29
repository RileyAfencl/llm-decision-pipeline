from __future__ import annotations
import time
from typing import Iterable, Sequence, Set
import uuid
from pipeline.failure_policy import DefaultFailurePolicy, FailureMode, FailurePolicy
from pipeline.steps.base import PipelineStep
from pipeline.utils.logger import get_logger
from pipeline.utils.retry import retry_call
from pipeline.version import PIPELINE_VERSION
from pipeline.config import CONFIG
from pipeline.utils.invariants import require_keys, InvariantViolation
from pipeline.policy import DefaultPolicy, Policy, StepContext, CompositePolicy


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

def build_run_summary(data: dict, steps: Iterable[PipelineStep]) -> dict:
    timings = data.get("timings", {}) or {}
    failures = data.get("failures", []) or []
    flags = data.get("failure_flags", {}) or {}
    skipped_events = data.get("skipped_steps", []) or []
    decision_events = data.get("decision_events", []) or []
    decision_narrative = []
    
    error_step = None
    if isinstance(data.get("error"), dict):
            error_step = data["error"].get("step")

    # status
    if data.get("action") == "error":
        status = "error"
    elif len(failures) > 0:
        status = "degraded"
    else:
        status = "success"

    # step lists in declared order
    step_names = [s.name for s in steps]

    failed_set = {f.get("step") for f in failures if isinstance(f, dict)}
    if error_step:
        failed_set.add(error_step)
    
    # ordered list of skipped step names for summary display
    skipped_ordered = [ev["step"] for ev in skipped_events]

    # name-only set for membership checks in existing logic
    skipped_set = {ev["step"] for ev in skipped_events}


    # attempted = either has timing entry OR is in failures (covers failure paths)
    attempted = [
    name
    for name in step_names
    if ((name in timings) or (name in failed_set)) and (name not in skipped_set)
    ]

    # successfully ran = attempted minus failed minus skipped
    ran = [name for name in attempted if name not in failed_set and name not in skipped_set]

    # skipped (ordered) from step list
    skipped_ordered = [name for name in step_names if name in skipped_set]

    total_time_s = sum(float(timings.get(name, 0.0)) for name in step_names)

    # Decision narrative
    for ev in decision_events:
        step = ev.get("step")
        occ = ev.get("occurrence")
        ran = ev.get("run")
        decision_status = "ran" if ran else "skipped"
        reason = ev.get("reason", "")
        pol = ev.get("policy", "")
        decision_narrative.append(f"{step}#{occ} {decision_status} — {reason} ({pol})")

    return {
        "status": status,
        "attempted_steps": attempted,
        "ran_steps": ran,
        "skipped_steps": skipped_ordered,
        "failures": failures,
        "failure_flags": flags,
        "total_time_s": total_time_s,
        "decision_events": decision_events,
        "decision_narrative": decision_narrative,
    }

def run_pipeline(steps: Iterable[PipelineStep], 
                 initial_data: dict, 
                 policy: Policy | list[Policy] | None = None,
                 failure_policy: FailurePolicy | None = None,
             ) -> dict:
    run_id = str(uuid.uuid4())
    if failure_policy is None:
        failure_policy_obj: FailurePolicy = DefaultFailurePolicy()
    else:
        failure_policy_obj: FailurePolicy = failure_policy 

    if policy is None:
        policy_obj: Policy = DefaultPolicy()
    elif isinstance(policy, Sequence) and not isinstance(policy, (str, bytes)):
        # list/tuple/etc of policies
        policy_obj = CompositePolicy(policies=policy)
    else:
        # single Policy
        policy_obj = policy
    name_counts: dict[str, int] = {}
    data = {
        **initial_data,
        "run_id": run_id,
        "pipeline_version": CONFIG.pipeline_version,
        "env": CONFIG.env,
        "model": CONFIG.default_model,
        }
    logger.info(f"Starting pipeline run_id={run_id} version={PIPELINE_VERSION} env={CONFIG.env}")
    preflight_validate(steps, data)
    
    for idx, step in enumerate(steps):
        try:
            required = REQUIRES_BEFORE.get(step.name, ())
            if required:
             require_keys(
                step.name,
                data,
                required,
                message="Pipeline state invalid before running this step.",
                )
        
            occurrence = name_counts.get(step.name, 0) + 1
            name_counts[step.name] = occurrence
            ctx = StepContext(step_index=idx, occurrence=occurrence)

            decision = policy_obj.decide(step, data, ctx)

            # record decision metadata (both run + skip)
            decision_events = list(data.get("decision_events", []))
            decision_events.append(
                {
                "step": step.name,
                "run": decision.run,
                "policy": decision.policy,
                "reason": decision.reason,
                "step_index": ctx.step_index,
                "occurrence": ctx.occurrence,
                }
            )
            data = {**data, "decision_events": decision_events}

            if not decision.run:
                logger.info(
                    f"Skipping step: {step.name} (occurrence={occurrence}) "
                    f"policy={decision.policy} reason={decision.reason}"
                )
                timings = dict(data.get("timings", {}))
                timings[step.name] = 0.0
                skipped = list(data.get("skipped_steps", []))
                skipped.append({"step": step.name, "occurrence": ctx.occurrence, "step_index": ctx.step_index})
                data = {**data, "timings": timings, "skipped_steps": skipped}
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
            data = {**data, "run_summary": build_run_summary(data, steps)}
            return data  # stop pipeline immediately 

        except Exception as e:
        # # ctx may not exist if we failed before it was created; make a safe fallback
            ctx_fallback = locals().get(
                "ctx",
                StepContext(
                    step_index=idx,
                    occurrence=name_counts.get(step.name, 0) + 1,
                ),
            )

            decision = failure_policy_obj.on_step_failure(step, data, ctx_fallback, e)

            if decision.mode == FailureMode.SKIP:
                # record failure as data and continue
                failure_event = {
                    "type": type(e).__name__,
                    "step": step.name,
                    "message": decision.reason or str(e),
                    "failure_mode": decision.mode.value,   # "skip"
                    "failure_reason": decision.reason,
                    "step_index": ctx_fallback.step_index,
                    "occurrence": ctx_fallback.occurrence,
                }

                failures = list(data.get("failures", []))
                failures.append(failure_event)

                timings = dict(data.get("timings", {}))
                timings[step.name] = 0.0

                data = {
                    **data,
                    "failures": failures,
                    "timings": timings,
                }

                logger.exception(f"Step failed (SKIP): {step.name}")
                continue

            if decision.mode == FailureMode.CONTINUE_WITH_FLAG:
                # record failure as data and continue, but also inject a failure flag
                failure_event = {
                    "type": type(e).__name__,
                    "step": step.name,
                    "message": decision.reason or str(e),
                    "failure_mode": decision.mode.value,   # "continue_with_flag"
                    "failure_reason": decision.reason,
                    "step_index": ctx_fallback.step_index,
                    "occurrence": ctx_fallback.occurrence,
                }

                failures = list(data.get("failures", []))
                failures.append(failure_event)

                flags = dict(data.get("failure_flags", {}))
                # If the same step can fail multiple times, last-write-wins is fine for now.
                flags[step.name] = {
                    "type": type(e).__name__,
                    "reason": decision.reason or str(e),
                    "step_index": ctx_fallback.step_index,
                    "occurrence": ctx_fallback.occurrence,
                }

                timings = dict(data.get("timings", {}))
                timings[step.name] = 0.0

                data = {
                    **data,
                    "failures": failures,
                    "failure_flags": flags,
                    "timings": timings,
                }

                logger.exception(f"Step failed (CONTINUE_WITH_FLAG): {step.name}")
                continue

            if decision.mode != FailureMode.ABORT:
                raise NotImplementedError(
                    f"Failure mode {decision.mode} not implemented yet"
                )

            # ABORT (current behavior): structured failure payload + stop
            data = {
                **data,
                "error": {
                    "type": type(e).__name__,
                    "step": step.name,
                    "message": decision.reason or str(e),
                    "failure_mode": decision.mode.value,  # "abort"
                    "failure_reason": decision.reason,
                },
                "action": "error",
            }
            logger.exception(f"Step failed: {step.name}")
            data = {**data, "run_summary": build_run_summary(data, steps)}
            return data
        
    data = {**data, "run_summary": build_run_summary(data, steps)}
    return data
