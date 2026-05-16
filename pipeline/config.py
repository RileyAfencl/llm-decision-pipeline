# pipeline/config.py
from __future__ import annotations
from dataclasses import dataclass
from pipeline.version import PIPELINE_VERSION

@dataclass(frozen=True)
class TemperatureProfile:
    name: str
    prompt: float
    repair_json: float
    grade: float
    reask: float


TEMPERATURE_PROFILES = {
    "v0_current" : TemperatureProfile(
        name="v0_current",
        prompt=0.2,
        repair_json=0.0,
        grade=0.0,
        reask=0.2,
        ),
    "v1_low_temp": TemperatureProfile(
        name="v1_low_temp",
        prompt=0.0,
        repair_json=0.0,
        grade=0.0,
        reask=0.0,
    ),
    "v2_mid_temp": TemperatureProfile(
        name="v2_mid_temp",
        prompt=0.7,
        repair_json=0.3,
        grade=0.0,
        reask=0.7,
    ),
    "v3_high_temp": TemperatureProfile(
        name="v3_high_temp",
        prompt=1.3,
        repair_json=0.6,
        grade=0.0,
        reask=1.3,
    ),
}

@dataclass(frozen=True)
class AppConfig:
    env: str = "dev"                  # dev | prod
    default_model: str = "gpt-4o-mini"
    pipeline_version: str = PIPELINE_VERSION
    default_temperature_profile: str = "v0_current"

CONFIG = AppConfig()


def get_temperature_profile(name: str | None = None) -> TemperatureProfile:
    profile_name = name or CONFIG.default_temperature_profile

    try:
        return TEMPERATURE_PROFILES[profile_name]
    except KeyError as exc:
        raise ValueError(f"Unknown temperature profile: {profile_name}") from exc
