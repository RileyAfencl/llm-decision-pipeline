from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Set, ClassVar

from pipeline.utils.retry import RetryConfig

class PipelineStep(ABC):
    name: str
    retry_config: Optional[RetryConfig] = None  # default no retries

    reads: ClassVar[Set[str]] = set()
    writes: ClassVar[Set[str]] = set()
    deletes: ClassVar[Set[str]] = set()

    @abstractmethod
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes the full pipeline state and returns a dict of updates.
        Must NOT mutate input in-place.
        """
        raise NotImplementedError

    def when(self, data: dict) -> bool:
        """Return True to run this step, False to skip."""
        return True
