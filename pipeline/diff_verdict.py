from enum import Enum


class DiffVerdict(str, Enum):
    FULL_MATCH = "full_match"
    STRUCTURAL_MATCH_ONLY = "structural_match_only"
    SCHEMA_MISMATCH = "schema_mismatch"
    RUN_MISMATCH = "run_mismatch"