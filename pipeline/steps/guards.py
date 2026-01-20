from __future__ import annotations

from typing import Callable
from pipeline.steps.base import PipelineStep


class Guard(PipelineStep):
    """
    Wrap a step with a predicate so you can conditionally run only specific instances
    (e.g., the second Repair/Score/Grade/Decide block).
    """

    def __init__(self, step: PipelineStep, predicate: Callable[[dict], bool]):
        self._step = step
        self._predicate = predicate

        # Mirror identity/contract to keep orchestrator + preflight happy
        self.name = step.name
        self.retry_config = step.retry_config

        self.reads = step.reads
        self.writes = step.writes
        self.deletes = step.deletes

    def when(self, data: dict) -> bool:
        result = self._predicate(data)
        if not isinstance(result, bool):
            raise TypeError(
                f"Guard predicate for step '{self.name}' must return bool, got {type(result).__name__}"
            )
        return result

    def run(self, data: dict) -> dict:
        return self._step.run(data)
