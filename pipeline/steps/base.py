from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from pipeline.utils.retry import RetryConfig

class PipelineStep(ABC):
    name: str
    retry_config: Optional[RetryConfig] = None  # default no retries

    @abstractmethod
    def run(self, input_data: dict) -> dict:
        ...
