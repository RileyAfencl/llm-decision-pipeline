from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_INPUT_PATH = Path("experiments/temp_stability/results.jsonl")
DEFAULT_OUTPUT_PATH = Path("experiments/temp_stability/results.csv")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            row = json.loads(line)

            if not isinstance(row, dict):
                raise ValueError(f"Expected JSON object per line, got: {type(row)}")

            rows.append(row)

    if not rows:
        raise ValueError(f"No rows found in {path}")

    return rows


def collect_fieldnames(rows: List[Dict[str, Any]]) -> List[str]:
    fieldnames: List[str] = []
    seen = set()

    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    return fieldnames


def normalize_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return value


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    key: normalize_value(row.get(key))
                    for key in fieldnames
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert experiment JSONL results to CSV.")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help=f"Input JSONL path. Default: {DEFAULT_INPUT_PATH}",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Output CSV path. Default: {DEFAULT_OUTPUT_PATH}",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    rows = load_jsonl(input_path)
    fieldnames = collect_fieldnames(rows)
    write_csv(output_path, rows, fieldnames)

    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()