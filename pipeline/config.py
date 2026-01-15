# pipeline/config.py
from __future__ import annotations
from dataclasses import dataclass
from pipeline.version import PIPELINE_VERSION

@dataclass(frozen=True)
class AppConfig:
    env: str = "dev"                  # dev | prod
    default_model: str = "gpt-4o-mini"
    pipeline_version: str = PIPELINE_VERSION

CONFIG = AppConfig()
