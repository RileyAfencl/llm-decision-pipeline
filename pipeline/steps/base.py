from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

from pipeline.utils.retry import RetryConfig

class PipelineStep(ABC):
    name: str
    retry_config: Optional[RetryConfig] = None  # default no retries

    @abstractmethod
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes the full pipeline state and returns a dict of updates.
        Must NOT mutate input in-place.
        """
        raise NotImplementedError
