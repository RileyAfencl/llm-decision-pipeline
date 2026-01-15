from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def persist_run(result: Dict[str, Any], path: Path) -> None:
    """
    Append a single pipeline run to a JSONL file.
    """
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": result.get("question"),
        "best": result.get("best"),
        "decision_reason": result.get("decision_reason"),
        "reasked": result.get("reasked"),
        "reask_count": result.get("reask_count"),
        "reask_blocked": result.get("reask_blocked"),
        "attempt1": result.get("attempt1"),
        "final": {
            "validated": result.get("validated"),
            "score": result.get("score"),
            "grade": result.get("grade"),
            "action": result.get("action"),
        },
    }

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
