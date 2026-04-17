from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayConfig:
    """
    Configuration for replay comparison behavior.
    """

    confidence_tolerance: float = 0.05

    require_validated: bool = True