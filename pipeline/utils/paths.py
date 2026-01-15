from __future__ import annotations
from pathlib import Path

def project_root() -> Path:
    """
    Returns the repo root directory (the folder that contains '.env').
    Assumes this file is at: <root>/pipeline/utils/paths.py
    """
    return Path(__file__).resolve().parents[2]
