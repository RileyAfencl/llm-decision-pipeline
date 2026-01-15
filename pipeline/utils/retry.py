from __future__ import annotations

import time
import random
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Type, TypeVar

T = TypeVar("T")

@dataclass(frozen=True)
class RetryConfig:
    attempts: int = 5                 # total tries (1 = no retry)
    base_delay_s: float = 0.25        # starting delay
    max_delay_s: float = 5.0          # cap backoff
    backoff: float = 2.0              # exponential multiplier
    jitter_s: float = 0.10            # random [0, jitter_s] added
    retry_on: Tuple[Type[BaseException], ...] = (Exception,)  # narrow this in real code

def retry_call(
    fn: Callable[[], T],
    *,
    cfg: RetryConfig = RetryConfig(),
    on_retry: Optional[Callable[[int, BaseException, float], None]] = None,
) -> T:
    """
    Calls fn() with retry behavior. Retries only exceptions in cfg.retry_on.
    Raises the last exception if all attempts fail.
    """
    if cfg.attempts < 1:
        raise ValueError("attempts must be >= 1")

    last_err: Optional[BaseException] = None
    delay = cfg.base_delay_s

    for attempt in range(1, cfg.attempts + 1):
        try:
            return fn()
        except cfg.retry_on as e:
            last_err = e
            if attempt == cfg.attempts:
                raise

            sleep_s = min(cfg.max_delay_s, delay) + (random.random() * cfg.jitter_s)
            if on_retry:
                on_retry(attempt, e, sleep_s)

            time.sleep(sleep_s)
            delay *= cfg.backoff

    # unreachable, but keeps type-checkers happy
    assert last_err is not None
    raise last_err

