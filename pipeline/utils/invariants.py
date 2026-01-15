# pipeline/utils/invariants.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class InvariantViolation(Exception):
    step: str
    missing_keys: tuple[str, ...]
    message: str

    def __str__(self) -> str:
        keys = ", ".join(self.missing_keys)
        return f"[{self.step}] missing required keys: {keys}. {self.message}"


def require_keys(step_name: str, data: dict, keys: Iterable[str], *, message: str = "") -> None:
    missing = tuple(k for k in keys if k not in data)
    if missing:
        raise InvariantViolation(step=step_name, missing_keys=missing, message=message)
