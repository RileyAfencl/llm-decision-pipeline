from enum import Enum


class ReplayVerdict(str, Enum):
    FULL_MATCH = "full_match"
    STRUCTURAL_MATCH_ONLY = "structural_match_only"
    REPLAY_DIVERGED = "replay_diverged"